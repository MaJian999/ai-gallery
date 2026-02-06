import streamlit as st
from supabase import create_client
import time

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="AI 灵感库 Pro Max", layout="wide", initial_sidebar_state="expanded")

# --- CSS 魔法：让登录框居中 & 隐藏不需要的元素 ---
st.markdown("""
<style>
    /* 登录界面的居中样式 */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 60vh; /* 占据视口高度 */
        flex-direction: column;
    }
    .stTextInput input {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心功能函数 ---

# A. 居中登录验证系统 (你的需求：密码框居中)
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # 使用 3 列布局，让中间那列占据主要位置，实现水平居中
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True) # 稍微往下顶一点
            st.title("🔒 灵感库保险箱")
            st.info("请输入访问密码")
            password = st.text_input("Password", type="password", label_visibility="collapsed")
            
            if st.button("解锁进入", use_container_width=True):
                if password == st.secrets["APP_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🚫 密码错误，请重试")
        st.stop() 

# B. 获取数据库连接
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("请先在 Secrets 配置 SUPABASE_URL 和 SUPABASE_KEY")
        st.stop()

# --- 3. 程序主入口 ---
check_login()
supabase = init_connection()

st.title("🎨 AI 灵感收藏夹 Pro Max")

# --- 4. 侧边栏：上传与录入 ---
with st.sidebar:
    st.header("📤 录入新作品")
    
    # 获取现有分类
    existing_styles_query = supabase.table("gallery").select("style").execute()
    existing_styles = list(set([item['style'] for item in existing_styles_query.data if item['style']]))
    existing_styles.sort()
    
    # 分类输入逻辑
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
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"img_{int(time.time())}.{file_ext}"
                
                # 上传 & 入库
                supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                img_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{file_name}"
                data = {"prompt": prompt_text, "style": selected_style, "image_url": img_url}
                supabase.table("gallery").insert(data).execute()
                
                st.success(f"✅ 已存入分类：{selected_style}")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("请补全所有信息")

# --- 5. 主界面：筛选与展示 ---

col_filter, col_layout = st.columns([3, 1])
with col_filter:
    if existing_styles:
        selected_filters = st.multiselect("🔍 风格/分类筛选", existing_styles, placeholder="显示全部")
    else:
        selected_filters = []
with col_layout:
    num_columns = st.slider("👁️ 布局", min_value=2, max_value=6, value=4)

st.divider()

# 读取数据
query = supabase.table("gallery").select("*").order("id", desc=True)
if selected_filters:
    query = query.in_("style", selected_filters)
items = query.execute().data

if not items:
    st.info("📭 暂无数据")

# --- 瀑布流展示 (含编辑功能) ---
cols = st.columns(num_columns)

for idx, item in enumerate(items):
    with cols[idx % num_columns]:
        with st.container(border=True):
            st.image(item['image_url'], use_container_width=True)
            st.caption(f"🏷️ {item['style']}")
            
            # 按钮组：编辑 | 提示词 | 删除
            b1, b2, b3 = st.columns([1, 2, 1])
            
            # --- 功能 A: 编辑 (你的新需求) ---
            with b1:
                with st.popover("✏️"):
                    st.markdown("### 修改作品信息")
                    with st.form(key=f"edit_form_{item['id']}"):
                        # 1. 修改文本信息
                        new_style = st.text_input("风格/分类", value=item['style'])
                        new_prompt = st.text_area("提示词", value=item['prompt'], height=150)
                        
                        # 2. 修改图片 (可选)
                        st.markdown("**更换图片 (不填则保持原图):**")
                        new_img_file = st.file_uploader("上传新图", type=['jpg', 'png', 'webp'], key=f"u_{item['id']}")
                        
                        if st.form_submit_button("确认修改"):
                            update_data = {"style": new_style, "prompt": new_prompt}
                            
                            # 如果用户传了新图，处理图片上传逻辑
                            if new_img_file:
                                try:
                                    # 删除旧图 (从URL解析文件名)
                                    old_file_name = item['image_url'].split('/')[-1]
                                    supabase.storage.from_("images").remove([old_file_name])
                                except:
                                    pass # 忽略删除错误
                                
                                # 上传新图
                                f_bytes = new_img_file.getvalue()
                                f_ext = new_img_file.name.split('.')[-1]
                                f_name = f"img_{int(time.time())}.{f_ext}"
                                supabase.storage.from_("images").upload(f_name, f_bytes, {"content-type": f"image/{f_ext}"})
                                
                                # 更新链接
                                new_url = f"{st.secrets['SUPABASE_URL']}/storage/v1/object/public/images/{f_name}"
                                update_data["image_url"] = new_url
                            
                            # 执行数据库更新
                            supabase.table("gallery").update(update_data).eq("id", item['id']).execute()
                            st.success("修改成功！")
                            time.sleep(0.5)
                            st.rerun()

            # --- 功能 B: 查看提示词 ---
            with b2:
                with st.popover("📄 提示词", use_container_width=True):
                    st.code(item['prompt'], language=None)

            # --- 功能 C: 删除 ---
            with b3:
                with st.popover("🗑️"):
                    st.write("确认删除？")
                    if st.button("Yes", key=f"del_{item['id']}", type="primary"):
                        supabase.table("gallery").delete().eq("id", item['id']).execute()
                        try:
                            fname = item['image_url'].split('/')[-1]
                            supabase.storage.from_("images").remove([fname])
                        except:
                            pass
                        st.rerun()
