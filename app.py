import streamlit as st

# 把 CSS 样式包裹在 st.markdown 中
st.markdown("""
    <style>
        /* 针对 Streamlit 的弹窗 (Modal/Dialog) 进行样式覆盖 */
        div[data-testid="stDialog"] div[role="dialog"] {
            width: 90vw !important;  /* 宽度占屏幕 90% */
            max-width: 90vw !important;
            height: 90vh !important; /* 高度占屏幕 90% */
            max-height: 90vh !important;
            display: flex;
            flex-direction: column;
        }

        /* 让弹窗内部的内容区域自适应高度 */
        div[data-testid="stDialog"] div[role="dialog"] > div {
            height: 100%;
        }

        /* 针对长文本输入框/显示框的高度调整 */
        div[data-testid="stTextArea"] textarea {
            height: 60vh !important; /* 强制文本框变高 */
            min-height: 400px;
            font-family: monospace; /* 等宽字体更适合看提示词 */
        }
    </style>
""", unsafe_allow_html=True)
