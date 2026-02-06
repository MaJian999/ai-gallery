import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 资产库 Ultimate v8", layout="wide", initial_sidebar_state="expanded")

# --- CSS 终极适配 ---
st.markdown("""
<style>
    /* 1. 登录框居中 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
    
    /* 2. 核心按钮样式 (正方形、大图标) */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] > div > div > div > button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-height: 0px !important;
        height: auto !important;
        padding: 0px !important;
        font-size: 1.1rem !important;    
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid #f0f2f6 !important;
        border-radius: 8px !important;
        margin: 0 auto !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* 悬停效果 */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] > div > div > div > button:hover {
        border-color: #ff4b4b !important;
        background-color: #fff1f1 !important;
        color: #ff4b4b !important;
        transform: scale(1.05);
        transition: all 0.2s;
    }

    /* 3. 菜单内按钮 (长条形) */
    div[data-testid="stPopoverBody"] button {
        aspect-ratio: auto !important;
        width: 100% !important;
        height: auto !important;
        padding: 0.5rem 1rem !important;
        justify-content: flex-start !important;
        border: 1px solid #eee !important;
        margin-bottom: 5px !important;
    }
    
    /* 4. 隐藏 Popover 默认箭头 */
    div[data-testid="stPopover"] > button > svg { display: none !important; }
    div[data-testid="stPopover"] > button > div { margin: 0 !important; padding: 0 !important; }

    /* 5. 多选框 Tag 样式 */
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

# --- 4. 功能弹窗 (Dialogs) ---

# A. 编辑信息弹窗
@st.dialog("✏️ 编辑作品信息")
def edit_dialog(item, all_cats, all_styles):
    new_title = st.text_input("标题", value=item['title'])
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        current_cat = item['category']
        cat_index = all_cats.index(current_cat) if current_cat in all_cats else 0
        edit_cat_sel = st.selectbox("分类 (已有)", all_cats, index=cat_index)
        edit_cat_new = st.text_input("或：新建分类")
    with col_d2:
        current_style_str = item.get('style', '')
        current_style_list = [s.strip() for s in current_style_str.split(',')] if current_style_str else []
        default_styles = [s for s in current_style_list if s in all_styles]
        edit_style_sel = st.multiselect("风格 (多选)", all_styles, default=default_styles)
        edit_style_new = st.text_input("或：新建风格")

    new_prompt = st.text_area("提示词", value=item['prompt'], height=200)
    
    if st.button("💾 保存修改", type="primary", use_container_width=True):
        final_cat = edit_cat_new.strip() if edit_cat_new.strip() else edit_cat_sel
        final_styles = edit_style_sel.copy()
        if edit_style_new:
            final_styles.extend([t.strip() for t in edit_style_new.replace('，', ',').split(',') if t.strip()])
        final_style_str = ", ".join(list(set(final_styles)))
        
        supabase.table("gallery").update({
            "title": new_title, 
            "category": final_cat, 
            "style": final_style_str, 
            "prompt": new_prompt
        }).eq("id", item['id']).execute()
        st.success("修改已保存！")
        time.sleep(0.5)
        st.rerun()

# B. 全屏详情弹窗 (Lightbox)
@st.dialog("🔍 作品详情", width="large")
def view_dialog(item):
    # 左右布局：左图右文
    col_img, col_info = st.columns([1.5, 1])
    
    with col_img:
        if item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        else:
            st.info("纯文本资产，无图片")
            
    with col_info:
        st.subheader(item['title'])
        st.caption(f"📂 **{item['category']}**")
        
        # 风格标签
        if item['style']:
            tags = item['style'].split(',')
            st.markdown(" ".join([f"`{t.strip()}`" for t in tags]))
        
        st.divider()
        st.markdown("**提示词**")
        # st.code 自带复制按钮，完美满足需求
        st.code(item['prompt'], language=None)
        
        st.caption("提示：点击代码块右上角的图标即可复制")


# --- 5. 侧边栏：录入系统 ---
with st.sidebar:
    st.header("📤 新增资产")
    new_title = st.text_input("标题 / 备注 (必填)", placeholder="例如: 赛博朋克女孩v1")

    st.write("📂 **分类**")
    cat_mode = st.radio("分类方式", ["已有", "新建"], horizontal=True, label_visibility="collapsed")
    if cat_mode == "已有":
        final_category = st.selectbox("已有分类", all_cats if all_cats else ["默认分类"], label_visibility="collapsed")
    else:
        final_category = st.text_input("输入新分类", label_visibility="collapsed").strip()
        if not final_category: final_category = "默认分类"

    st.write("🎨 **风格**")
    selected_styles = st.multiselect("选择风格", all_styles, placeholder="选择标签...")
    new_style_input = st.text_input("新增风格", placeholder="输入新标签，逗号隔开")
    
    final_style_list = selected_styles.copy()
    if new_style_input:
        manual_tags = [t.strip() for t in new_style_input.replace('，', ',').split(',') if t.strip()]
        final_style_list.extend(manual_tags)
    final_style_str = ", ".join(list(set(final_style_list)))

    prompt_text = st.text_area("提示词", height=150)
    uploaded_file = st.file_uploader("上传图片", type=['jpg', 'png', 'jpeg', 'webp'])

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
                    "title": new_title, "category": final_category, "style": final_style_str,
                    "prompt": prompt_text, "image_url": img_url,
                    "is_pinned": False, "is_favorite": False
                }
                supabase.table("gallery").insert(data).execute()
                st.success("✅ 保存成功！")
                time.sleep(1)
                st.rerun()
        else:
            st.error("⚠️ 标题不能为空")

# --- 6. 主界面 ---
st.title("🌌 我的 AI 资产库")

with st.container(border=True):
    f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
    with f_col1: filter_cats = st.multiselect("📂 筛选分类", all_cats, placeholder="全部分类")
    with f_col2: filter_styles = st.multiselect("🎨 筛选风格", all_styles, placeholder="全部风格")
    with f_col3: layout_cols = st.slider("列数", 2, 6, 4)

# --- 核心卡片渲染 ---
def render_card(item, is_text_only=False, key_suffix="main"):
    with st.container(border=True):
        # 1. 图片区
        if not is_text_only and item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        elif is_text_only:
            st.info(item['prompt'][:100] + "..." if item['prompt'] else "(无内容)")
        
        # 2. 标题区
        st.markdown(f"#### {item.get('title', '未命名')}")
        
        # 3. 标签区
        current_style_str = item.get('style', '')
        current_style_list = [s.strip() for s in current_style_str.split(',')] if current_style_str else []
        tags_display = f"📂 {item['category']}"
        if current_style_list:
            tags_display += f" | 🎨 {', '.join(current_style_list)}"
        if len(tags_display) > 40: st.caption(tags_display[:40] + "...")
        else: st.caption(tags_display)

        # 4. 底部操作栏 (5列布局)
        # [查看] [置顶] [收藏] [复制] [更多]
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            # 👁️ 全屏详情 (Lightbox)
            if st.button("👁️", key=f"view_{item['id']}_{key_suffix}", help="全屏详情"):
                view_dialog(item)
        
        with c2:
            pin_icon = "📌" if item['is_pinned'] else "📍"
            if st.button(pin_icon, key=f"pin_{item['id']}_{key_suffix}", help="置顶"):
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
        
        with c3:
            fav_icon = "❤️" if item['is_favorite'] else "🤍"
            if st.button(fav_icon, key=f"fav_{item['id']}_{key_suffix}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()

        with c4:
            # 📄 复制 (Popover 形式，因为 st.code 需要容器)
            # 点击后直接展示代码，方便复制
            with st.popover("📄", use_container_width=True, help="复制提示词"):
                 st.code(item['prompt'], language=None)

        with c5:
            # ⋮ 更多菜单 (收纳低频操作)
            with st.popover("⋮", use_container_width=True):
                st.caption("管理")
                # 编辑 -> 触发编辑弹窗
                if st.button("✏️ 编辑", key=f"edit_{item['id']}_{key_suffix}"):
                    edit_dialog(item, all_cats, all_styles)
                
                # 删除 -> 红色按钮
                if st.button("🗑️ 删除", key=f"del_{item['id']}_{key_suffix}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    if item['image_url']:
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()

# --- 数据筛选 ---
raw_data = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data
filtered_data = []
for item in raw_data:
    if filter_cats and item['category'] not in filter_cats: continue
    if filter_styles:
        item_styles = [s.strip() for s in item.get('style', '').split(',')]
        if not set(filter_styles).intersection(set(item_styles)): continue
    filtered_data.append(item)

# --- Tab 展示 ---
tabs = st.tabs(["🖼️ 灵感图库", "📝 纯提示词", "⭐ 我的收藏"])

with tabs[0]:
    data_img = [d for d in filtered_data if d['image_url']]
    if not data_img: st.info("暂无图片")
    else:
        c_img = st.columns(layout_cols)
        for idx, item in enumerate(data_img):
            with c_img[idx % layout_cols]: render_card(item, False, "img")

with tabs[1]:
    data_txt = [d for d in filtered_data if not d['image_url']]
    if not data_txt: st.info("暂无文本")
    else:
        c_txt = st.columns(layout_cols)
        for idx, item in enumerate(data_txt):
            with c_txt[idx % layout_cols]: render_card(item, True, "txt")

with tabs[2]:
    data_fav = [d for d in filtered_data if d['is_favorite']]
    if not data_fav: st.info("暂无收藏")
    else:
        c_fav = st.columns(layout_cols)
        for idx, item in enumerate(data_fav):
            with c_fav[idx % layout_cols]: render_card(item, (item['image_url'] is None), "fav")
