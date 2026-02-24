# Cursor Browser Extension 设置指南

## 重要说明

**只使用 Cursor Browser Extension 的 browser 工具进行截图，不使用任何备选方案。**

## Browser 工具是什么？

`cursor-browser-extension` 是 Cursor IDE 的内置 MCP 服务器，提供以下浏览器工具：
- `browser_navigate` - 导航到 URL
- `browser_take_screenshot` - 截图
- `browser_wait_for` - 等待元素出现
- `browser_click` - 点击元素
- 等等

## 如何授权和使用

### 1. 检查 Browser 工具是否可用

Browser 工具是 Cursor IDE 内置的，通常已经可用。检查方法：

```bash
# 检查工具文件是否存在
ls -la ~/.cursor/projects/*/mcps/cursor-browser-extension/tools/
```

如果看到 `browser_take_screenshot.json` 等文件，说明工具已安装。

### 2. 在 Cursor 对话中授权

当 AI 首次使用 browser 工具时，Cursor 会弹出授权提示：
1. 点击 "Allow" 或 "授权"
2. 选择 "Always allow" 以避免每次都需要授权

### 3. 使用 Browser 工具截图

在 Cursor 对话中直接告诉 AI：

```
请使用 browser 工具截图以下 HTML 文件：
1. browser_navigate 到: file:///path/to/test.html
2. browser_wait_for 等待: .mermaid svg
3. browser_take_screenshot 保存为: test.png
```

## 使用脚本

### screenshot_with_cursor_browser.py

```bash
# 单个文件截图
python scripts/screenshot_with_cursor_browser.py test.html -o output.png

# 批量处理目录
python scripts/screenshot_with_cursor_browser.py test_html/ -o output_images/ --directory
```

脚本会生成指令，然后在 Cursor 对话中让 AI 执行。

## 故障排除

### 问题: Browser 工具不可用

**解决方案**:
1. 确认 Cursor IDE 已更新到最新版本
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
4. 在 Cursor 对话中明确要求使用 browser 工具

## 重要原则

- ✅ **只使用** Cursor Browser Extension 的 browser 工具
- ❌ **不使用** Puppeteer MCP
- ❌ **不使用** webshot-mcp
- ❌ **不使用** Playwright
- ❌ **不使用** wkhtmltoimage
- ❌ **不使用** 任何其他截图工具

如果 browser 工具不可用，请：
1. 检查 Cursor 设置
2. 更新 Cursor IDE
3. 联系 Cursor 支持

**绝不使用备选方案！**
