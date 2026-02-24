# 快速测试指南 - 截图功能

## 最快测试方式（10秒内完成）

### 方式 1: 使用 wkhtmltoimage（立即可用，推荐）

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

# 直接截图，10秒内完成
python scripts/screenshot_html_mermaid.py \
    test_mcp_html/test_mermaid.html \
    -o test_mcp_images/test_mermaid.png \
    --wait 10

# 验证结果
ls -lh test_mcp_images/test_mermaid.png
```

**优点**：
- ✅ 已安装，立即可用
- ✅ 10秒内完成
- ✅ 无需配置
- ✅ 截图质量好

### 方式 2: 使用 webshot-mcp（需要配置）

```bash
# 1. 确保 webshot-mcp 已配置（只需一次）
bash scripts/install_webshot_mcp.sh

# 2. 重启 Cursor IDE

# 3. 运行测试（AI 会自动使用 webshot-mcp）
python scripts/auto_mcp_screenshot.py \
    test_mcp_html/ \
    -o test_mcp_images/ \
    --max-wait 10
```

## 测试流程说明

### 当前截图处理方式

1. **wkhtmltoimage**（当前使用）
   - 工具：`scripts/screenshot_html_mermaid.py`
   - 时间：10秒
   - 状态：✅ 已安装，可用

2. **webshot-mcp**（MCP 工具）
   - 工具：`scripts/auto_mcp_screenshot.py`
   - 时间：10-30秒（取决于 MCP 响应）
   - 状态：需要配置

3. **Playwright**（备选）
   - 工具：`scripts/auto_screenshot_mcp.py`
   - 时间：5-10秒
   - 状态：浏览器未安装

### 推荐测试命令

**最快测试**（推荐）：
```bash
python scripts/screenshot_html_mermaid.py \
    test_mcp_html/test_mermaid.html \
    -o test_mcp_images/test_mermaid.png \
    --wait 10
```

**使用 webshot-mcp**（如果已配置）：
```bash
python scripts/auto_mcp_screenshot.py \
    test_mcp_html/ \
    -o test_mcp_images/ \
    --max-wait 10
```

## 验证截图

```bash
# 验证截图文件
python scripts/html_to_image_mcp.py \
    test_mcp_html/ \
    -o test_mcp_images/ \
    --verify -v

# 查看文件
ls -lh test_mcp_images/*.png
```

## 总结

**当前可用的截图方式**：
1. ✅ **wkhtmltoimage** - 立即可用，10秒完成（推荐测试）
2. ⚠️ **webshot-mcp** - 需要配置，AI 自动调用
3. ⚠️ **Playwright** - 浏览器未安装

**测试建议**：
- 快速测试：使用 `screenshot_html_mermaid.py`（wkhtmltoimage）
- MCP 测试：配置 webshot-mcp 后使用 `auto_mcp_screenshot.py`
