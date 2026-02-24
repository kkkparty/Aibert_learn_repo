# 如何使用 Cursor Browser Extension 截图

## 重要说明

`browser_navigate` 和 `browser_take_screenshot` 是 Cursor IDE 的内置工具，**需要在 Cursor 对话中由 AI 直接调用**，不能通过脚本自动执行。

## 使用方法

### 方法 1: 直接在 Cursor 对话中使用（推荐）

在 Cursor 对话中，直接告诉 AI：

```
请使用 browser 工具截图以下 HTML 文件：
1. 使用 browser_navigate 导航到: file:///path/to/test.html
2. 使用 browser_take_screenshot 截图，保存为: test.png
```

### 方法 2: 使用脚本生成指令，然后让 AI 执行

```bash
# 生成指令
python scripts/screenshot_with_cursor_browser.py test.html -o output.png

# 然后复制生成的指令，在 Cursor 对话中发送给 AI
```

## 为什么脚本不能自动执行？

1. **安全限制**: browser 工具需要用户授权才能执行
2. **交互式工具**: 这些工具需要在 Cursor 的对话环境中由 AI 调用
3. **权限控制**: Cursor 会要求用户确认浏览器操作

## 正确的使用流程

### 步骤 1: 运行脚本生成指令

```bash
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid.png
```

### 步骤 2: 在 Cursor 对话中执行

将脚本生成的指令复制到 Cursor 对话中，AI 会直接使用 browser 工具执行截图。

### 步骤 3: 授权确认

Cursor 可能会弹出授权提示，确认后 AI 会执行截图操作。

## 示例对话

**你**:
```
请使用 browser 工具截图以下 HTML 文件：
- HTML 文件: file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html
- 输出文件: test_mcp_images/test_mermaid.png
```

**AI**:
会直接使用 `browser_navigate` 和 `browser_take_screenshot` 工具执行截图。

## 故障排除

### 问题: AI 没有执行截图

**解决方案**:
1. 确认在 Cursor 对话中明确要求使用 browser 工具
2. 检查 Cursor 设置中是否启用了 Browser Extension
3. 确认已授权浏览器操作

### 问题: 找不到 browser 工具

**解决方案**:
1. 重启 Cursor IDE
2. 检查 `~/.cursor/projects/*/mcps/cursor-browser-extension/` 目录是否存在
3. 更新 Cursor 到最新版本

## 总结

- ✅ browser 工具是 Cursor 内置的，无需安装
- ✅ 需要在 Cursor 对话中由 AI 直接调用
- ❌ 不能通过脚本自动执行（安全限制）
- ✅ 使用脚本生成指令，然后在对话中让 AI 执行
