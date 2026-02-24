# MCP 截图功能 - 快速开始

## 5 分钟快速上手

### 步骤 1: 准备 HTML 文件

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

# 如果你已有 Markdown 文件，先生成 HTML
python scripts/mermaid_to_html.py your_doc.md -o html_output/

# 或使用测试文件
ls test_mcp_html/test_mermaid.html
```

### 步骤 2: 生成 MCP 任务清单

```bash
# 生成任务清单
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ -v

# 或保存到文件
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ --save-request task.md
```

### 步骤 3: 在 Cursor 中使用 MCP 工具

**复制以下内容，在 Cursor 对话中发送给 AI：**

```
请使用 Cursor MCP 浏览器工具，帮我截图以下 HTML 文件：

HTML 文件: file:///home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html
输出文件: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid.png

操作要求：
1. 使用 file:// 协议打开 HTML 文件
2. 等待页面完全加载
3. 等待 .mermaid svg 元素出现（确保 Mermaid 渲染完成）
4. 等待 2-3 秒让动画完成
5. 截取 .container 元素（包含标题和图表）
6. 保存为 PNG 文件到指定路径

请开始截图并告知结果。
```

### 步骤 4: 验证结果

```bash
# 验证截图是否成功
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ --verify -v
```

预期输出：
```
=== 验证截图结果 ===
✓ PNG 文件数量: 1 / 1
✅ 所有图片已生成！

=== 文件列表 ===
  ✓ test_mermaid.png (XX.X KB)
```

## 实际项目使用

### 完整工作流

```bash
# 1. Markdown → HTML
python scripts/mermaid_to_html.py document.md -o html/

# 2. 生成 MCP 任务
python scripts/html_to_image_mcp.py html/ -o images/ --save-request mcp_task.md

# 3. 查看任务清单
cat mcp_task.md

# 4. 在 Cursor 中使用 MCP 工具（复制 mcp_task.md 内容）

# 5. 验证
python scripts/html_to_image_mcp.py html/ -o images/ --verify

# 6. 替换 Markdown
python scripts/replace_mermaid_with_images.py document.md -i images/
```

## 常见问题

### Q1: MCP 工具在哪里？

**A**: MCP 工具是 Cursor IDE 内置的功能，在对话中可以使用。包括：
- `cursor-ide-browser`: Cursor IDE 内置浏览器
- `cursor-browser-extension`: Cursor 浏览器扩展

### Q2: 如果 MCP 工具不可用怎么办？

**A**: 使用备选方案：

**方案 A: Playwright（完全自动）**
```bash
pip install playwright
playwright install chromium
python scripts/mermaid_to_image.py html/ -o images/
```

**方案 B: wkhtmltoimage（本地渲染）**
```bash
sudo apt-get install wkhtmltopdf
python scripts/screenshot_html_mermaid.py test.html -o output.png
```

**方案 C: 手动截图**
```bash
# 在浏览器中打开 HTML 文件
xdg-open test.html
# 按 F12 → Ctrl+Shift+P → "Capture node screenshot"
```

### Q3: 批量处理多个文件？

**A**: 脚本自动支持批量处理：
```bash
# 自动处理目录中所有 HTML 文件
python scripts/html_to_image_mcp.py html_directory/ -o images/ -v
```

## 提示

1. **等待时间**: 复杂的 Mermaid 图表可能需要更长的等待时间（5-10秒）
2. **文件路径**: 确保使用绝对路径，避免路径错误
3. **验证**: 截图完成后一定要验证，确保所有文件都已生成

## 下一步

- 查看详细文档: [HTML_TO_IMAGE_MCP_USAGE.md](scripts/HTML_TO_IMAGE_MCP_USAGE.md)
- 测试说明: [TEST_MCP_SCREENSHOT.md](TEST_MCP_SCREENSHOT.md)
- 功能总结: [MCP_SCREENSHOT_READY.md](MCP_SCREENSHOT_READY.md)

---

**开始使用 MCP 截图功能！** 🚀
