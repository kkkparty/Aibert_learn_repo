# HTML 截图测试指南

## 当前可用的脚本

**唯一脚本**: `screenshot_with_cursor_browser.py`

**功能**: 使用 Cursor Browser Extension 的 browser 工具截图 HTML 文件

## 快速测试

### 1. 单个文件截图测试

```bash
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

# 测试截图
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid.png \
  -v
```

### 2. 批量目录截图测试

```bash
# 批量处理目录中的所有 HTML 文件
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/ \
  -o test_mcp_images/ \
  --directory \
  -v
```

### 3. 全页面截图测试

```bash
# 全页面截图
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid_full.png \
  --full-page \
  -v
```

### 4. 截取特定元素

```bash
# 只截取 .container 元素
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid_container.png \
  --selector ".container" \
  -v
```

## 脚本参数说明

```bash
python scripts/screenshot_with_cursor_browser.py [选项]

必需参数:
  html                   HTML 文件路径或目录

  -o, --output OUTPUT   输出 PNG 文件路径或目录（必需）

可选参数:
  -v, --verbose         详细输出
  -f, --full-page       全页面截图（默认: false）
  -s, --selector SELECTOR  CSS 选择器（用于截取特定元素）
  -d, --directory       批量处理目录
```

## 测试流程

### 步骤 1: 准备测试 HTML 文件

```bash
# 确保测试 HTML 文件存在
ls -lh test_mcp_html/test_mermaid.html
```

### 步骤 2: 运行截图脚本

```bash
# 运行脚本生成指令
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid.png \
  -v
```

### 步骤 3: 在 Cursor 对话中执行

脚本会生成指令，然后：

1. **复制脚本输出的指令**
2. **在 Cursor 对话中发送给 AI**
3. **AI 会直接使用 browser 工具执行截图**

### 步骤 4: 验证结果

```bash
# 检查截图文件是否生成
ls -lh test_mcp_images/*.png

# 验证文件类型
file test_mcp_images/test_mermaid.png
```

## 完整测试示例

```bash
# 1. 进入项目目录
cd /home/aibert.liu/libra/code/ai_infra/skills/source_code_learn_skill

# 2. 确保输出目录存在
mkdir -p test_mcp_images

# 3. 运行截图脚本
python scripts/screenshot_with_cursor_browser.py \
  test_mcp_html/test_mermaid.html \
  -o test_mcp_images/test_mermaid.png \
  -v

# 4. 脚本会输出指令，在 Cursor 对话中让 AI 执行

# 5. 验证结果
if [ -f test_mcp_images/test_mermaid.png ]; then
    echo "✅ 截图成功生成"
    ls -lh test_mcp_images/test_mermaid.png
else
    echo "❌ 截图未生成，请检查 Cursor 对话中的执行结果"
fi
```

## 注意事项

1. **Browser 工具需要在 Cursor 对话中调用**
   - 脚本只生成指令，不直接执行截图
   - 需要在 Cursor 对话中让 AI 执行

2. **首次使用需要授权**
   - Cursor 会弹出授权提示
   - 点击 "Allow" 并选择 "Always allow"

3. **文件路径**
   - HTML 文件路径使用绝对路径（file:// 协议）
   - 输出文件路径可以是相对路径或绝对路径

4. **等待渲染**
   - 对于 Mermaid 图表，需要等待渲染完成
   - 脚本会自动添加等待步骤

## 故障排除

### 问题: 脚本运行但没有生成截图

**原因**: 脚本只生成指令，需要在 Cursor 对话中执行

**解决**: 将脚本输出的指令复制到 Cursor 对话中，让 AI 执行

### 问题: AI 无法使用 browser 工具

**检查**:
```bash
# 检查工具文件是否存在
ls -la ~/.cursor/projects/*/mcps/cursor-browser-extension/tools/browser_take_screenshot.json
```

**解决**:
1. 重启 Cursor IDE
2. 更新 Cursor 到最新版本
3. 检查 Cursor 设置中的 MCP 配置

### 问题: 授权被拒绝

**解决**:
1. 在 Cursor 设置中检查 MCP 权限
2. 重新授权 browser 工具
3. 选择 "Always allow" 避免每次授权

## 相关文档

- `BROWSER_TOOL_SETUP.md` - 详细设置指南
- `CURSOR_BROWSER_EXTENSION.md` - 工具说明
- `HOW_TO_USE_BROWSER_SCREENSHOT.md` - 使用指南
