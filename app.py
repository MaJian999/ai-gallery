import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI Asset Library", layout="wide", initial_sidebar_state="expanded")

# --- CSS 像素级暴力修复 ---
st.markdown("""
<style>
    /* 1. 登录框居中 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }

    /* ================================================================= */
    /* 核心修复 A：Emoji 绝对居中 (针对三个功能按钮) */
    /* ================================================================= */
    
    /* 1. 锁定中间这三个按钮的外壳 */
    div[data-testid="column"] button {
        aspect-ratio: 1 / 1 !important;
        min-height: 34px !important;
        height: 34px !important;
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid #eee !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        background-color: white !important;
    }

    /* 2. 穿透修复：强制把按钮里的 emoji (p标签) 摁在正中间 */
    div[data-testid="column"] button p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        font-size: 1.1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transform: translateY(-1px); /* 微调：emoji视觉重心通常偏高，往下压1像素 */
    }

    /* 悬停变色 */
    div[data-testid="column"] button:hover {
        border-color: #ff4b4b !important;
        background-color: #fff5f5 !important;
    }

    /* ================================================================= */
    /* 核心修复 B：消灭间距 (Compact Mode) */
    /* ================================================================= */
    
    /* 1. 标题 (h4) */
    h4 {
        margin-bottom: 2px !important;
        padding-bottom: 0 !important;
        font-size: 0.95rem !important;
        line-height: 1.2 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* 2. 标签 (Caption) */
    div[data-testid="stCaptionContainer"] {
        margin-bottom: 4px !important; /* 标题和标签很近 */
        margin-top: 0px !important;
        font-size: 0.75rem !important;
        line-height: 1.2 !important;
        color: #666 !important;
    }

    /* 3. 中间按钮组所在的 Columns 容器 */
    /* 这是一个比较狠的招数：找到按钮上面的那个 div，把它的下边距砍掉 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important; /* 减小列之间的间隙 */
    }
    
    /* 4. 分割线 (hr) */
    hr {
        margin: 8px 0 !important; /* 减小分割线上下的留白 */
    }

    /* ================================================================= */
    /* 其他样式 */
    /* ================================================================= */

    /* 底部大按钮 (提示词) */
    .bottom-wide button {
        width: 100% !important;
        min-height: 36px !important;
        background-color: #f8f9fa !important;
        border-radius: 6px !important;
        font-size: 0.9rem !important;
        aspect-ratio: auto !important; /* 覆盖上面的正方形规则 */
        justify-content: flex-start !important; /* 文字左对齐 */
        padding-left: 10px !important;
    }
    
    /* 底部菜单按钮 (⋮) */
    .bottom-menu button {
        font-weight: bold !important;
        background-color: #f8f9fa !important;
    }

    /* 隐藏 Popover 箭头 */
    div[data-testid="stPopover"] > button > svg { display: none !important; }
    
    /* Tag 样式 */
    .stMultiSelect span {
        background-color: #e8f0fe; 
        color: #1967d2; 
        border-radius: 4px; 
        font-size: 0.85rem;
    }
    
    /* 图片高度限制 */
    img {
        max-height: 600px;
        object-fit: contain;
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

# --- 4. 弹窗 ---
try:
    all_data = supabase.table("gallery").select("category, style").execute().data
    all_cats = sorted(list(set([i['category'] for i in all_data if i.get('category')])))
    raw_s = [i['style'] for i in all_data if i.get('style')]
    all_styles = set()
    for s in raw_s: all_styles.update([t.strip() for t in s.split(',')])
    all_styles = sorted(list(all_styles))
except:
    all_cats = []
    all_styles = []

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
        }).eq("id", item['id']).execute()
        st.rerun()

@st.dialog("🔍 详情", width="large")
def view_dialog(item):
    c1, c2 = st.columns([1.5, 1])
    with c1: 
        if item['image_url']: st.image(item['image_url'])
        else: st.info("无图")
    with c2:
        st.subheader(item['title'])
        st.caption(f"📂 {item['category']} | {item['style']}")
        st.divider()
        st.code(item['prompt'], language=None)

# --- 5. 侧边栏 ---
with st.sidebar:
    st.header("📤 新增")
    new_t = st.text_input("标题 (必填)")
    st.caption("分类")
    c_mode = st.radio("C", ["选", "新"], horizontal=True, label_visibility="collapsed")
    fin_cat = st.selectbox("C", all_cats) if c_mode=="选" else st.text_input("C").strip() or "默认"
    st.caption("风格")
    sel_sty = st.multiselect("S", all_styles)
    new_sty = st.text_input("新S", placeholder="逗号隔开")
    fin_sty_l = sel_sty + [t.strip() for t in new_sty.replace('，',',').split(',') if t.strip()]
    
    p_txt = st.text_area("Prompt", height=100)
    up_file = st.file_uploader("Img", type=['jpg','png','webp'])
    
    if st.button("🚀 提交", type="primary", use_container_width=True):
        if new_t:
            url = None
            if up_file:
                b = up_file.getvalue()
                ext = up_file.name.split('.')[-1]
                name = f"img_{int(time.time())}.{ext}"
                supabase.storage.from_("images").upload(name, b, {"content-type": f"image/{ext}"})
                url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{name}"
            
            supabase.table("gallery").insert({
                "title": new_t, "category": fin_cat, "style": ", ".join(list(set(fin_sty_l))),
                "prompt": p_txt, "image_url": url, "is_pinned": False, "is_favorite": False
            }).execute()
            st.rerun()

# --- 6. 主页 ---
st.title("🌌 资产库")
with st.container(border=True):
    c1, c2, c3 = st.columns([2,2,1])
    f_cat = c1.multiselect("分类", all_cats)
    f_sty = c2.multiselect("风格", all_styles)
    cols = c3.slider("列", 2, 6, 4)

# --- 卡片渲染 ---
def render(item, txt_only=False, k=""):
    with st.container(border=True):
        # 1. 图
        if not txt_only and item['image_url']: st.image(item['image_url'], use_container_width=True)
        elif txt_only: st.info(item['prompt'][:50]+"..." if item['prompt'] else "...")
        
        # 2. 标题
        st.markdown(f"#### {item.get('title','NO NAME')}")
        
        # 3. 标签
        tags = f"{item['category']}"
        if item['style']: tags += f" | {item['style']}"
        st.caption(tags[:30]+"..." if len(tags)>30 else tags)

        # 4. 中间按钮 (View, Pin, Fav) - 紧贴标签下方
        # 这里的 gap="small" 是 Streamlit 1.25+ 特性，配合 CSS 压缩间距
        b1, b2, b3, space = st.columns([1, 1, 1, 2], gap="small")
        with b1:
            if st.button("👁️", key=f"v{item['id']}{k}", help="查看"): view_dialog(item)
        with b2:
            p = "📌" if item['is_pinned'] else "📍"
            if st.button(p, key=f"p{item['id']}{k}"): 
                supabase.table("gallery").update({"is_pinned": not item['is_pinned']}).eq("id", item['id']).execute()
                st.rerun()
        with b3:
            f = "❤️" if item['is_favorite'] else "🤍"
            if st.button(f, key=f"f{item['id']}{k}"):
                supabase.table("gallery").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()

        # 5. 底部 (提示词 & 菜单)
        st.markdown("---") 
        w1, w2 = st.columns([4, 1], gap="small")
        with w1:
            st.markdown('<div class="bottom-wide">', unsafe_allow_html=True)
            with st.popover(f"📄 查看提示词", use_container_width=True): st.code(item['prompt'], language=None)
            st.markdown('</div>', unsafe_allow_html=True)
        with w2:
            st.markdown('<div class="bottom-menu">', unsafe_allow_html=True)
            with st.popover("⋮", use_container_width=True):
                if st.button("✏️ 编辑", key=f"e{item['id']}{k}"): edit_dialog(item)
                if st.button("🗑️ 删除", key=f"d{item['id']}{k}", type="primary"):
                    supabase.table("gallery").delete().eq("id", item['id']).execute()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 列表 ---
raw = supabase.table("gallery").select("*").order("is_pinned", desc=True).order("id", desc=True).execute().data
data = []
for i in raw:
    if f_cat and i['category'] not in f_cat: continue
    if f_sty and not set(f_sty).intersection(set(i.get('style','').split(','))): continue
    data.append(i)

t1, t2, t3 = st.tabs(["图库", "文本", "收藏"])
with t1:
    cur = [x for x in data if x['image_url']]
    c = st.columns(cols)
    for i, x in enumerate(cur): 
        with c[i%cols]: render(x, False, "i")
with t2:
    cur = [x for x in data if not x['image_url']]
    c = st.columns(cols)
    for i, x in enumerate(cur): 
        with c[i%cols]: render(x, True, "t")
with t3:
    cur = [x for x in data if x['is_favorite']]
    c = st.columns(cols)
    for i, x in enumerate(cur): 
        with c[i%cols]: render(x, not x['image_url'], "f")
