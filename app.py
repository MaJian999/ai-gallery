import streamlit as st
from supabase import create_client
import time

# 页面基础设置
st.set_page_config(page_title="我的 AI 图库", layout="wide")
st.title("🎨 我的 AI 灵感收藏夹")

# --- 连接数据库 ---
# 这里的 secrets 会自动从 Streamlit 后台读取，不用改代码
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(supabase_url, supabase_key)
except:
    st.error("请先在 Streamlit 后台配置 Secrets！")
    st.stop()

# --- 侧边栏：上传区 ---
with st.sidebar:
    st.header("📤 上传新图")
    uploaded_file = st.file_uploader("选择图片", type=['jpg', 'png', 'jpeg'])
    prompt = st.text_area("提示词 (Prompt)", height=150)
    style = st.text_input("风格标签 (例如: 赛博朋克)")
    
    if st.button("提交保存", type="primary"):
        if uploaded_file and prompt:
            with st.spinner("正在上传云端..."):
                # 1. 上传图片到 Storage
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"img_{int(time.time())}.{file_ext}"
                
                # 执行上传
                supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": f"image/{file_ext}"})
                
                # 2. 拼接图片的公开链接
                img_url = f"{supabase_url}/storage/v1/object/public/images/{file_name}"

                # 3. 写入数据库
                data = {"prompt": prompt, "style": style, "image_url": img_url}
                supabase.table("gallery").insert(data).execute()
                
                st.success("✅ 保存成功！")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("图片和提示词不能为空哦")

# --- 主界面：展示区 ---
st.subheader("🖼️ 灵感瀑布流")

# 读取数据 (按时间倒序)
response = supabase.table("gallery").select("*").order("id", desc=True).execute()
items = response.data

if not items:
    st.info("还没有图片，快去左边上传一张吧！")

# 3列布局
cols = st.columns(3)
for idx, item in enumerate(items):
    with cols[idx % 3]:
        with st.container(border=True):
            st.image(item['image_url'], use_container_width=True)
            if item['style']:
                st.caption(f"🏷️ {item['style']}")
            
            # 提示词和复制
            st.text_area("提示词", value=item['prompt'], height=100, key=f"txt_{item['id']}")
            
            # 删除按钮
            if st.button("🗑️ 删除", key=f"del_{item['id']}"):
                # 1. 删记录
                supabase.table("gallery").delete().eq("id", item['id']).execute()
                # 2. 删图片 (文件名从URL里拆出来)
                file_name_in_url = item['image_url'].split('/')[-1]
                supabase.storage.from_("images").remove([file_name_in_url])
                st.rerun()
