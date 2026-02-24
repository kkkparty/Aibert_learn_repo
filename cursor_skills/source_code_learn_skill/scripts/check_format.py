#!/usr/bin/env python3
"""
文档格式检查工具
功能：
1. 检查代码引用格式（是否有行号）
2. 检查图示完整性
3. 检查面试题数量
4. 检查章节结构
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


class DocumentChecker:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = ''
        self.lines = []
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)
        
        if self.filepath.exists():
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
    
    def check_code_references(self):
        """检查代码引用格式"""
        # 查找代码块
        code_blocks = re.finditer(r'```(\w+)?\n(.*?)```', self.content, re.DOTALL)
        
        for match in code_blocks:
            lang = match.group(1)
            code = match.group(2)
            
            # 检查是否是源码引用（应该有行号格式）
            if lang and ':' in self.lines[self.content[:match.start()].count('\n')]:
                # 格式：```startLine:endLine:path
                self.stats['code_refs'] += 1
            elif lang:
                # 普通代码块
                self.stats['code_blocks'] += 1
    
    def check_diagrams(self):
        """检查图示"""
        # 查找常见图示标记
        diagram_patterns = [
            r'```\n.*?[┌└│─↓↑].*?```',  # ASCII 图
            r'流程图',
            r'架构图',
            r'时序图',
            r'数据流图',
            r'对比图',
        ]
        
        for pattern in diagram_patterns:
            matches = re.findall(pattern, self.content, re.DOTALL)
            self.stats['diagrams'] += len(matches)
    
    def check_interview_questions(self):
        """检查面试题"""
        # 查找面试题标记
        q_pattern = r'\*\*Q\d+[：:](.*?)\*\*'
        questions = re.findall(q_pattern, self.content)
        
        self.stats['interview_questions'] = len(questions)
        
        # 检查分类
        basic = len(re.findall(r'### 基础题', self.content))
        advanced = len(re.findall(r'### 进阶题', self.content))
        deep = len(re.findall(r'### 深入题', self.content))
        
        self.stats['basic_questions'] = basic
        self.stats['advanced_questions'] = advanced
        self.stats['deep_questions'] = deep
        
        # 建议：每章至少8道题
        if self.stats['interview_questions'] < 8:
            self.warnings.append(
                f"面试题数量不足：{self.stats['interview_questions']} 道（建议至少 8 道）"
            )
    
    def check_structure(self):
        """检查章节结构"""
        # 检查是否有"本章目标"
        if '## 本章目标' not in self.content:
            self.warnings.append("缺少"本章目标"章节")
        
        # 检查是否有"本章总结"
        if '## 本章总结' not in self.content and '## 总结' not in self.content:
            self.warnings.append("缺少"本章总结"章节")
        
        # 检查标题层级
        h1_count = len(re.findall(r'^# ', self.content, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', self.content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', self.content, re.MULTILINE))
        
        self.stats['h1_headings'] = h1_count
        self.stats['h2_headings'] = h2_count
        self.stats['h3_headings'] = h3_count
        
        if h1_count > 1:
            self.warnings.append(f"一级标题过多：{h1_count} 个（建议只有 1 个）")
    
    def check_special_chars(self):
        """检查特殊字符（emoji 等）"""
        # 检查 emoji
        emoji_pattern = r'[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]'
        emojis = re.findall(emoji_pattern, self.content)
        
        if emojis:
            self.warnings.append(f"检测到 {len(emojis)} 个 emoji 符号（建议移除）")
    
    def check_code_blocks_size(self):
        """检查代码块大小"""
        code_blocks = re.finditer(r'```.*?\n(.*?)```', self.content, re.DOTALL)
        
        for match in code_blocks:
            code = match.group(1)
            lines = code.count('\n')
            
            if lines > 100:
                line_num = self.content[:match.start()].count('\n') + 1
                self.warnings.append(
                    f"代码块过大：行 {line_num}，{lines} 行（建议不超过 100 行）"
                )
    
    def run_all_checks(self):
        """运行所有检查"""
        self.check_code_references()
        self.check_diagrams()
        self.check_interview_questions()
        self.check_structure()
        self.check_special_chars()
        self.check_code_blocks_size()
    
    def generate_report(self) -> str:
        """生成检查报告"""
        lines = []
        lines.append(f"# 文档格式检查报告：{self.filepath.name}\n")
        
        # 统计信息
        lines.append("## 统计信息\n")
        lines.append(f"- 文件大小：{len(self.content)} 字符")
        lines.append(f"- 行数：{len(self.lines)}")
        lines.append(f"- 一级标题：{self.stats['h1_headings']}")
        lines.append(f"- 二级标题：{self.stats['h2_headings']}")
        lines.append(f"- 三级标题：{self.stats['h3_headings']}")
        lines.append(f"- 代码块：{self.stats['code_blocks']}")
        lines.append(f"- 代码引用：{self.stats['code_refs']}")
        lines.append(f"- 图示：{self.stats['diagrams']}")
        lines.append(f"- 面试题：{self.stats['interview_questions']}")
        lines.append("")
        
        # 问题
        if self.issues:
            lines.append("## ❌ 问题\n")
            for issue in self.issues:
                lines.append(f"- {issue}")
            lines.append("")
        
        # 警告
        if self.warnings:
            lines.append("## ⚠️ 警告\n")
            for warning in self.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # 总结
        if not self.issues and not self.warnings:
            lines.append("## ✓ 检查通过\n")
            lines.append("文档格式符合规范！")
        else:
            lines.append(f"## 总结\n")
            lines.append(f"- 问题：{len(self.issues)} 个")
            lines.append(f"- 警告：{len(self.warnings)} 个")
        
        return '\n'.join(lines)


def check_file(filepath: str):
    """检查单个文件"""
    checker = DocumentChecker(filepath)
    
    if not checker.filepath.exists():
        print(f"错误：文件 {filepath} 不存在")
        return False
    
    checker.run_all_checks()
    report = checker.generate_report()
    print(report)
    
    return len(checker.issues) == 0


def check_directory(directory: str, pattern: str = "*.md"):
    """检查目录中的所有文件"""
    path = Path(directory)
    
    if not path.exists():
        print(f"错误：目录 {directory} 不存在")
        return
    
    files = list(path.glob(pattern))
    
    if not files:
        print(f"警告：目录 {directory} 中没有找到匹配 {pattern} 的文件")
        return
    
    print(f"找到 {len(files)} 个文件\n")
    
    results = {}
    for file in files:
        print(f"{'='*60}")
        print(f"检查：{file.name}")
        print(f"{'='*60}\n")
        results[file.name] = check_file(str(file))
        print()
    
    # 总结
    print(f"{'='*60}")
    print("总结")
    print(f"{'='*60}")
    passed = sum(1 for v in results.values() if v)
    print(f"通过：{passed}/{len(results)}")
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {name}")


def main():
    parser = argparse.ArgumentParser(description='文档格式检查工具')
    parser.add_argument('path', help='文件或目录路径')
    parser.add_argument('-d', '--directory', action='store_true',
                        help='目录模式：检查目录中的所有文件')
    parser.add_argument('-p', '--pattern', default='*.md',
                        help='文件匹配模式（仅目录模式，默认：*.md）')
    
    args = parser.parse_args()
    
    if args.directory:
        check_directory(args.path, args.pattern)
    else:
        check_file(args.path)


if __name__ == '__main__':
    main()
