import streamlit as st
from supabase import create_client
import time

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="AI 灵感库 Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. 核心功能函数 ---

# A. 登录验证系统 (你的需求1)
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("### 🔒 请输入密码访问")
        password = st.text_input("Password", type="password")
        if st.button("登录"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误")
        st.stop() # 如果没登录，停止加载后面的代码

# B. 获取数据库连接
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("请先在 Secrets 配置 SUPABASE_URL 和 SUPABASE_KEY")
        st.stop()

# --- 3. 程序主入口 ---
check_login() # 先拦路查密码
supabase = init_connection()

st.title("🎨 AI 灵感收藏夹 Pro")

# --- 4. 侧边栏：上传与录入 ---
with st.sidebar:
    st.header("📤 录入新作品")
    
    # 获取现有所有分类 (用于下拉选择)
    existing_styles_query = supabase.table("gallery").select("style").execute()
    existing_styles = list(set([item['style'] for item in existing_styles_query.data if item['style']]))
    existing_styles.sort()
    
    # --- 智能分类输入框 (你的需求4) ---
    selection_mode = st.radio("分类方式", ["选择已有", "创建新分类"], horizontal=True, label_visibility="collapsed")
    
    if selection_mode == "选择已有" and existing_styles:
        selected_style = st.selectbox("选择风格标签", existing_styles)
    else:
        selected_style = st.text_input("输入新风格名称 (例如: 赛博朋克)")

    uploaded_file = st.file_uploader("拖拽上传图片", type=['jpg', 'png', 'jpeg', 'webp'])
    prompt_text = st.text_area("提示词 (Prompt)", height=150)

    if st.button("🚀 提交保存", type="primary"):
        if uploaded_file and prompt_text and selected_style:
            with st.spinner("正在上传云端..."):
                # 1. 上传图片
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"img_{int(time.time())}.{file_ext}"
                supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                
                # 2. 生成链接
                img_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{file_name}"

                # 3. 存入数据库
                data = {"prompt": prompt_text, "style": selected_style, "image_url": img_url}
                supabase.table("gallery").insert(data).execute()
                
                st.success(f"✅ 已存入分类：{selected_style}")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("请补全：图片、提示词和风格标签")

    st.divider()
    st.caption("Designed for myself.")

# --- 5. 主界面：筛选与展示 ---

# --- 顶部控制栏 (你的需求3 & 5) ---
col_filter, col_layout = st.columns([3, 1])

with col_filter:
    # 筛选器
    if existing_styles:
        selected_filters = st.multiselect("🔍 风格筛选", existing_styles, placeholder="显示全部风格")
    else:
        selected_filters = []

with col_layout:
    # 布局控制器 (类似你的截图，用滑块控制一行几个)
    num_columns = st.slider("👁️ 布局(每行几张)", min_value=2, max_value=6, value=4)

st.divider()

# --- 读取数据逻辑 ---
query = supabase.table("gallery").select("*").order("id", desc=True)
if selected_filters:
    query = query.in_("style", selected_filters) # 添加筛选条件
response = query.execute()
items = response.data

if not items:
    st.info("📭 暂无数据，去侧边栏上传一张吧！")

# --- 瀑布流展示核心 (你的需求2 & 6) ---
cols = st.columns(num_columns) # 根据滑块动态生成列

for idx, item in enumerate(items):
    with cols[idx % num_columns]:
        # 使用 container 框住每一个作品
        with st.container(border=True):
            # 1. 纯净看图
            st.image(item['image_url'], use_container_width=True)
            
            # 风格小标签
            st.caption(f"🏷️ {item['style']}")
            
            # 操作栏 (一行两个按钮：查看提示词、删除)
            btn_col1, btn_col2 = st.columns([4, 1])
            
            with btn_col1:
                # 2. 隐藏的提示词与复制 (popover实现点击才弹窗)
                with st.popover("📄 提示词"):
                    st.markdown("**Prompt:**")
                    # st.code 自带右上角复制按钮
                    st.code(item['prompt'], language=None)
            
            with btn_col2:
                # 3. 防误删 (popover实现二级确认)
                with st.popover("🗑️"):
                    st.write("确定删除？")
                    if st.button("确认", key=f"del_{item['id']}", type="primary"):
                        # 删除数据库记录
                        supabase.table("gallery").delete().eq("id", item['id']).execute()
                        # 删除云端文件 (从URL提取文件名)
                        try:
                            file_name = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([file_name])
                        except:
                            pass # 就算文件删失败也不报错
                        st.rerun()
