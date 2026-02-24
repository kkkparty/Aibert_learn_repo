#!/usr/bin/env python3
"""
Mermaid to HTML 转换工具
功能：
1. 从 Markdown 中提取 Mermaid 代码块
2. 生成独立的 HTML 文件（用于截图）
3. 支持批量处理
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# HTML 模板
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .description {{
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {description}
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#74c0fc',
                primaryTextColor: '#000',
                primaryBorderColor: '#339af0',
                lineColor: '#868e96',
                secondaryColor: '#a9e34b',
                tertiaryColor: '#ffd43b'
            }}
        }});
    </script>
</body>
</html>
"""


def extract_mermaid_blocks(content: str) -> List[Tuple[str, str, int]]:
    """
    从 Markdown 中提取 Mermaid 代码块

    Returns:
        List of (title, mermaid_code, line_number)
    """
    blocks = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测 mermaid 代码块开始
        if line.strip().startswith('```mermaid'):
            # 向上查找标题（最近的 ## 或 ###）
            title = "Mermaid Diagram"
            for j in range(i - 1, max(0, i - 10), -1):
                if lines[j].strip().startswith('#'):
                    title = lines[j].strip().lstrip('#').strip()
                    break

            # 提取 mermaid 代码
            i += 1
            mermaid_lines = []
            start_line = i + 1

            while i < len(lines) and not lines[i].strip().startswith('```'):
                mermaid_lines.append(lines[i])
                i += 1

            mermaid_code = '\n'.join(mermaid_lines)
            blocks.append((title, mermaid_code, start_line))

        i += 1

    return blocks


def generate_html(title: str, mermaid_code: str, description: str = "") -> str:
    """生成 HTML"""
    desc_html = f'<p class="description">{description}</p>' if description else ''

    return HTML_TEMPLATE.format(
        title=title,
        description=desc_html,
        mermaid_code=mermaid_code
    )


def process_file(input_file: Path, output_dir: Path, verbose: bool = False):
    """处理单个文件"""
    if not input_file.exists():
        print(f"错误：文件不存在 {input_file}")
        return

    # 读取内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 Mermaid 块
    blocks = extract_mermaid_blocks(content)

    if not blocks:
        if verbose:
            print(f"⚠️  {input_file.name}: 未找到 Mermaid 代码块")
        return

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成 HTML 文件
    base_name = input_file.stem

    for idx, (title, mermaid_code, line_num) in enumerate(blocks, 1):
        # 生成文件名
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        html_filename = f"{base_name}-mermaid-{idx:02d}-{safe_title[:30]}.html"
        html_path = output_dir / html_filename

        # 生成 HTML
        html_content = generate_html(title, mermaid_code)

        # 保存
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        if verbose:
            print(f"✓ 生成: {html_filename}")
            print(f"  标题: {title}")
            print(f"  行号: {line_num}")
            print()

    print(f"✓ {input_file.name}: 生成 {len(blocks)} 个 HTML 文件")


def process_directory(input_dir: Path, output_dir: Path, pattern: str = "*.md", verbose: bool = False):
    """批量处理目录"""
    files = list(input_dir.glob(pattern))

    if not files:
        print(f"未找到匹配 {pattern} 的文件")
        return

    print(f"找到 {len(files)} 个文件")
    print()

    for file in files:
        process_file(file, output_dir, verbose)


def main():
    parser = argparse.ArgumentParser(description='Mermaid to HTML 转换工具')
    parser.add_argument('input', help='输入文件或目录')
    parser.add_argument('-o', '--output', default='mermaid_html', help='输出目录（默认: mermaid_html）')
    parser.add_argument('-d', '--directory', action='store_true', help='批量处理目录')
    parser.add_argument('-p', '--pattern', default='*.md', help='文件匹配模式（默认: *.md）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if args.directory:
        if not input_path.is_dir():
            print(f"错误：{input_path} 不是目录")
            sys.exit(1)
        process_directory(input_path, output_dir, args.pattern, args.verbose)
    else:
        if not input_path.is_file():
            print(f"错误：{input_path} 不是文件")
            sys.exit(1)
        process_file(input_path, output_dir, args.verbose)

    print()
    print(f"✓ 所有 HTML 文件已保存到: {output_dir}")
    print()
    print("下一步:")
    print(f"  1. 在浏览器中打开 HTML 文件预览")
    print(f"  2. 使用 mermaid_to_image.py 生成图片")
    print(f"     python scripts/mermaid_to_image.py {output_dir}")


if __name__ == '__main__':
    main()
