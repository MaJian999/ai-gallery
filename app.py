import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 资产库 Ultimate", layout="wide", initial_sidebar_state="expanded")

# --- CSS 美化 ---
st.markdown("""
<style>
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
    /* 调整 tab 字体 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心函数 ---

def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.title("🔒 AI 资产库")
            password = st.text_input("访问密码", type="password", label_visibility="collapsed")
            if st.button("解锁", use_container_width=True):
                if password == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🚫 密码错误")
        st.stop()

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("请配置 Secrets！")
        st.stop()

# --- 3. 初始化 ---
check_login()
supabase = init_connection()

# --- 4. 侧边栏：录入系统 ---
with st.sidebar:
    st.header("📤 新增资产")
    
    # 0. 获取现有数据 (用于下拉框)
    try:
        # 获取已有分类
        cat_query = supabase.table("gallery").select("category").execute()
        existing_cats = sorted(list(set([i['category'] for i in cat_query.data if i.get('category')])))
        
        # 获取已有风格 (你的需求: 风格也要下拉框)
        style_query = supabase.table("gallery").select("style").execute()
        existing_styles = sorted(list(set([i['style'] for i in style_query.data if i.get('style')])))
    except:
        existing_cats = []
        existing_styles = []

    # 1. 备注名称 (必填)
    new_title = st.text_input("标题 / 备注 (必填)", placeholder="例如: 赛博朋克女孩v1")

    # 2. 分类选择 (下拉或新建)
    st.write("📂 **分类 (Category)**")
    cat_tabs = st.tabs(["选择已有", "新建"])
    with cat_tabs[0]:
        sel_cat = st.selectbox("已有分类", existing_cats if existing_cats else ["默认分类"], label_visibility="collapsed")
    with cat_tabs[1]:
        new_cat = st.text_input("输入新分类", placeholder="例如: logo设计", label_visibility="collapsed")
    final_category = new_cat if new_cat.strip() else sel_cat

    # 3. 风格选择 (下拉或新建)
    st.write("🎨 **风格 (Style)**")
    style_tabs = st.tabs(["选择已有", "新建"])
    with style_tabs[0]:
        sel_style = st.selectbox("已有风格", existing_styles if existing_styles else [""], label_visibility="collapsed")
    with style_tabs[1]:
        new_style = st.text_input("输入新风格", placeholder="例如: 3D, 极简", label_visibility="collapsed")
    final_style = new_style if new_style.strip() else sel_style
    # 如果用户在两个tab都没选/没填，且已有列表为空，style则为空
    if not final_style and not existing_styles: final_style = ""

    # 4. 内容录入
    prompt_text = st.text_area("提示词 (Prompt)", height=150)
    uploaded_file = st.file_uploader("上传图片 (可选，不传则为纯文本)", type=['jpg', 'png', 'jpeg', 'webp'])

    # 5. 提交逻辑
    if st.button("🚀 提交保存", type="primary", use_container_width=True):
        if new_title and final_category:
            with st.spinner("处理中..."):
                img_url = None
                # 如果有图片，先上传
                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()
                    file_ext = uploaded_file.name.split('.')[-1]
                    file_name = f"img_{int(time.time())}.{file_ext}"
                    supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                    img_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{file_name}"

                # 存入数据库
                data = {
                    "title": new_title,
                    "category": final_category,
                    "style": final_style,
                    "prompt": prompt_text,
                    "image_url": img_url,
                    "is_pinned": False,
                    "is_favorite": False
                }
                supabase.table("gallery").insert(data).execute()
                st.success("✅ 保存成功！")
                time.sleep(1)
                st.rerun()
        else:
            st.error("⚠️ 标题和分类不能为空")

# --- 5. 主界面：展示系统 ---

# 页面顶部标题
st.title("🌌 我的 AI 资产库")

# 定义卡片渲染函数 (复用逻辑)
def render_card(item, is_text_only=False):
    with st.container(border=True):
        # 顶部工具栏：置顶 & 收藏 & 删除
        c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
        with c1:
            st.markdown(f"**{item.get('title', '未命名')}**")
        with c2:
            # 置顶按钮
            pin_icon = "📌" if item['is_pinned'] else "📍"
            if st.button(pin_icon, key=f"pin_{item['id']}", help="点击置顶/取消"):
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
        with c3:
            # 收藏按钮
            fav_icon = "❤️" if item['is_favorite'] else "🤍"
            if st.button(fav_icon, key=f"fav_{item['id']}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()
        with c4:
            # 删除按钮
            with st.popover("🗑️"):
                st.write("确认删除？")
                if st.button("Yes", key=f"del_{item['id']}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    if item['image_url']:
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()

        # 中间内容区
        if not is_text_only and item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        else:
            # 纯文本模式显示大段提示词
            st.info(item['prompt'] if item['prompt'] else "(无提示词内容)")

        # 底部标签区
        st.caption(f"📂 {item['category']} | 🎨 {item['style']}")
        
        # 底部操作区 (编辑 & 复制)
        b1, b2 = st.columns([1, 3])
        with b1:
             with st.popover("✏️ 编辑"):
                with st.form(key=f"edit_{item['id']}"):
                    e_title = st.text_input("标题", value=item['title'])
                    e_cat = st.text_input("分类", value=item['category'])
                    e_style = st.text_input("风格", value=item['style'])
                    e_prompt = st.text_area("提示词", value=item['prompt'])
                    if st.form_submit_button("保存修改"):
                        supabase.table("gallery").update({
                            "title": e_title, "category": e_cat, 
                            "style": e_style, "prompt": e_prompt
                        }).eq("id", item['id']).execute()
                        st.rerun()
        with b2:
             with st.popover("📄 复制提示词", use_container_width=True):
                 st.code(item['prompt'], language=None)

# --- 数据读取与筛选 ---
# 逻辑：先按置顶排序，再按ID倒序
base_query = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True)

# 顶部 Tab 切换
tabs = st.tabs(["🖼️ 灵感图库", "📝 纯提示词", "⭐ 我的收藏"])

# --- Tab 1: 灵感图库 (只看有图的) ---
with tabs[0]:
    # 筛选器
    col_f, col_l = st.columns([3,1])
    with col_f:
        # 只显示属于"有图"的分类
        if existing_cats:
            sel_cats_img = st.multiselect("📂 筛选分类", existing_cats, key="filter_img")
        else: sel_cats_img = []
    with col_l:
        cols_img = st.slider("列数", 2, 6, 4, key="slider_img")

    # 查询数据
    query_img = base_query.neq("image_url", "null") # 只要有图的
    if sel_cats_img: query_img = query_img.in_("category", sel_cats_img)
    data_img = query_img.execute().data

    if not data_img: st.info("这里空空如也~")
    
    # 渲染
    c_img = st.columns(cols_img)
    for idx, item in enumerate(data_img):
        with c_img[idx % cols_img]:
            render_card(item, is_text_only=False)

# --- Tab 2: 纯提示词 (只看无图的) ---
with tabs[1]:
    col_f2, col_l2 = st.columns([3,1])
    with col_f2:
        if existing_cats:
            sel_cats_txt = st.multiselect("📂 筛选分类", existing_cats, key="filter_txt")
        else: sel_cats_txt = []
    with col_l2:
        cols_txt = st.slider("列数", 2, 4, 3, key="slider_txt")

    query_txt = base_query.is_("image_url", "null") # 只要没图的
    if sel_cats_txt: query_txt = query_txt.in_("category", sel_cats_txt)
    data_txt = query_txt.execute().data

    if not data_txt: st.info("没有纯提示词记录")

    c_txt = st.columns(cols_txt)
    for idx, item in enumerate(data_txt):
        with c_txt[idx % cols_txt]:
            render_card(item, is_text_only=True)

# --- Tab 3: 收藏夹 (只看 is_favorite=True) ---
with tabs[2]:
    st.caption("这里汇集了你标记为 ❤️ 的所有内容（包含图片和纯文本）")
    cols_fav = st.slider("列数", 2, 6, 4, key="slider_fav")
    
    query_fav = base_query.eq("is_favorite", True)
    data_fav = query_fav.execute().data
    
    if not data_fav: st.info("还没有收藏任何内容")
    
    c_fav = st.columns(cols_fav)
    for idx, item in enumerate(data_fav):
        with c_fav[idx % cols_fav]:
            # 判断是图还是文，自动适配
            is_txt = item['image_url'] is None
            render_card(item, is_text_only=is_txt)
