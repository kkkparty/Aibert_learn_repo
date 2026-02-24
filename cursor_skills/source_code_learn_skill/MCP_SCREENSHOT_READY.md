# MCP 截图功能已就绪 ✅

## 功能状态

✅ **已完成**：
- `html_to_image_mcp.py` - MCP 任务生成脚本
- `html_to_image_mcp_direct.py` - 直接调用版本
- 测试 HTML 文件和目录结构
- 完整的使用文档和指南
- 测试脚本和验证工具

⏳ **待测试**：
- 实际使用 Cursor MCP 浏览器工具截图

## 快速使用

### 完整工作流

```bash
# 1. 生成 HTML 文件（从 Markdown 的 Mermaid 代码）
python scripts/mermaid_to_html.py your_document.md -o html_output/

# 2. 生成 MCP 任务清单
python scripts/html_to_image_mcp.py html_output/ -o images/ -v

# 3. 使用 MCP 工具截图（在 Cursor 中）
#    复制上面生成的任务清单，发送给 AI

# 4. 验证结果
python scripts/html_to_image_mcp.py html_output/ -o images/ --verify

# 5. 替换 Markdown 中的 Mermaid 为图片
python scripts/replace_mermaid_with_images.py your_document.md -i images/
```

## 测试用例

### 测试文件已准备好

- **HTML 文件**: `test_mcp_html/test_mermaid.html`
- **输出目录**: `test_mcp_images/`
- **MCP 任务**: `mcp_task.md`

### 运行测试

**方法 1: 使用测试脚本**

```bash
./scripts/test_mcp_screenshot.sh
```

**方法 2: 手动测试**

```bash
# 生成任务清单
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ -v

# 复制任务清单内容，在 Cursor 对话中发送给 AI

# 验证结果
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ --verify
```

## 在 Cursor 中使用 MCP 工具

### 示例请求（复制到 Cursor 对话）

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

## 文件结构

```
skills/source_code_learn_skill/
├── scripts/
│   ├── html_to_image_mcp.py          # MCP 任务生成（主脚本）
│   ├── html_to_image_mcp_direct.py   # 直接调用版本
│   ├── test_mcp_screenshot.sh        # 测试脚本
│   └── HTML_TO_IMAGE_MCP_USAGE.md    # 使用指南
├── test_mcp_html/
│   └── test_mermaid.html             # 测试 HTML 文件
├── test_mcp_images/                   # 输出目录
├── mcp_task.md                        # 生成的 MCP 任务清单
├── MCP_SCREENSHOT_READY.md           # 本文档
└── TEST_MCP_SCREENSHOT.md            # 测试说明
```

## 功能特点

### 1. 自动化任务生成

- 扫描 HTML 文件目录
- 生成格式化的 MCP 任务清单
- 支持批量处理

### 2. 灵活的输出选项

- 终端输出（默认）
- 保存到文件（`--save-request`）
- 生成 Python 脚本（`--generate-script`）

### 3. 结果验证

- 检查截图文件数量
- 显示文件列表和大小
- 提示缺失的文件

### 4. 多方案支持

- **方案 A**: Cursor MCP 浏览器（高质量）
- **方案 B**: Playwright（完全自动）
- **方案 C**: wkhtmltoimage（本地渲染）
- **方案 D**: 手动截图（最可靠）

## 与现有工具的集成

### 集成到 mermaid_full_pipeline.py

```python
# 可以选择使用 MCP 工具替代 Playwright
# 修改 html_to_image() 函数以支持 MCP 选项

def html_to_image(html_path, output_path, use_mcp=False):
    if use_mcp:
        # 生成 MCP 任务并提示用户
        generate_mcp_task_and_wait()
    else:
        # 使用 Playwright 或 wkhtmltoimage
        screenshot_with_playwright()
```

### 完整流水线示例

```bash
#!/bin/bash
# 完整的 Mermaid → 图片 → Markdown 流水线

DOC="document.md"
HTML_DIR="html_output"
IMG_DIR="images"

# 步骤 1: Mermaid → HTML
python scripts/mermaid_to_html.py "$DOC" -o "$HTML_DIR/"

# 步骤 2: 生成 MCP 任务
python scripts/html_to_image_mcp.py "$HTML_DIR/" -o "$IMG_DIR/" --save-request mcp_task.md

# 步骤 3: 提示用户使用 MCP 工具
echo "请在 Cursor 中使用 MCP 工具截图（见 mcp_task.md）"
echo "完成后按 Enter 继续..."
read

# 步骤 4: 验证
python scripts/html_to_image_mcp.py "$HTML_DIR/" -o "$IMG_DIR/" --verify

# 步骤 5: 替换 Markdown
python scripts/replace_mermaid_with_images.py "$DOC" -i "$IMG_DIR/"

echo "完成！"
```

## 下一步

### 立即测试

在 Cursor 对话中复制以下内容并发送：

```
请使用 Cursor MCP 浏览器工具，帮我截图测试 HTML 文件：

源文件: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_html/test_mermaid.html
输出: /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill/test_mcp_images/test_mermaid.png

请使用 file:// 协议打开，等待 Mermaid 渲染完成后截取 .container 元素，保存为 PNG。
```

### 验证结果

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill
python scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ --verify -v
```

### 实际应用

测试成功后，可以用于实际项目：

```bash
# DDP 文档示例
python scripts/mermaid_to_html.py /path/to/DDP文档.md -o mermaid_html/
python scripts/html_to_image_mcp.py mermaid_html/ -o mermaid_images/ -v
# 在 Cursor 中使用 MCP 工具截图
python scripts/html_to_image_mcp.py mermaid_html/ -o mermaid_images/ --verify
```

## 相关文档

- [HTML_TO_IMAGE_MCP_USAGE.md](scripts/HTML_TO_IMAGE_MCP_USAGE.md) - 详细使用指南
- [TEST_MCP_SCREENSHOT.md](TEST_MCP_SCREENSHOT.md) - 测试说明
- [MCP浏览器截图完整指南.md](MCP浏览器截图完整指南.md) - MCP 工具详细说明
- [MERMAID_VISUALIZATION_GUIDE.md](MERMAID_VISUALIZATION_GUIDE.md) - Mermaid 可视化指南
- [README.md](README.md) - 主文档

---

**功能已就绪，可以开始使用！** 🚀
