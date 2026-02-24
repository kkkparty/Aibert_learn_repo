#!/usr/bin/env python3
"""
Markdown 目录生成工具
功能：
1. 自动提取 Markdown 文件中的标题
2. 生成带链接的目录
3. 支持多级标题
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


def extract_headings(content: str) -> List[Tuple[int, str, str]]:
    """
    提取 Markdown 标题
    
    返回: [(level, text, anchor), ...]
    """
    headings = []
    lines = content.split('\n')
    
    for line in lines:
        # 匹配 # 标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            
            # 生成 anchor（GitHub 风格）
            anchor = text.lower()
            anchor = re.sub(r'[^\w\s-]', '', anchor)
            anchor = re.sub(r'[\s_]+', '-', anchor)
            anchor = anchor.strip('-')
            
            headings.append((level, text, anchor))
    
    return headings


def generate_toc(headings: List[Tuple[int, str, str]], 
                 max_level: int = 3,
                 indent_size: int = 2) -> str:
    """
    生成目录
    
    Args:
        headings: 标题列表
        max_level: 最大标题级别
        indent_size: 缩进空格数
    """
    toc_lines = []
    toc_lines.append("## 目录\n")
    
    for level, text, anchor in headings:
        if level > max_level:
            continue
        
        # 计算缩进
        indent = ' ' * ((level - 1) * indent_size)
        
        # 生成目录项
        link = f"[{text}](#{anchor})"
        toc_lines.append(f"{indent}- {link}")
    
    return '\n'.join(toc_lines)


def insert_or_update_toc(content: str, toc: str) -> str:
    """
    插入或更新目录
    
    如果文件中已有目录标记，则更新；否则在第一个标题后插入
    """
    # 查找现有目录标记
    toc_pattern = r'<!-- TOC START -->.*?<!-- TOC END -->'
    
    toc_block = f"<!-- TOC START -->\n{toc}\n<!-- TOC END -->"
    
    if re.search(toc_pattern, content, re.DOTALL):
        # 更新现有目录
        content = re.sub(toc_pattern, toc_block, content, flags=re.DOTALL)
    else:
        # 在第一个标题后插入
        lines = content.split('\n')
        insert_pos = 0
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                insert_pos = i + 1
                break
        
        lines.insert(insert_pos, '\n' + toc_block + '\n')
        content = '\n'.join(lines)
    
    return content


def process_file(filepath: str, max_level: int = 3, inplace: bool = False):
    """处理单个文件"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"错误：文件 {filepath} 不存在")
        return
    
    # 读取文件
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    headings = extract_headings(content)
    
    if not headings:
        print(f"警告：文件 {filepath} 中没有找到标题")
        return
    
    # 生成目录
    toc = generate_toc(headings, max_level)
    
    # 输出或更新文件
    if inplace:
        new_content = insert_or_update_toc(content, toc)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ 已更新 {filepath} 的目录")
    else:
        print(toc)


def process_directory(directory: str, pattern: str = "*.md", max_level: int = 3):
    """处理目录中的所有 Markdown 文件"""
    path = Path(directory)
    
    if not path.exists():
        print(f"错误：目录 {directory} 不存在")
        return
    
    files = list(path.glob(pattern))
    
    if not files:
        print(f"警告：目录 {directory} 中没有找到匹配 {pattern} 的文件")
        return
    
    print(f"找到 {len(files)} 个文件")
    
    for file in files:
        print(f"\n处理：{file.name}")
        process_file(str(file), max_level, inplace=True)


def main():
    parser = argparse.ArgumentParser(description='Markdown 目录生成工具')
    parser.add_argument('path', help='文件或目录路径')
    parser.add_argument('-l', '--max-level', type=int, default=3, 
                        help='最大标题级别（默认：3）')
    parser.add_argument('-i', '--inplace', action='store_true',
                        help='直接修改文件（默认：输出到终端）')
    parser.add_argument('-p', '--pattern', default='*.md',
                        help='文件匹配模式（仅目录模式，默认：*.md）')
    parser.add_argument('-d', '--directory', action='store_true',
                        help='目录模式：处理目录中的所有文件')
    
    args = parser.parse_args()
    
    if args.directory:
        process_directory(args.path, args.pattern, args.max_level)
    else:
        process_file(args.path, args.max_level, args.inplace)


if __name__ == '__main__':
    main()
