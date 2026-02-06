import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI Asset Library", layout="wide", initial_sidebar_state="expanded")

# --- CSS 样式 ---
st.markdown("""
<style>
    /* 1. 基础布局调整 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: 12px !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] { gap: 0px !important; }

    /* 2. 提示词专用样式 (满足你的3点要求) */
    .prompt-box {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px;
        font-family: "Source Code Pro", monospace; /* 保持代码风格字体 */
        font-size: 0.9rem;
        color: #333;
        
        /* 核心要求实现 */
        white-space: pre-wrap !important; /* 强制换行 */
        word-wrap: break-word !important; /* 单词太长也断行 */
        overflow-x: hidden !important;    /* 彻底隐藏横向滚动条 */
        overflow-y: auto !important;      /* 内容多时显示纵向滚动条 */
        max-height: 300px !important;     /* 限制高度，超过则滚动 */
        line-height: 1.5 !important;
    }

    /* 3. 按钮样式 */
    .full-view-btn button {
        width: 100%;
        margin-top: 8px !important; margin-bottom: 4px !important;
        min-height: 32px !important; height: 32px !important;
        border-radius: 6px !important; font-weight: 500 !important;
        background-color: #f0f2f6 !important; border: 1px solid #e0e0e0 !important;
        color: #333 !important; line-height: 1 !important;
    }
    .full-view-btn button:hover { border-color: #ff4b4b !important; color: #ff4b4b !important; }

    .square-icon-btn button {
        aspect-ratio: 1 / 1 !important; width: 100% !important; min-height: 36px !important;
        padding: 0 !important; margin: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        border: 1px solid #eee !important; border-radius: 6px !important; background: white !important;
    }
    .square-icon-btn button p { font-size: 1.2rem !important; margin: 0 !important; transform: translateY(-2px); }
    .square-icon-btn button:hover { border-color: #ff4b4b !important; color: #ff4b4b !important; background-color: #fff5f5 !important; }

    /* 杂项 */
    img { max-height: 70vh !important; object-fit: contain; width: 100%; display: block; }
    div[data-testid="stPopover"] > button > svg { display: none !important; }
    div[data-testid="stPopover"] > button {
         aspect-ratio: 1 / 1 !important; width: 100% !important; min-height: 36px !important;
         display: flex !important; align-items: center !important; justify-content: center !important;
         padding: 0 !important; border: 1px solid #eee !important;
    }
    div[data-testid="stPopover"] > button p { margin: 0 !important; font-size: 1.2rem !important; transform: translateY(-2px); }
    .stMultiSelect span { background-color: #e8f0fe; color: #1967d2; border-radius: 4px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心函数 ---
def check_login():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.title("🔒 AI 资产库")
            password = st.text_input("访问密码", type="password", label_visibility="collapsed")
            if st.button("解锁", use_container_width=True):
                if password == st.secrets["APP_PASSWORD"]: st.session_state.authenticated = True; st.rerun()
                else: st.error("🚫 密码错误")
        st.stop()

@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: st.error("请配置 Secrets！"); st.stop()

check_login(); supabase = init_connection()

# --- 4. 弹窗与数据 ---
try:
    all_data = supabase.table("gallery").select("category, style").execute().data
    all_cats = sorted(list(set([i['category'] for i in all_data if i.get('category')])))
    raw_s = [i['style'] for i in all_data if i.get('style')]
    all_styles = set()
    for s in raw_s: all_styles.update([t.strip() for t in s.split(',')])
    all_styles = sorted(list(all_styles))
except: all_cats = []; all_styles = []

@st.dialog("✏️ 编辑", width="large")
def edit_dialog(item):
    new_title = st.text_input("标题", value=item['title'])
    c1, c2 = st.columns(2)
    with c1:
        cat = item['category']
        cat_sel = st.selectbox("分类", all_cats, index=all_cats.index(cat) if cat in all_cats else 0)
        cat_new = st.text_input("或新建分类")
    with c2:
        cur_sty = [s.strip() for s in item.get('style','').split(',') if s.strip()]
        def_sty = [s for s in cur_sty if s in all_styles]
        sty_sel = st.multiselect("风格", all_styles, default=def_sty)
        sty_new = st.text_input("或新建风格")
    prompt = st.text_area("提示词", value=item['prompt'], height=200)
    
    if st.button("💾 保存", type="primary", use_container_width=True):
        f_cat = cat_new.strip() if cat_new.strip() else cat_sel
        f_sty = sty_sel.copy()
        if sty_new: f_sty.extend([t.strip() for t in sty_new.replace('，',',').split(',') if t.strip()])
        supabase.table("gallery").update({
            "title": new_title, "category": f_cat, "style": ", ".join(list(set(f_sty))), "prompt": prompt
        }).eq("id", item['id']).execute(); st.rerun()

@st.dialog("🔍 详情", width="large")
def view_dialog(item):
    c1, c2 = st.columns([1.8, 1])
    with c1: 
        if item['image_url']: st.image(item['image_url'], use_container_width=True)
        else: st.info("无图")
    with c2:
        st.subheader(item['title'])
        st.caption(f"📂 {item['category']}")
        if item['style']: st.markdown(" ".join([f"`{t.strip()}`" for t in item['style'].split(',')]))
        st.divider()
        st.markdown("**提示词**")
        # 详情页也应用新的提示词样式
        st.markdown(f'<div class="prompt-box">{item["prompt"]}</div>', unsafe_allow_html=True)

# 【核心修改】提示词弹窗
@st.dialog("📄 提示词内容", width="small")
def prompt_dialog(prompt_text):
    # 使用自定义 div 替代 st.code
    st.markdown(f"""
    <div class="prompt-box">
        {prompt_text}
    </div>
    """, unsafe_allow_html=True)
    st.caption("提示：请手动选择文本进行复制")

# --- 5. 侧边栏 ---
with st.sidebar:
    st.header("📤 新增资产")
    new_title = st.text_input("标题 / 备注 (必填)", placeholder="例如: 赛博朋克女孩v1")
    st.write("📂 **分类**")
    cat_mode = st.radio("分类方式", ["已有", "新建"], horizontal=True, label_visibility="collapsed")
    fin_cat = st.selectbox("已有分类", all_cats if all_cats else ["默认分类"], label_visibility="collapsed") if cat_mode=="已有" else (st.text_input("输入新分类", label_visibility="collapsed").strip() or "默认分类")
    st.write("🎨 **风格**")
    selected_styles = st.multiselect("选择风格", all_styles, placeholder="选择标签...")
    new_style_input = st.text_input("新增风格", placeholder="逗号隔开")
    final_style_list = selected_styles + ([t.strip() for t in new_style_input.replace('，',',').split(',') if t.strip()] if new_style_input else [])
    
    prompt_text = st.text_area("提示词 (Prompt)", height=150)
    uploaded_file = st.file_uploader("上传图片 (可选)", type=['jpg', 'png', 'jpeg', 'webp'])
    if st.button("🚀 提交保存", type="primary", use_container_width=True):
        if new_title:
            with st.spinner("处理中..."):
                url = None
                if uploaded_file:
                    b = uploaded_file.getvalue(); ext = uploaded_file.name.split('.')[-1]; name = f"img_{int(time.time())}.{ext}"
                    supabase.storage.from_("images").upload(name, b, {"content-type": f"image/{ext}"})
                    url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{name}"
                supabase.table("gallery").insert({
                    "title": new_title, "category": fin_cat, "style": ", ".join(list(set(final_style_list))),
                    "prompt": prompt_text, "image_url": url, "is_pinned": False, "is_favorite": False
                }).execute(); st.success("✅ 保存成功！"); time.sleep(1); st.rerun()
        else: st.error("⚠️ 标题不能为空")

# --- 6. 主界面 ---
st.title("🌌 我的 AI 资产库")
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: filter_cats = st.multiselect("📂 筛选分类", all_cats, placeholder="全部分类")
    with c2: filter_styles = st.multiselect("🎨 筛选风格", all_styles, placeholder="全部风格")
    with c3: layout_cols = st.slider("列数", 2, 6, 4)

# --- 核心渲染 ---
def render_card(item, is_text_only=False, key_suffix="main"):
    with st.container(border=True):
        # 1. 图片
        if not is_text_only and item['image_url']: st.image(item['image_url'], use_container_width=True)
        elif is_text_only: st.info(item['prompt'][:80] + "..." if item['prompt'] else "无内容")

        # 2. 信息
        tags = f"📂 {item['category']}"
        if item.get('style'): tags += f" | {item['style']}"
        if len(tags) > 40: tags = tags[:40] + "..."
        st.markdown(f"""
        <div style="margin-top: 5px; line-height: 1.2;">
            <div style="font-weight: 600; font-size: 1rem; color: #333;">{item.get('title', '未命名')}</div>
            <div style="font-size: 0.8rem; color: #666;">{tags}</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 全屏查看按钮
        st.markdown('<div class="full-view-btn">', unsafe_allow_html=True)
        if st.button("全屏查看", key=f"v_{item['id']}_{key_suffix}", use_container_width=True):
             view_dialog(item)
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. 底部 4 个图标
        b1, b2, b3, b4 = st.columns(4, gap="small")
        
        with b1:
            st.markdown('<div class="square-icon-btn">', unsafe_allow_html=True)
            p = "📌" if item['is_pinned'] else "📍"
            if st.button(p, key=f"p_{item['id']}_{key_suffix}", help="置顶"): 
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with b2:
            st.markdown('<div class="square-icon-btn">', unsafe_allow_html=True)
            f = "❤️" if item['is_favorite'] else "🤍"
            if st.button(f, key=f"f_{item['id']}_{key_suffix}", help="收藏"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with b3:
            st.markdown('<div class="square-icon-btn">', unsafe_allow_html=True)
            if st.button("📄", key=f"txt_{item['id']}_{key_suffix}", help="查看提示词"):
                prompt_dialog(item['prompt'])
            st.markdown('</div>', unsafe_allow_html=True)

        with b4:
            st.markdown('<div class="square-icon-btn">', unsafe_allow_html=True)
            with st.popover("⋮", use_container_width=True):
                if st.button("✏️ 编辑", key=f"e_{item['id']}_{key_suffix}"): edit_dialog(item)
                if st.button("🗑️ 删除", key=f"d_{item['id']}_{key_suffix}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute(); 
                    if item['image_url']:
                        try: fname = item['image_url'].split('/')[-1]; supabase.storage.from_("images").remove([fname])
                        except: pass
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 列表 ---
raw = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data
filtered = []
for i in raw:
    if filter_cats and i['category'] not in filter_cats: continue
    if filter_styles and not set(filter_styles).intersection(set(i.get('style','').split(','))): continue
    filtered.append(i)

t1, t2, t3 = st.tabs(["🖼️ 灵感图库", "📝 纯提示词", "⭐ 收藏"])
with t1:
    d = [x for x in filtered if x['image_url']]
    c = st.columns(layout_cols)
    for i, x in enumerate(d): 
        with c[i%layout_cols]: render_card(x, False, "img")
with t2:
    d = [x for x in filtered if not x['image_url']]
    c = st.columns(layout_cols)
    for i, x in enumerate(d): 
        with c[i%layout_cols]: render_card(x, True, "txt")
with t3:
    d = [x for x in filtered if x['is_favorite']]
    c = st.columns(layout_cols)
    for i, x in enumerate(d): 
        with c[i%layout_cols]: render_card(x, (x['image_url'] is None), "fav")
