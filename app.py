import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI Asset Library", layout="wide", initial_sidebar_state="expanded")

# --- CSS 暴力去间隙版 ---
st.markdown("""
<style>
    /* 1. 登录框居中 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }

    /* ================================================================= */
    /* 新思路：使用负边距 (Negative Margin) 强制压缩垂直空间 */
    /* ================================================================= */

    /* 1. 标题 (h4) - 紧贴图片 */
    h4 {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        padding-top: 5px !important;
        font-size: 1rem !important;
        line-height: 1.2 !important;
    }

    /* 2. 标签 (Caption) - 紧贴标题 */
    div[data-testid="stCaptionContainer"] {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        margin-top: 0px !important;
        line-height: 1 !important;
    }

    /* 3. 中间三个按钮 (View, Pin, Fav) 的容器修正 */
    /* 这里的核心是用 margin-top: -5px 把这一行硬提上去 */
    .icon-row {
        margin-top: -10px !important; 
        margin-bottom: -10px !important;
    }

    /* 4. 按钮本体 - 绝对居中 + 紧凑 */
    .icon-btn button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-height: 32px !important; /*稍微改小一点点，显得更精致*/
        height: auto !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid #f0f2f6 !important;
        border-radius: 6px !important;
        background-color: white !important;
        box-shadow: 0 1px 1px rgba(0,0,0,0.05);
    }
    
    /* 强制 Emoji 居中 */
    .icon-btn button p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        font-size: 1.1rem !important;
        transform: translateY(-2px);
    }

    /* 5. 分割线 - 压缩上下间距 */
    hr {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
        border-top: 1px solid #f0f2f6 !important;
    }

    /* ================================================================= */
    /* 其他样式保持不变 */
    /* ================================================================= */

    .wide-btn button {
        width: 100% !important;
        min-height: 38px !important;
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        color: #333 !important;
        justify-content: flex-start !important;
        padding-left: 10px !important;
    }
    
    .menu-btn button {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-height: 38px !important;
        border-radius: 6px !important;
    }

    .icon-btn button:hover { border-color: #ff4b4b !important; background-color: #fff1f1 !important; color: #ff4b4b !important; }
    div[data-testid="stPopover"] > button > svg { display: none !important; }
    .stMultiSelect span { background-color: #e8f0fe; color: #1967d2; border-radius: 4px; font-size: 0.85rem; }
    img { max-height: 600px; object-fit: contain; }
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

# --- 4. 弹窗与数据 ---
try:
    all_data = supabase.table("gallery").select("category, style").execute().data
    all_cats = sorted(list(set([i['category'] for i in all_data if i.get('category')])))
    raw_s = [i['style'] for i in all_data if i.get('style')]
    all_styles = set()
    for s in raw_s: 
        tags = [t.strip() for t in s.split(',')]
        all_styles.update(tags)
    all_styles = sorted(list(all_styles))
except:
    all_cats = []
    all_styles = []

@st.dialog("✏️ 编辑信息", width="large")
def edit_dialog(item):
    new_title = st.text_input("标题", value=item['title'])
    c1, c2 = st.columns(2)
    with c1:
        cur_cat = item['category']
        idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        cat_sel = st.selectbox("分类 (已有)", all_cats, index=idx)
        cat_new = st.text_input("或：新建分类")
    with c2:
        cur_style = item.get('style', '')
        cur_list = [s.strip() for s in cur_style.split(',')] if cur_style else []
        def_style = [s for s in cur_list if s in all_styles]
        style_sel = st.multiselect("风格 (多选)", all_styles, default=def_style)
        style_new = st.text_input("或：新建风格")

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

@st.dialog("🔍 作品详情", width="large")
def view_dialog(item):
    col_img, col_info = st.columns([1.8, 1])
    with col_img:
        if item['image_url']: st.image(item['image_url'], use_container_width=True)
        else: st.info("无图片")
    with col_info:
        st.subheader(item['title'])
        st.caption(f"📂 {item['category']}")
        if item['style']:
            st.markdown(" ".join([f"`{t.strip()}`" for t in item['style'].split(',')]))
        st.divider()
        st.caption("提示词:")
        st.code(item['prompt'], language=None)

# --- 5. 侧边栏 (完整版 - 保持不动) ---
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

    prompt_text = st.text_area("提示词 (Prompt)", height=150)
    uploaded_file = st.file_uploader("上传图片 (可选)", type=['jpg', 'png', 'jpeg', 'webp'])

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
    f1, f2, f3 = st.columns([2, 2, 1])
    with f1: filter_cats = st.multiselect("📂 筛选分类", all_cats, placeholder="全部分类")
    with f2: filter_styles = st.multiselect("🎨 筛选风格", all_styles, placeholder="全部风格")
    with f3: layout_cols = st.slider("列数", 2, 6, 4)

# --- 核心卡片渲染 ---
def render_card(item, is_text_only=False, key_suffix="main"):
    with st.container(border=True):
        
        # 1. 图片
        if not is_text_only and item['image_url']:
            st.image(item['image_url'], use_container_width=True)
        elif is_text_only:
            st.info(item['prompt'][:80] + "..." if item['prompt'] else "无内容")

        # 2. 标题
        st.markdown(f"#### {item.get('title', '未命名')}")

        # 3. 标签
        tags = f"📂 {item['category']}"
        if item.get('style'): tags += f" | {item['style']}"
        st.caption(tags if len(tags)<40 else tags[:40]+"...")

        # 4. 中间工具栏：View | Pin | Fav (高度紧凑版)
        # 增加一个 div 容器，应用 .icon-row 样式 (margin 负值)
        st.markdown('<div class="icon-row">', unsafe_allow_html=True)
        
        b1, b2, b3, space = st.columns([1, 1, 1, 3], gap="small")
        with b1:
            st.markdown('<div class="icon-btn">', unsafe_allow_html=True)
            if st.button("👁️", key=f"v_{item['id']}_{key_suffix}", help="查看"): view_dialog(item)
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            st.markdown('<div class="icon-btn">', unsafe_allow_html=True)
            p = "📌" if item['is_pinned'] else "📍"
            if st.button(p, key=f"p_{item['id']}_{key_suffix}", help="置顶"): 
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with b3:
            st.markdown('<div class="icon-btn">', unsafe_allow_html=True)
            f = "❤️" if item['is_favorite'] else "🤍"
            if st.button(f, key=f"f_{item['id']}_{key_suffix}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) # end icon-row

        # 5. 底部按钮
        st.markdown("---") 
        w1, w2 = st.columns([4, 1], gap="small")
        
        with w1:
            st.markdown('<div class="wide-btn">', unsafe_allow_html=True)
            with st.popover("📄 查看提示词", use_container_width=True):
                 st.code(item['prompt'], language=None)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with w2:
            st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
            with st.popover("⋮", use_container_width=True):
                if st.button("✏️ 编辑", key=f"e_{item['id']}_{key_suffix}"):
                    edit_dialog(item)
                if st.button("🗑️ 删除", key=f"d_{item['id']}_{key_suffix}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    if item['image_url']:
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 列表与展示 ---
raw = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data
filtered = []
for i in raw:
    if filter_cats and i['category'] not in filter_cats: continue
    if filter_styles:
        if not set(filter_styles).intersection(set([s.strip() for s in i.get('style','').split(',')])): continue
    filtered.append(i)

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
