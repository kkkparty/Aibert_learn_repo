#!/bin/bash
# 安装环境依赖（不包含截图工具）
# 注意：截图功能只使用 Cursor Browser Extension，无需安装其他工具
# 支持 Ubuntu/Debian 系统

set -e

echo "=========================================="
echo "  安装环境依赖"
echo "=========================================="
echo ""
echo "注意: 截图功能只使用 Cursor Browser Extension，无需安装其他工具"
echo ""

# 检测系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "无法检测系统类型"
    exit 1
fi

echo "检测到系统: $OS $VER"
echo ""

# 检查是否为 root 或 sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
    echo "需要 root 权限，将使用 sudo"
else
    SUDO=""
fi

# 注意：截图功能只使用 Cursor Browser Extension，无需安装其他工具
echo "[1/1] 检查 Cursor Browser Extension..."
if [ -d "$HOME/.cursor/projects" ] && find "$HOME/.cursor/projects" -name "cursor-browser-extension" -type d 2>/dev/null | grep -q .; then
    echo "  ✓ Cursor Browser Extension 已安装（Cursor IDE 内置）"
else
    echo "  ⚠️  Cursor Browser Extension 未找到"
    echo "  请确保："
    echo "  1. 已安装 Cursor IDE"
    echo "  2. Cursor IDE 已更新到最新版本"
    echo "  3. 重启 Cursor IDE"
fi

echo ""
echo "=========================================="
echo "  依赖安装完成"
echo "=========================================="
echo ""

# 验证 Browser Extension
echo "验证安装结果..."
echo ""

if [ -d "$HOME/.cursor/projects" ] && find "$HOME/.cursor/projects" -name "browser_take_screenshot.json" -type f 2>/dev/null | grep -q .; then
    echo "✓ Cursor Browser Extension: 可用"
    echo "  工具文件: $(find "$HOME/.cursor/projects" -name "browser_take_screenshot.json" -type f 2>/dev/null | head -1)"
else
    echo "⚠️  Cursor Browser Extension: 未找到"
    echo "  请确保 Cursor IDE 已安装并更新到最新版本"
fi

echo ""
echo "=========================================="
echo "  检查完成"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 在 Cursor 对话中使用 browser 工具截图"
echo "  2. 使用脚本: python scripts/screenshot_with_cursor_browser.py test.html -o output.png"
echo "  3. 查看文档: scripts/BROWSER_TOOL_SETUP.md"
