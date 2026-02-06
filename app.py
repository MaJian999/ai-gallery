import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 资产库 Ultimate v9", layout="wide", initial_sidebar_state="expanded")

# --- CSS 样式重构 ---
st.markdown("""
<style>
    /* 1. 登录框居中 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
    
    /* 2. 顶部小工具栏按钮 (View, Pin, Fav) - 保持正方形 */
    .toolbar-btn button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        padding: 0 !important;
        line-height: 1 !important;
        min-height: 32px !important; /*稍微小一点，精致*/
        border-radius: 6px !important;
        border: 1px solid #f0f2f6 !important;
    }

    /* 3. 底部大按钮 (提示词) - 宽大 */
    .wide-btn button {
        width: 100% !important;
        min-height: 40px !important;
        border: 1px solid #e0e0e0 !important;
        background-color: #f8f9fa !important;
        border-radius: 8px !important;
        color: #31333F !important;
        font-weight: 500 !important;
    }
    .wide-btn button:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
    }

    /* 4. 底部菜单按钮 (⋮) - 正方形 */
    .menu-btn button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-height: 40px !important;
        border-radius: 8px !important;
    }

    /* 5. 弹窗内图片限制高度 */
    /* 这是一个比较暴力的限制，防止图片太长 */
    img {
        max-height: 600px;
        object-fit: contain;
    }
    
    /* 6. 隐藏 Popover 箭头 */
    div[data-testid="stPopover"] > button > svg { display: none !important; }
    div[data-testid="stPopover"] > button > div { margin: 0 !important; padding: 0 !important; }

    /* Tag 样式 */
    .stMultiSelect span {
        background-color: #e8f0fe;
        color: #1967d2;
        border-radius: 4px;
        font-size: 0.85rem;
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

# --- 全局数据预取 ---
try:
    all_data_preview = supabase.table("gallery").select("category, style").execute().data
    all_cats = sorted(list(set([i['category'] for i in all_data_preview if i.get('category')])))
    
    raw_styles = [i['style'] for i in all_data_preview if i.get('style')]
    all_styles = set()
    for s in raw_styles:
        tags = [tag.strip() for tag in s.split(',')]
        all_styles.update(tags)
    all_styles = sorted(list(all_styles))
except:
    all_cats = []
    all_styles = []

# --- 4. 弹窗功能 ---

# A. 编辑弹窗
@st.dialog("✏️ 编辑信息")
def edit_dialog(item, all_cats, all_styles):
    new_title = st.text_input("标题", value=item['title'])
    
    c1, c2 = st.columns(2)
    with c1:
        cur_cat = item['category']
        idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        cat_sel = st.selectbox("分类", all_cats, index=idx)
        cat_new = st.text_input("或新建分类")
    with c2:
        cur_style = item.get('style', '')
        cur_list = [s.strip() for s in cur_style.split(',')] if cur_style else []
        def_style = [s for s in cur_list if s in all_styles]
        style_sel = st.multiselect("风格", all_styles, default=def_style)
        style_new = st.text_input("或新建风格")

    new_prompt = st.text_area("提示词", value=item['prompt'], height=200)
    
    if st.button("💾 保存", type="primary", use_container_width=True):
        f_cat = cat_new.strip() if cat_new.strip() else cat_sel
        f_styles = style_sel.copy()
        if style_new: f_styles.extend([t.strip() for t in style_new.replace('，', ',').split(',') if t.strip()])
        f_style_str = ", ".join(list(set(f_styles)))
        
        supabase.table("gallery").update({
            "title": new_title, "category": f_cat, "style": f_style_str, "prompt": new_prompt
        }).eq("id", item['id']).execute()
        st.rerun()

# B. 查看详情弹窗 (缩小版)
# 去掉了 width="large"，使用默认宽度，防止太宽太高
@st.dialog("🔍 作品详情")
def view_dialog(item):
    # 使用 1:1 比例，防止图片列太宽
    col_img, col_info = st.columns([1, 1])
    
    with col_img:
        if item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        else:
            st.info("无图片")
            
    with col_info:
        st.subheader(item['title'])
        st.caption(f"📂 {item['category']}")
        if item['style']:
            st.markdown(" ".join([f"`{t.strip()}`" for t in item['style'].split(',')]))
        
        st.divider()
        st.caption("提示词 (点击复制图标):")
        st.code(item['prompt'], language=None)

# --- 5. 侧边栏：录入 ---
with st.sidebar:
    st.header("📤 新增资产")
    new_title = st.text_input("标题 (必填)", placeholder="例如: 赛博朋克女孩v1")

    st.write("📂 **分类**")
    cat_mode = st.radio("分类方式", ["已有", "新建"], horizontal=True, label_visibility="collapsed")
    if cat_mode == "已有":
        final_category = st.selectbox("已有分类", all_cats if all_cats else ["默认分类"], label_visibility="collapsed")
    else:
        final_category = st.text_input("输入新分类", label_visibility="collapsed").strip() or "默认分类"

    st.write("🎨 **风格**")
    selected_styles = st.multiselect("选择风格", all_styles)
    new_style_input = st.text_input("新增风格", placeholder="逗号隔开")
    
    final_style_list = selected_styles.copy()
    if new_style_input:
        manual_tags = [t.strip() for t in new_style_input.replace('，', ',').split(',') if t.strip()]
        final_style_list.extend(manual_tags)
    final_style_str = ", ".join(list(set(final_style_list)))

    prompt_text = st.text_area("提示词", height=150)
    uploaded_file = st.file_uploader("上传图片", type=['jpg', 'png', 'jpeg', 'webp'])

    if st.button("🚀 提交", type="primary", use_container_width=True):
        if new_title:
            with st.spinner("处理中..."):
                img_url = None
                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()
                    file_ext = uploaded_file.name.split('.')[-1]
                    file_name = f"img_{int(time.time())}.{file_ext}"
                    supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                    img_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{file_name}"

                data = {
                    "title": new_title, "category": final_category, "style": final_style_str,
                    "prompt": prompt_text, "image_url": img_url,
                    "is_pinned": False, "is_favorite": False
                }
                supabase.table("gallery").insert(data).execute()
                st.success("成功！")
                time.sleep(1)
                st.rerun()
        else:
            st.error("标题必填")

# --- 6. 主界面 ---
st.title("🌌 我的 AI 资产库")

with st.container(border=True):
    f1, f2, f3 = st.columns([2, 2, 1])
    with f1: filter_cats = st.multiselect("📂 筛选分类", all_cats)
    with f2: filter_styles = st.multiselect("🎨 筛选风格", all_styles)
    with f3: layout_cols = st.slider("列数", 2, 6, 4)

# --- 核心渲染逻辑 (优化布局) ---
def render_card(item, is_text_only=False, key_suffix="main"):
    with st.container(border=True):
        
        # [层级1] 图片
        if not is_text_only and item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        elif is_text_only:
            st.info(item['prompt'][:80] + "..." if item['prompt'] else "无内容")

        # [层级2] 工具栏：View | Pin | Fav (靠左排列)
        # 布局：3个小按钮 + 空白
        t1, t2, t3, t4 = st.columns([1, 1, 1, 3])
        
        # 引入 CSS class 限制它们的大小
        with t1:
            st.markdown('<div class="toolbar-btn">', unsafe_allow_html=True)
            if st.button("👁️", key=f"v_{item['id']}_{key_suffix}", help="查看详情"):
                view_dialog(item)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with t2:
            st.markdown('<div class="toolbar-btn">', unsafe_allow_html=True)
            pin_icon = "📌" if item['is_pinned'] else "📍"
            if st.button(pin_icon, key=f"p_{item['id']}_{key_suffix}", help="置顶"):
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with t3:
            st.markdown('<div class="toolbar-btn">', unsafe_allow_html=True)
            fav_icon = "❤️" if item['is_favorite'] else "🤍"
            if st.button(fav_icon, key=f"f_{item['id']}_{key_suffix}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # [层级3] 信息区
        st.markdown(f"**{item.get('title', '未命名')}**")
        tags = f"📂 {item['category']}"
        if item.get('style'): tags += f" | {item['style']}"
        st.caption(tags if len(tags)<35 else tags[:35]+"...")

        # [层级4] 底部大按钮区
        # 布局：[ 提示词 (80%) ] [ ⋮ (20%) ]
        b1, b2 = st.columns([4, 1])
        
        with b1:
            st.markdown('<div class="wide-btn">', unsafe_allow_html=True)
            # Popover 模拟成一个宽按钮
            with st.popover("📄 查看提示词", use_container_width=True):
                st.code(item['prompt'], language=None)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with b2:
            st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
            with st.popover("⋮", use_container_width=True):
                if st.button("✏️ 编辑", key=f"e_{item['id']}_{key_suffix}"):
                    edit_dialog(item, all_cats, all_styles)
                if st.button("🗑️ 删除", key=f"d_{item['id']}_{key_suffix}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    if item['image_url']:
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 数据处理 ---
raw = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data
filtered = []
for i in raw:
    if filter_cats and i['category'] not in filter_cats: continue
    if filter_styles:
        if not set(filter_styles).intersection(set([s.strip() for s in i.get('style','').split(',')])): continue
    filtered.append(i)

# --- Tab ---
t1, t2, t3 = st.tabs(["🖼️ 灵感图库", "📝 纯提示词", "⭐ 收藏"])

with t1:
    d = [x for x in filtered if x['image_url']]
    if not d: st.info("空")
    else:
        cols = st.columns(layout_cols)
        for idx, item in enumerate(d):
            with cols[idx % layout_cols]: render_card(item, False, "img")

with t2:
    d = [x for x in filtered if not x['image_url']]
    if not d: st.info("空")
    else:
        cols = st.columns(layout_cols)
        for idx, item in enumerate(d):
            with cols[idx % layout_cols]: render_card(item, True, "txt")

with t3:
    d = [x for x in filtered if x['is_favorite']]
    if not d: st.info("空")
    else:
        cols = st.columns(layout_cols)
        for idx, item in enumerate(d):
            with cols[idx % layout_cols]: render_card(item, (item['image_url'] is None), "fav")
