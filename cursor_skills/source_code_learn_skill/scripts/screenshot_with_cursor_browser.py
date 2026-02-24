#!/usr/bin/env python3
"""
使用 Cursor Browser Extension 的 browser_take_screenshot 工具截图 HTML 文件

注意: cursor-browser-extension 是 Cursor IDE 的内置功能，无需安装！

此脚本会生成指令，AI 会在 Cursor 对话中直接使用 browser 工具执行截图。
"""

import sys
import argparse
from pathlib import Path
import json

def generate_cursor_browser_instruction(html_path: Path, output_path: Path,
                                        full_page: bool = False,
                                        element_selector: str = None,
                                        verbose: bool = False):
    """
    生成 Cursor Browser Extension 截图指令

    Args:
        html_path: HTML 文件路径
        output_path: 输出 PNG 文件路径
        full_page: 是否全页面截图
        element_selector: CSS 选择器（可选，用于截取特定元素）
        verbose: 是否详细输出
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换为 file:// URL
    html_url = f"file://{html_path.absolute()}"

    if verbose:
        print("=" * 70)
        print("  Cursor Browser Extension 截图指令")
        print("=" * 70)
        print()

    print("=" * 70)
    print("  使用 Cursor Browser Extension 截图")
    print("=" * 70)
    print()
    print("AI 将直接使用 browser 工具执行以下操作：\n")
    print(f"**HTML 文件**: `{html_url}`")
    print(f"**输出文件**: `{output_path}`\n")
    print("=" * 70)
    print("  开始执行截图...")
    print("=" * 70)
    print()

    # 生成 JSON 格式的指令，供 AI 直接使用
    instructions = {
        "step1": {
            "tool": "browser_navigate",
            "params": {
                "url": html_url
            }
        }
    }

    if element_selector:
        instructions["step2"] = {
            "tool": "browser_wait_for",
            "params": {
                "selector": element_selector,
                "timeout": 10000
            }
        }

    screenshot_params = {
        "filename": output_path.name,
        "type": "png"
    }
    if full_page:
        screenshot_params["fullPage"] = True
    if element_selector:
        screenshot_params["ref"] = element_selector

    instructions["step_screenshot"] = {
        "tool": "browser_take_screenshot",
        "params": screenshot_params
    }

    if verbose:
        print("执行指令（JSON 格式）：")
        print(json.dumps(instructions, indent=2, ensure_ascii=False))
        print()

    print("请 AI 直接执行以下操作：\n")
    print("1. 使用 browser_navigate 导航到:", html_url)
    if element_selector:
        print("2. 使用 browser_wait_for 等待元素:", element_selector)
    print("3. 使用 browser_take_screenshot 截图，参数:")
    print("   - filename:", output_path.name)
    print("   - type: png")
    if full_page:
        print("   - fullPage: true")
    if element_selector:
        print("   - ref:", element_selector)
    print()

    return {
        "url": html_url,
        "output": str(output_path),
        "fullPage": full_page,
        "selector": element_selector
    }

def main():
    parser = argparse.ArgumentParser(
        description='使用 Cursor Browser Extension 截图 HTML 文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个文件截图
  python scripts/screenshot_with_cursor_browser.py test.html -o output.png

  # 全页面截图
  python scripts/screenshot_with_cursor_browser.py test.html -o output.png --full-page

  # 截取特定元素
  python scripts/screenshot_with_cursor_browser.py test.html -o output.png --selector ".container"

  # 批量处理目录
  python scripts/screenshot_with_cursor_browser.py test_html/ -o output_images/ --directory
        """
    )
    parser.add_argument('html', help='HTML 文件路径或目录')
    parser.add_argument('-o', '--output', required=True, help='输出 PNG 文件路径或目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-f', '--full-page', action='store_true',
                       help='全页面截图（默认: false）')
    parser.add_argument('-s', '--selector', type=str,
                       help='CSS 选择器（用于截取特定元素）')
    parser.add_argument('-d', '--directory', action='store_true',
                       help='批量处理目录')

    args = parser.parse_args()

    if args.directory:
        input_path = Path(args.html)
        output_dir = Path(args.output)

        if not input_path.is_dir():
            print(f"错误: {input_path} 不是目录")
            sys.exit(1)

        html_files = sorted(list(input_path.glob('*.html')))
        if not html_files:
            print(f"错误: 在 {input_path} 中未找到 HTML 文件")
            sys.exit(1)

        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 70)
        print("  使用 Cursor Browser Extension 批量截图")
        print("=" * 70)
        print(f"\n找到 {len(html_files)} 个 HTML 文件\n")

        for idx, html_file in enumerate(html_files, 1):
            output_name = html_file.stem + '.png'
            output_path = output_dir / output_name

            print(f"\n文件 {idx}/{len(html_files)}: {html_file.name}")
            print("-" * 70)
            generate_cursor_browser_instruction(
                html_file, output_path,
                args.full_page, args.selector, args.verbose
            )

        print("\n" + "=" * 70)
        print("  批量截图指令生成完成")
        print("=" * 70)
        print("\n请在 Cursor 对话中使用上述指令，让 AI 使用 browser 工具完成截图。")
    else:
        html_path = Path(args.html)
        output_path = Path(args.output)

        if not html_path.exists():
            print(f"错误: HTML 文件不存在: {html_path}")
            sys.exit(1)

        generate_cursor_browser_instruction(
            html_path, output_path,
            args.full_page, args.selector, args.verbose
        )

if __name__ == '__main__':
    main()
