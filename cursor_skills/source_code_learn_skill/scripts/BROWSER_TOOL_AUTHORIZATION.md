# Browser 工具授权和使用指南

## 授权 Browser 工具

### 在 Cursor 中授权 Browser 工具

1. **打开 Cursor 设置**
   - 点击 Cursor 菜单 > Settings
   - 或使用快捷键 `Ctrl+,` (Windows/Linux) 或 `Cmd+,` (Mac)

2. **找到 MCP 设置**
   - 在设置中搜索 "MCP" 或 "Model Context Protocol"
   - 确认 `cursor-browser-extension` 已启用

3. **授权浏览器操作**
   - 当 AI 首次使用 browser 工具时，Cursor 会弹出授权提示
   - 点击 "Allow" 或 "授权" 按钮
   - 选择 "Always allow" 以避免每次都需要授权

## 直接使用 Browser 工具截图

### 在 Cursor 对话中使用

直接在 Cursor 对话中告诉 AI：

```
请使用 browser 工具截图以下 HTML 文件：
1. 使用 browser_navigate 导航到: file:///path/to/test.html
2. 使用 browser_take_screenshot 截图，保存为: test.png
```

### 完整示例

```
请使用 browser 工具执行以下操作：

1. browser_navigate 到:
   file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html

2. 等待页面加载完成（等待 Mermaid 图表渲染）

3. browser_take_screenshot 截图:
   - filename: test_mermaid.png
   - type: png
   - fullPage: false

4. 将截图移动到目标目录:
   /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid.png
```

## 工具参数说明

### browser_navigate
- `url`: 要导航的 URL（支持 file:// 协议）

### browser_take_screenshot
- `filename`: 文件名（如 `test.png`）
- `type`: 图片格式（`png` 或 `jpeg`，默认 `png`）
- `fullPage`: 是否全页面截图（`true`/`false`）
- `ref`: CSS 选择器（用于截取特定元素）

## 故障排除

### 问题: 工具不可用

**解决方案**:
1. 确认 Cursor 已更新到最新版本
2. 重启 Cursor IDE
3. 检查 `~/.cursor/projects/*/mcps/cursor-browser-extension/` 目录是否存在

### 问题: 授权被拒绝

**解决方案**:
1. 在 Cursor 设置中检查 MCP 权限
2. 重新授权 browser 工具
3. 检查是否有其他安全设置阻止了浏览器操作

### 问题: 截图失败

**解决方案**:
1. 确认 HTML 文件路径正确（使用绝对路径）
2. 检查文件是否存在
3. 确认有写入权限

## 总结

- ✅ Browser 工具是 Cursor 内置的，无需安装
- ✅ 需要在 Cursor 对话中授权才能使用
- ✅ 直接在对话中告诉 AI 使用 browser 工具即可
- ✅ AI 会自动处理导航、等待和截图操作
