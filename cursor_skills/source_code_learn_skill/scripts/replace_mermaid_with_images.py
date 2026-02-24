#!/usr/bin/env python3
"""
Mermaid 替换工具
功能：
1. 将 Markdown 中的 Mermaid 代码块替换为图片引用
2. 保留原始 Mermaid 代码在折叠区域（可选）
3. 支持预览模式
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


def find_mermaid_blocks_with_positions(content: str) -> List[Tuple[int, int, str]]:
    """
    查找 Mermaid 代码块的位置

    Returns:
        List of (start_pos, end_pos, mermaid_code)
    """
    blocks = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('```mermaid'):
            start_line = i
            i += 1
            mermaid_lines = []

            while i < len(lines) and not lines[i].strip().startswith('```'):
                mermaid_lines.append(lines[i])
                i += 1

            end_line = i
            mermaid_code = '\n'.join(mermaid_lines)
            blocks.append((start_line, end_line, mermaid_code))

        i += 1

    return blocks


def generate_image_reference(image_path: str, alt_text: str, keep_code: bool = True, mermaid_code: str = "") -> str:
    """生成图片引用"""
    result = []

    # 图片引用
    result.append(f"![{alt_text}]({image_path})")
    result.append("")

    # 可选：保留原始代码在折叠区域
    if keep_code and mermaid_code:
        result.append("<details>")
        result.append("<summary>查看 Mermaid 源码</summary>")
        result.append("")
        result.append("```mermaid")
        result.append(mermaid_code)
        result.append("```")
        result.append("")
        result.append("</details>")
        result.append("")

    return '\n'.join(result)


def replace_mermaid_blocks(content: str, image_dir: Path, keep_code: bool = True, dry_run: bool = False) -> Tuple[str, int]:
    """
    替换 Mermaid 代码块为图片

    Returns:
        (new_content, replace_count)
    """
    lines = content.split('\n')
    blocks = find_mermaid_blocks_with_positions(content)

    if not blocks:
        return content, 0

    # 从后往前替换，避免位置偏移
    blocks.reverse()

    replace_count = 0
    for idx, (start_line, end_line, mermaid_code) in enumerate(blocks):
        # 计算图片索引（从后往前，所以需要反转）
        image_idx = len(blocks) - idx

        # 查找对应的图片文件
        # 假设图片命名为: xxx-mermaid-01-title.png
        image_files = list(image_dir.glob(f"*-mermaid-{image_idx:02d}-*.png"))

        if not image_files:
            print(f"⚠️  未找到图片 #{image_idx}")
            continue

        image_file = image_files[0]

        # 生成相对路径
        image_path = f"images/{image_file.name}"

        # 查找标题（向上搜索）
        alt_text = f"Mermaid Diagram {image_idx}"
        for j in range(start_line - 1, max(0, start_line - 10), -1):
            if lines[j].strip().startswith('#'):
                alt_text = lines[j].strip().lstrip('#').strip()
                break

        # 生成替换内容
        replacement = generate_image_reference(image_path, alt_text, keep_code, mermaid_code)
        replacement_lines = replacement.split('\n')

        # 替换
        lines[start_line:end_line+1] = replacement_lines
        replace_count += 1

        if dry_run:
            print(f"✓ 将替换第 {start_line+1}-{end_line+1} 行")
            print(f"  图片: {image_path}")
            print(f"  标题: {alt_text}")
            print()

    return '\n'.join(lines), replace_count


def process_file(input_file: Path, image_dir: Path, output_file: Path = None,
                keep_code: bool = True, dry_run: bool = False, backup: bool = True):
    """处理文件"""
    if not input_file.exists():
        print(f"错误：文件不存在 {input_file}")
        return

    # 读取内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换
    new_content, replace_count = replace_mermaid_blocks(content, image_dir, keep_code, dry_run)

    if replace_count == 0:
        print(f"⚠️  {input_file.name}: 未找到可替换的 Mermaid 代码块")
        return

    if dry_run:
        print(f"预览模式: 将替换 {replace_count} 个 Mermaid 代码块")
        return

    # 确定输出文件
    if output_file is None:
        output_file = input_file

        # 备份原文件
        if backup:
            backup_file = input_file.with_suffix('.md.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已备份: {backup_file.name}")

    # 写入
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ {output_file.name}: 已替换 {replace_count} 个 Mermaid 代码块")


def main():
    parser = argparse.ArgumentParser(description='Mermaid 替换工具')
    parser.add_argument('input', help='输入 Markdown 文件')
    parser.add_argument('-i', '--image-dir', default='mermaid_images', help='图片目录（默认: mermaid_images）')
    parser.add_argument('-o', '--output', help='输出文件（默认: 覆盖原文件）')
    parser.add_argument('--no-keep-code', action='store_true', help='不保留原始 Mermaid 代码')
    parser.add_argument('--no-backup', action='store_true', help='不备份原文件')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改')

    args = parser.parse_args()

    input_file = Path(args.input)
    image_dir = Path(args.image_dir)
    output_file = Path(args.output) if args.output else None

    if not image_dir.is_dir():
        print(f"错误：图片目录不存在 {image_dir}")
        print("请先运行 mermaid_to_image.py 生成图片")
        sys.exit(1)

    keep_code = not args.no_keep_code
    backup = not args.no_backup

    process_file(input_file, image_dir, output_file, keep_code, args.dry_run, backup)

    if not args.dry_run:
        print()
        print("✓ 完成！")
        if keep_code:
            print("  原始 Mermaid 代码已保留在折叠区域")
        if backup and output_file is None:
            print("  原文件已备份为 .md.backup")


if __name__ == '__main__':
    main()
