import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 资产库 Ultimate v2", layout="wide", initial_sidebar_state="expanded")

# --- CSS 优化 ---
st.markdown("""
<style>
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
    
    /* 卡片微调 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 10px;
    }
    
    /* 调整多选框的tag样式 */
    .stMultiSelect span {
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 4px;
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

# --- 全局数据获取 (为了下拉框和筛选) ---
# 每次刷新页面获取一次所有标签，保证下拉框是最新的
try:
    all_data_preview = supabase.table("gallery").select("category, style").execute().data
    
    # 提取所有分类
    all_cats = sorted(list(set([i['category'] for i in all_data_preview if i.get('category')])))
    
    # 提取所有风格 (处理多选逗号分隔的情况)
    raw_styles = [i['style'] for i in all_data_preview if i.get('style')]
    all_styles = set()
    for s in raw_styles:
        # 把 "3D, 赛博朋克" 拆分成单独的标签
        tags = [tag.strip() for tag in s.split(',')]
        all_styles.update(tags)
    all_styles = sorted(list(all_styles))
except:
    all_cats = []
    all_styles = []

# --- 4. 侧边栏：录入系统 ---
with st.sidebar:
    st.header("📤 新增资产")

    # 1. 备注名称 (必填)
    new_title = st.text_input("标题 / 备注 (必填)", placeholder="例如: 赛博朋克女孩v1")

    # 2. 分类选择 (下拉 + 新建)
    st.write("📂 **分类 (Category)**")
    cat_mode = st.radio("分类方式", ["选择已有", "新建"], horizontal=True, label_visibility="collapsed")
    if cat_mode == "选择已有":
        final_category = st.selectbox("已有分类", all_cats if all_cats else ["默认分类"], label_visibility="collapsed")
    else:
        final_category = st.text_input("输入新分类", placeholder="例如: logo设计", label_visibility="collapsed").strip()
        if not final_category: final_category = "默认分类"

    # 3. 风格选择 (多选下拉 + 新建)
    st.write("🎨 **风格 (Style - 可多选)**")
    # 多选框
    selected_styles = st.multiselect("选择风格", all_styles, placeholder="选择标签...")
    # 补充输入框
    new_style_input = st.text_input("新增风格 (可选)", placeholder="输入新标签，多个用逗号隔开")
    
    # 合并逻辑
    final_style_list = selected_styles.copy()
    if new_style_input:
        # 处理用户手动输入: "油画, 4k" -> ["油画", "4k"]
        manual_tags = [t.strip() for t in new_style_input.replace('，', ',').split(',') if t.strip()]
        final_style_list.extend(manual_tags)
    
    # 转为字符串存库: ["A", "B"] -> "A, B"
    final_style_str = ", ".join(list(set(final_style_list)))

    # 4. 内容录入
    prompt_text = st.text_area("提示词 (Prompt)", height=150)
    uploaded_file = st.file_uploader("上传图片 (可选，不传则为纯文本)", type=['jpg', 'png', 'jpeg', 'webp'])

    # 5. 提交逻辑
    if st.button("🚀 提交保存", type="primary", use_container_width=True):
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
                    "title": new_title,
                    "category": final_category,
                    "style": final_style_str,
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
            st.error("⚠️ 标题不能为空")

# --- 5. 主界面：展示系统 ---

st.title("🌌 我的 AI 资产库")

# --- 卡片渲染函数 (重构版：解决排版乱的问题) ---
def render_card(item, is_text_only=False):
    # 边框容器
    with st.container(border=True):
        
        # [区域1] 图片展示 (放在最上面，最显眼)
        if not is_text_only and item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        elif is_text_only:
            st.info(item['prompt'][:100] + "..." if item['prompt'] else "(无内容)")
        
        # [区域2] 标题与关键信息 (加粗标题)
        st.markdown(f"#### {item.get('title', '未命名')}")
        
        # 解析多风格标签
        current_style_str = item.get('style', '')
        current_style_list = [s.strip() for s in current_style_str.split(',')] if current_style_str else []
        
        # 显示标签 (分类 | 风格1, 风格2...)
        tags_display = f"📂 **{item['category']}**"
        if current_style_list:
            tags_display += f"  |  🎨 {', '.join(current_style_list)}"
        st.caption(tags_display)

        # [区域3] 底部操作栏 (一行排开：置顶、收藏、编辑、删除)
        # 使用 col 布局让图标紧凑
        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns([1, 1, 1, 1, 2])
        
        with col_act1:
            # 📌 置顶
            pin_icon = "📌" if item['is_pinned'] else "📍"
            if st.button(pin_icon, key=f"pin_{item['id']}", help="置顶"):
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
        
        with col_act2:
            # ❤️ 收藏
            fav_icon = "❤️" if item['is_favorite'] else "🤍"
            if st.button(fav_icon, key=f"fav_{item['id']}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()

        with col_act3:
            # 📄 复制
            with st.popover("📄"):
                 st.code(item['prompt'], language=None)

        with col_act4:
            # 🗑️ 删除 (带确认)
            with st.popover("🗑️"):
                st.write("删掉？")
                if st.button("Yes", key=f"del_{item['id']}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    if item['image_url']:
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()

        with col_act5:
            # ✏️ 编辑 (全能修改：下拉+新建)
            with st.popover("✏️ 编辑", use_container_width=True):
                with st.form(key=f"edit_form_{item['id']}"):
                    st.write("**编辑信息**")
                    new_title = st.text_input("标题", value=item['title'])
                    
                    # 编辑分类：下拉选择
                    cat_index = all_cats.index(item['category']) if item['category'] in all_cats else 0
                    edit_cat_sel = st.selectbox("分类 (选择)", all_cats, index=cat_index)
                    edit_cat_new = st.text_input("分类 (或输入新分类)")
                    # 逻辑：如果填了新的，用新的；否则用选的
                    final_edit_cat = edit_cat_new.strip() if edit_cat_new.strip() else edit_cat_sel
                    
                    # 编辑风格：多选框
                    # 预先选中当前的风格
                    default_styles = [s for s in current_style_list if s in all_styles]
                    edit_style_sel = st.multiselect("风格 (多选)", all_styles, default=default_styles)
                    edit_style_new = st.text_input("新增风格 (可选)")
                    
                    # 编辑提示词
                    new_prompt = st.text_area("提示词", value=item['prompt'], height=100)
                    
                    if st.form_submit_button("保存修改"):
                        # 合并风格
                        final_edit_styles = edit_style_sel.copy()
                        if edit_style_new:
                            final_edit_styles.extend([t.strip() for t in edit_style_new.split(',') if t.strip()])
                        final_style_str = ", ".join(list(set(final_edit_styles)))
                        
                        supabase.table("gallery").update({
                            "title": new_title, 
                            "category": final_edit_cat, 
                            "style": final_style_str, 
                            "prompt": new_prompt
                        }).eq("id", item['id']).execute()
                        st.rerun()


# --- 数据读取与筛选逻辑 ---

# 1. 顶部 Tab
tabs = st.tabs(["🖼️ 灵感图库", "📝 纯提示词", "⭐ 我的收藏"])

# 2. 筛选区域 (全局筛选，两个Tab通用)
st.markdown("---")
f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
with f_col1:
    # 筛选分类
    filter_cats = st.multiselect("📂 筛选分类", all_cats)
with f_col2:
    # 筛选风格
    filter_styles = st.multiselect("🎨 筛选风格", all_styles)
with f_col3:
    layout_cols = st.slider("列数", 2, 6, 4)

# 3. 核心数据查询与处理
# Supabase 不支持复杂的 "Array Contains" 逻辑查询 CSV 字符串，
# 所以我们把所有数据拉下来(个人使用数据量不大)，在 Python 里做筛选。
raw_data = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data

# Python 筛选逻辑
filtered_data = []
for item in raw_data:
    # A. 分类筛选
    if filter_cats and item['category'] not in filter_cats:
        continue
    
    # B. 风格筛选 (包含逻辑：只要包含其中一个选中风格就显示)
    if filter_styles:
        item_styles = [s.strip() for s in item.get('style', '').split(',')]
        # 求交集：如果交集为空，说明没有选中的风格
        if not set(filter_styles).intersection(set(item_styles)):
            continue
            
    filtered_data.append(item)

# 4. Tab 内容渲染
with tabs[0]: # 图库
    # 过滤出有图的
    data_img = [d for d in filtered_data if d['image_url']]
    if not data_img:
        st.info("没有符合条件的图片资产")
    else:
        c_img = st.columns(layout_cols)
        for idx, item in enumerate(data_img):
            with c_img[idx % layout_cols]:
                render_card(item, is_text_only=False)

with tabs[1]: # 纯文本
    # 过滤出无图的
    data_txt = [d for d in filtered_data if not d['image_url']]
    if not data_txt:
        st.info("没有符合条件的纯文本资产")
    else:
        c_txt = st.columns(layout_cols) # 纯文本一般不需要太多列，也可以复用slider
        for idx, item in enumerate(data_txt):
            with c_txt[idx % layout_cols]:
                render_card(item, is_text_only=True)

with tabs[2]: # 收藏
    # 过滤 is_favorite = True，且符合筛选条件
    data_fav = [d for d in filtered_data if d['is_favorite']]
    if not data_fav:
        st.info("没有收藏内容")
    else:
        c_fav = st.columns(layout_cols)
        for idx, item in enumerate(data_fav):
            with c_fav[idx % layout_cols]:
                render_card(item, is_text_only=(item['image_url'] is None))
