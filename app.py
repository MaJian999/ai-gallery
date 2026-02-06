import streamlit as st
from supabase import create_client
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 灵感库 Pro Max", layout="wide", initial_sidebar_state="expanded")

# --- CSS: 登录框居中 ---
st.markdown("""
<style>
    .login-container { display: flex; justify-content: center; align-items: center; height: 60vh; flex-direction: column; }
    .stTextInput input { text-align: center; }
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
            st.title("🔒 灵感库保险箱")
            st.info("请输入访问密码")
            password = st.text_input("Password", type="password", label_visibility="collapsed")
            if st.button("解锁进入", use_container_width=True):
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
st.title("🎨 AI 灵感收藏夹 Pro Max")

# --- 4. 侧边栏：上传逻辑 (逻辑重构) ---
with st.sidebar:
    st.header("📤 录入新作品")
    
    # A. 获取现有分类 (Category)
    try:
        cat_query = supabase.table("gallery").select("category").execute()
        # 提取去重，过滤掉None
        existing_cats = list(set([item['category'] for item in cat_query.data if item and item.get('category')]))
        existing_cats.sort()
    except:
        existing_cats = []
    
    # B. 分类选择 (必填，默认为"默认分类")
    cat_mode = st.radio("分类来源", ["选择已有", "创建新分类"], horizontal=True, label_visibility="collapsed")
    
    final_category = "默认分类" # 兜底默认值
    
    if cat_mode == "选择已有" and existing_cats:
        final_category = st.selectbox("选择分类 (Category)", existing_cats)
    else:
        new_cat_input = st.text_input("新建分类 (Category)", placeholder="例如: 角色设计")
        if new_cat_input.strip():
            final_category = new_cat_input.strip()

    # C. 风格与内容 (选填)
    style_tag = st.text_input("风格标签 (Style - 选填)", placeholder="例如: 赛博朋克, 3D渲染")
    prompt_text = st.text_area("提示词 (Prompt - 选填)", height=150)
    uploaded_file = st.file_uploader("上传图片 (必填)", type=['jpg', 'png', 'jpeg', 'webp'])

    # D. 提交逻辑
    if st.button("🚀 提交保存", type="primary"):
        if uploaded_file: # 只有图片是硬性必填
            with st.spinner("正在上传..."):
                # 1. 上传图片
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"img_{int(time.time())}.{file_ext}"
                
                supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                img_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{file_name}"

                # 2. 存入数据库 (category必填, 其他选填)
                data = {
                    "category": final_category,
                    "style": style_tag if style_tag else "",
                    "prompt": prompt_text if prompt_text else "",
                    "image_url": img_url
                }
                supabase.table("gallery").insert(data).execute()
                
                st.success(f"✅ 已存入分类：{final_category}")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("⚠️ 请至少上传一张图片")

# --- 5. 主界面：展示逻辑 ---

# 顶部筛选栏
col_filter, col_layout = st.columns([3, 1])
with col_filter:
    # 这里现在筛选的是 "分类 (Category)"
    if existing_cats:
        selected_cats = st.multiselect("📂 按分类筛选", existing_cats, placeholder="显示全部分类")
    else:
        selected_cats = []
with col_layout:
    num_columns = st.slider("👁️ 布局", 2, 6, 4)

st.divider()

# 数据读取
query = supabase.table("gallery").select("*").order("id", desc=True)
if selected_cats:
    query = query.in_("category", selected_cats) # 按分类过滤
items = query.execute().data

if not items:
    st.info("📭 暂无数据")

# 瀑布流
cols = st.columns(num_columns)

for idx, item in enumerate(items):
    with cols[idx % num_columns]:
        with st.container(border=True):
            st.image(item['image_url'], use_container_width=True)
            
            # 展示信息：主分类 + 风格标签
            # 只有当 style 有值时才显示 style
            caption_text = f"📂 {item.get('category', '默认分类')}"
            if item.get('style'):
                caption_text += f" | 🏷️ {item['style']}"
            st.caption(caption_text)
            
            # 按钮区
            b1, b2, b3 = st.columns([1, 2, 1])
            
            # --- 功能 A: 全能编辑 (修改分类、风格、提示词) ---
            with b1:
                with st.popover("✏️"):
                    st.markdown("### 修改作品信息")
                    with st.form(key=f"edit_form_{item['id']}"):
                        # 所有字段都可修改
                        new_cat = st.text_input("分类 (Category)", value=item.get('category', '默认分类'))
                        new_style = st.text_input("风格 (Style)", value=item.get('style', ''))
                        new_prompt = st.text_area("提示词", value=item.get('prompt', ''), height=150)
                        
                        st.markdown("---")
                        st.markdown("**更换图片 (选填):**")
                        new_img_file = st.file_uploader("上传新图替换旧图", type=['jpg', 'png', 'webp'], key=f"u_{item['id']}")
                        
                        if st.form_submit_button("确认修改"):
                            update_data = {
                                "category": new_cat,
                                "style": new_style,
                                "prompt": new_prompt
                            }
                            
                            # 图片替换逻辑
                            if new_img_file:
                                try:
                                    old_name = item['image_url'].split('/')[-1]
                                    supabase.storage.from_("images").remove([old_name])
                                except: pass
                                
                                f_bytes = new_img_file.getvalue()
                                f_ext = new_img_file.name.split('.')[-1]
                                f_name = f"img_{int(time.time())}.{f_ext}"
                                supabase.storage.from_("images").upload(f_name, f_bytes, {"content-type": f"image/{f_ext}"})
                                
                                new_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{f_name}"
                                update_data["image_url"] = new_url
                            
                            supabase.table("gallery").update(update_data).eq("id", item['id']).execute()
                            st.success("修改成功！")
                            time.sleep(0.5)
                            st.rerun()

            # --- 功能 B: 提示词 (如果为空则显示无) ---
            with b2:
                with st.popover("📄 提示词", use_container_width=True):
                    if item.get('prompt'):
                        st.code(item['prompt'], language=None)
                    else:
                        st.info("未记录提示词")

            # --- 功能 C: 删除 ---
            with b3:
                with st.popover("🗑️"):
                    st.write("确认删除？")
                    if st.button("Yes", key=f"del_{item['id']}", type="primary"):
                        supabase.table("gallery").delete().eq("id", item['id']).execute()
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except: pass
                        st.rerun()
