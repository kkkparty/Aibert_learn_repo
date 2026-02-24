# 使用 Cursor MCP 浏览器批量截图 HTML 文件

请使用 cursor-ide-browser 或 cursor-browser-extension MCP 工具，
帮我批量截图以下 HTML 文件。

## 任务详情

**源目录**：`test_mcp_html`

**输出目录**：`test_mcp_images`


## 操作步骤（每个文件）

1. 打开 HTML 文件（使用 `file://` 协议）

2. 等待页面完全加载

3. 等待 `.mermaid svg` 元素出现（确保 Mermaid 渲染完成）

4. 等待 2-3 秒让动画完成

5. 使用 MCP 浏览器工具截图：

   - 截取 `.container` 元素（如果存在）

   - 或截取整个页面

6. 保存截图为对应的 PNG 文件


## 需要截图的文件

### 文件 1/1: test_mermaid.html

- **HTML**: `test_mcp_html/test_mermaid.html`

- **PNG**: `test_mcp_images/test_mermaid.png`



## 截图要求

- 等待 Mermaid 完全渲染（svg 元素出现且有内容）

- 截取 `.container` 元素（包含标题和图表）

- 图片格式：PNG

- 视口大小：1200x800 或更大

- 背景：白色


## 预期结果

完成后应该有 1 个 PNG 文件在：

`test_mcp_images`


请逐个处理并告知进度。完成后告知结果！
