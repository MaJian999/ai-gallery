/* 1. 模态框整体容器 */
.modal-content {
  height: 90vh; /* 占据屏幕高度的 90% */
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 防止外层滚动 */
}

/* 2. 模态框的主体内容区域 (包含文本框的部分) */
.modal-body {
  flex: 1; /* 自动撑开，占据剩余高度 */
  overflow-y: auto; /* 内部内容过多时滚动 */
  padding: 0; /* 根据需要调整 */
  display: flex; /* 让内部的 textarea 也能撑开 */
  flex-direction: column;
}

/* 3. 提示词文本框或展示框 */
.prompt-textarea, 
.prompt-display-box {
  width: 100%;
  flex: 1; /* 关键：撑满 modal-body 的高度 */
  height: 100%; /* 确保高度生效 */
  resize: none; /* 禁止用户手动拖拽，因为我们已经设为全屏了 */
  border: 1px solid #ddd;
  padding: 1rem;
  font-family: monospace;
}
