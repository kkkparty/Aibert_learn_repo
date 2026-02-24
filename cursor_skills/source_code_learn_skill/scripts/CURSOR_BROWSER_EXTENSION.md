# Cursor Browser Extension 使用指南

## 重要说明

**`cursor-browser-extension` 不是通过 pip 安装的 Python 包！**

它是 Cursor IDE 的内置 MCP 服务器，已经自动集成在 Cursor 中，无需单独安装。

## 检查是否可用

### 方法 1: 检查文件系统

```bash
# 检查工具文件是否存在
ls -la ~/.cursor/projects/*/mcps/cursor-browser-extension/tools/
```

如果看到类似以下文件，说明已安装：
- `browser_snapshot.json`
- `browser_navigate.json`
- `browser_click.json`
- 等等

### 方法 2: 在 Cursor 中检查

在 Cursor 对话中询问：
```
请列出可用的浏览器相关 MCP 工具
```

应该能看到 `browser_*` 开头的工具。

## 可用的浏览器工具

根据 Cursor Browser Extension 的配置，主要工具包括：

### 1. browser_take_screenshot ⭐（截图工具）
**这是你需要的截图工具！** 用于捕获页面截图。

### 2. browser_snapshot
捕获页面的可访问性快照，用于获取元素引用（不是截图）

### 3. browser_navigate
导航到指定 URL

### 4. browser_click
点击页面元素

### 5. browser_type
在输入框中输入文本

### 6. browser_fill_form
填写表单

### 7. browser_hover
悬停在元素上

### 8. browser_wait_for
等待元素出现

### 9. browser_resize
调整浏览器窗口大小

### 10. browser_handle_dialog
处理对话框（确认/取消）

### 11. browser_press_key
按下键盘按键

## 使用示例

### 截图本地 HTML 文件

```python
# 在 Cursor 对话中
请使用 browser 工具截图本地 HTML 文件：
1. 使用 browser_navigate 导航到: file:///home/user/test.html
2. 等待页面加载完成（可以使用 browser_wait_for）
3. 使用 browser_take_screenshot 截图
4. 保存截图到指定路径
```

### 具体使用步骤

```python
# 步骤 1: 导航到 HTML 文件
请使用 browser_navigate 工具，导航到：
- url: file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html

# 步骤 2: 等待页面加载（可选）
请使用 browser_wait_for 工具，等待元素出现：
- selector: .mermaid svg
- timeout: 10000

# 步骤 3: 截图
请使用 browser_take_screenshot 工具截图，并保存到：
- outputPath: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid.png
```

## 注意事项

1. **✅ 有截图工具**: `browser_take_screenshot` 可以直接截图
2. **已内置**: Cursor Browser Extension 是 Cursor IDE 的内置功能，无需安装
3. **无需 pip 安装**: `cursor-browser-extension` 不是 Python 包，不能通过 pip 安装
4. **推荐使用**: 对于本地 HTML 截图，这是最简单的方式（无需额外配置）

## 故障排除

### 问题: 找不到 browser 工具

**解决方案**:
1. 确认 Cursor IDE 已更新到最新版本
2. 重启 Cursor IDE
3. 检查 `~/.cursor/projects/*/mcps/cursor-browser-extension/` 目录是否存在

### 问题: 工具不可用

**解决方案**:
1. 检查 Cursor 设置中的 MCP 配置
2. 确认 Browser Extension 已启用
3. 查看 Cursor 日志（Help > Show Logs）

## 与其他工具对比

| 特性 | cursor-browser-extension | Puppeteer MCP | Playwright MCP |
|------|-------------------------|---------------|----------------|
| 安装方式 | Cursor 内置（无需安装） | npx 安装 | npx 安装 |
| 主要用途 | 浏览器交互和截图 | 截图和自动化 | 截图和自动化 |
| 截图功能 | ✅ (browser_take_screenshot) | ✅ | ✅ |
| 交互功能 | ✅ | ✅ | ✅ |
| 推荐场景 | **本地 HTML 截图（推荐）** | 需要更多控制时 | 需要更多控制时 |

## 总结

- ✅ `cursor-browser-extension` 已内置在 Cursor 中，无需安装
- ❌ 它不提供直接的截图功能
- ✅ 如果需要截图，使用 Puppeteer MCP 或 Playwright MCP
- ✅ 如果只需要浏览器交互，可以使用 cursor-browser-extension
