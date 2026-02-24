#!/bin/bash
# MCP 截图测试脚本
# 测试 HTML to Image MCP 功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo " MCP 截图功能测试"
echo "=========================================="
echo ""

# 步骤 1: 确认测试文件存在
echo "[1/5] 检查测试文件..."
HTML_FILE="$PROJECT_ROOT/test_mcp_html/test_mermaid.html"
OUTPUT_DIR="$PROJECT_ROOT/test_mcp_images"

if [ ! -f "$HTML_FILE" ]; then
    echo "✗ 测试 HTML 文件不存在: $HTML_FILE"
    exit 1
fi

echo "✓ 测试 HTML 文件: $HTML_FILE"
echo "✓ 输出目录: $OUTPUT_DIR"
echo ""

# 步骤 2: 生成 MCP 任务清单
echo "[2/5] 生成 MCP 任务清单..."
python3 "$SCRIPT_DIR/html_to_image_mcp.py" \
    "$PROJECT_ROOT/test_mcp_html" \
    -o "$OUTPUT_DIR" \
    --save-request "$PROJECT_ROOT/mcp_task.md"

echo "✓ MCP 任务清单已保存: $PROJECT_ROOT/mcp_task.md"
echo ""

# 步骤 3: 显示任务清单
echo "[3/5] MCP 任务清单内容:"
echo "=========================================="
cat "$PROJECT_ROOT/mcp_task.md"
echo "=========================================="
echo ""

# 步骤 4: 提示用户使用 MCP 工具
echo "[4/5] 使用 MCP 工具截图"
echo ""
echo "请在 Cursor 中执行以下操作："
echo ""
echo "方法 1: 在当前对话中"
echo "  复制 mcp_task.md 的内容"
echo "  发送给 AI: '请使用 Cursor MCP 浏览器工具，按照任务清单截图'"
echo ""
echo "方法 2: 新建对话"
echo "  在 Cursor 中新建对话"
echo "  粘贴 mcp_task.md 的内容并发送"
echo ""
echo "HTML 文件 URL: file://$HTML_FILE"
echo "输出文件: $OUTPUT_DIR/test_mermaid.png"
echo ""

# 步骤 5: 等待用户确认
read -p "完成截图后按 Enter 键验证结果..."
echo ""

echo "[5/5] 验证截图结果..."
python3 "$SCRIPT_DIR/html_to_image_mcp.py" \
    "$PROJECT_ROOT/test_mcp_html" \
    -o "$OUTPUT_DIR" \
    --verify -v

echo ""
echo "=========================================="
echo " 测试完成"
echo "=========================================="

# 检查截图是否存在
if [ -f "$OUTPUT_DIR/test_mermaid.png" ]; then
    SIZE=$(du -h "$OUTPUT_DIR/test_mermaid.png" | cut -f1)
    echo "✓ 截图成功: test_mermaid.png ($SIZE)"
    echo ""
    echo "下一步:"
    echo "  查看图片: xdg-open $OUTPUT_DIR/test_mermaid.png"
else
    echo "⚠️  截图文件不存在"
    echo ""
    echo "故障排除:"
    echo "  1. 检查 MCP 工具是否可用"
    echo "  2. 确认 HTML 文件在浏览器中可以正常打开"
    echo "  3. 尝试手动截图: 浏览器打开 HTML → F12 → 截图"
fi
