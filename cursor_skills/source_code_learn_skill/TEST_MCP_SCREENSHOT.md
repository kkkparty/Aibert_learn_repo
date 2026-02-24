# MCP 截图功能测试说明

## 测试目的

验证使用 Cursor MCP 浏览器工具截图 HTML 文件的功能是否正常工作。

## 测试文件

- **测试 HTML**: `test_mcp_html/test_mermaid.html`
- **输出目录**: `test_mcp_images/`
- **预期输出**: `test_mcp_images/test_mermaid.png`

## 快速测试

### 方法 1: 使用测试脚本（推荐）

```bash
# 运行测试脚本
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill
./scripts/test_mcp_screenshot.sh
```

脚本会：
1. 检查测试文件
2. 生成 MCP 任务清单
3. 显示任务清单内容
4. 提示你使用 MCP 工具截图
5. 验证截图结果

### 方法 2: 手动测试

**步骤 1: 生成 MCP 任务**

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

python3 scripts/html_to_image_mcp.py \
    test_mcp_html/ \
    -o test_mcp_images/ \
    --save-request mcp_task.md -v
```

**步骤 2: 使用 MCP 工具截图**

在 Cursor 中新建对话或在当前对话中，发送以下内容：

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
6. 保存为 PNG 文件

请开始截图。
```

**步骤 3: 验证结果**

```bash
python3 scripts/html_to_image_mcp.py \
    test_mcp_html/ \
    -o test_mcp_images/ \
    --verify -v
```

## 预期结果

成功完成后，应该看到：

```
=== 验证截图结果 ===
✓ PNG 文件数量: 1 / 1
✅ 所有图片已生成！

=== 文件列表 ===
  ✓ test_mermaid.png (XX.X KB)
```

## 故障排除

### 问题 1: MCP 工具不可用

**症状**: AI 提示"MCP 工具不可用"或"无法访问 MCP 服务器"

**解决方案**:
1. 确保在 Cursor IDE 中运行
2. 检查 Cursor 版本是否支持 MCP
3. 尝试重启 Cursor
4. 使用备选方案（Playwright 或手动截图）

### 问题 2: HTML 文件无法打开

**症状**: 浏览器无法打开 HTML 文件

**解决方案**:
1. 检查文件路径是否正确
2. 确认使用 `file://` 协议
3. 在系统浏览器中手动打开验证

### 问题 3: Mermaid 未渲染

**症状**: 截图中 Mermaid 图表未显示

**解决方案**:
1. 增加等待时间（从 2秒 改为 5秒）
2. 检查网络连接（Mermaid CDN）
3. 在浏览器中打开 HTML 手动验证

### 问题 4: 截图质量不佳

**症状**: 截图模糊或不清晰

**解决方案**:
1. 增加视口尺寸（默认 1200x800）
2. 使用更高的 DPI
3. 考虑使用 Playwright 替代

## 备选方案

如果 MCP 工具无法使用，可以使用以下备选方案：

### 方案 A: Playwright（推荐）

```bash
# 安装 Playwright
pip install playwright
playwright install chromium

# 使用 Playwright 截图
python3 scripts/mermaid_to_image.py test_mcp_html/ -o test_mcp_images/
```

### 方案 B: wkhtmltoimage

```bash
# 安装 wkhtmltoimage
sudo apt-get install wkhtmltopdf

# 使用 wkhtmltoimage 截图
python3 scripts/screenshot_html_mermaid.py \
    test_mcp_html/test_mermaid.html \
    -o test_mcp_images/test_mermaid.png
```

### 方案 C: 手动截图

```bash
# 在浏览器中打开 HTML 文件
xdg-open test_mcp_html/test_mermaid.html

# 然后：
# 1. 按 F12 打开开发者工具
# 2. 按 Ctrl+Shift+P 打开命令面板
# 3. 输入 "Capture node screenshot"
# 4. 点击 .container 元素
# 5. 保存到 test_mcp_images/test_mermaid.png
```

## 测试完成后

验证截图成功后，可以继续测试批量处理：

```bash
# 创建更多测试 HTML 文件
# 然后批量截图
python3 scripts/html_to_image_mcp.py test_mcp_html/ -o test_mcp_images/ -v
```

## 相关文档

- [HTML_TO_IMAGE_MCP_USAGE.md](scripts/HTML_TO_IMAGE_MCP_USAGE.md) - 详细使用指南
- [MCP浏览器截图完整指南.md](MCP浏览器截图完整指南.md) - MCP 工具说明
