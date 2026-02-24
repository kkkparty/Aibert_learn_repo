#!/usr/bin/env python3
"""
代码引用验证工具
功能：
1. 验证代码引用的文件路径是否存在
2. 验证代码引用的行号是否正确
3. 检查引用的代码是否已改变
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional


class CodeReferenceValidator:
    def __init__(self, doc_path: str, code_base_path: str = '.'):
        self.doc_path = Path(doc_path)
        self.code_base_path = Path(code_base_path)
        self.content = ''
        self.issues = []
        self.warnings = []
        
        if self.doc_path.exists():
            with open(self.doc_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
    
    def extract_code_references(self) -> List[Tuple[int, str, int, int, str]]:
        """
        提取文档中的代码引用
        
        返回: [(line_num, file_path, start_line, end_line, code), ...]
        """
        references = []
        lines = self.content.split('\n')
        
        in_code_block = False
        code_lines = []
        ref_info = None
        
        for i, line in enumerate(lines, 1):
            # 检查代码块开始
            if line.startswith('```'):
                if not in_code_block:
                    # 检查是否是代码引用格式：```start:end:path
                    match = re.match(r'```(\d+):(\d+):(.+)$', line)
                    if match:
                        start_line = int(match.group(1))
                        end_line = int(match.group(2))
                        file_path = match.group(3).strip()
                        ref_info = (i, file_path, start_line, end_line)
                        in_code_block = True
                        code_lines = []
                else:
                    # 代码块结束
                    if ref_info:
                        code = '\n'.join(code_lines)
                        references.append((*ref_info, code))
                        ref_info = None
                    in_code_block = False
                    code_lines = []
            elif in_code_block and ref_info:
                code_lines.append(line)
        
        return references
    
    def validate_reference(self, ref: Tuple[int, str, int, int, str]) -> bool:
        """验证单个代码引用"""
        doc_line, file_path, start_line, end_line, doc_code = ref
        
        # 解析文件路径（可能是相对路径）
        full_path = self.code_base_path / file_path
        
        # 检查文件是否存在
        if not full_path.exists():
            self.issues.append(
                f"行 {doc_line}: 文件不存在 '{file_path}'"
            )
            return False
        
        # 读取源文件
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
        except Exception as e:
            self.issues.append(
                f"行 {doc_line}: 无法读取文件 '{file_path}': {e}"
            )
            return False
        
        # 检查行号范围
        if start_line < 1 or end_line > len(source_lines):
            self.issues.append(
                f"行 {doc_line}: 行号越界 {start_line}:{end_line}，文件共 {len(source_lines)} 行"
            )
            return False
        
        if start_line > end_line:
            self.issues.append(
                f"行 {doc_line}: 起始行 {start_line} 大于结束行 {end_line}"
            )
            return False
        
        # 提取实际代码
        actual_code = ''.join(source_lines[start_line-1:end_line]).rstrip('\n')
        doc_code_clean = doc_code.rstrip('\n')
        
        # 比较代码（忽略行尾空白）
        if actual_code != doc_code_clean:
            self.warnings.append(
                f"行 {doc_line}: 代码不匹配 '{file_path}:{start_line}:{end_line}'\n"
                f"  可能原因：源代码已修改\n"
                f"  建议：更新文档中的代码"
            )
            return False
        
        return True
    
    def validate_all(self):
        """验证所有代码引用"""
        references = self.extract_code_references()
        
        if not references:
            print(f"✓ 文档中没有代码引用")
            return True
        
        print(f"找到 {len(references)} 个代码引用\n")
        
        valid_count = 0
        for ref in references:
            if self.validate_reference(ref):
                valid_count += 1
        
        return valid_count == len(references)
    
    def generate_report(self) -> str:
        """生成验证报告"""
        lines = []
        lines.append(f"# 代码引用验证报告：{self.doc_path.name}\n")
        
        # 统计
        references = self.extract_code_references()
        lines.append(f"- 代码引用数量：{len(references)}")
        lines.append(f"- 问题：{len(self.issues)}")
        lines.append(f"- 警告：{len(self.warnings)}\n")
        
        # 问题
        if self.issues:
            lines.append("## ❌ 问题\n")
            for issue in self.issues:
                lines.append(f"{issue}\n")
        
        # 警告
        if self.warnings:
            lines.append("## ⚠️ 警告\n")
            for warning in self.warnings:
                lines.append(f"{warning}\n")
        
        # 总结
        if not self.issues and not self.warnings:
            lines.append("## ✓ 验证通过\n")
            lines.append("所有代码引用都有效！")
        
        return '\n'.join(lines)


def validate_file(doc_path: str, code_base_path: str = '.'):
    """验证单个文档"""
    validator = CodeReferenceValidator(doc_path, code_base_path)
    
    if not validator.doc_path.exists():
        print(f"错误：文档 {doc_path} 不存在")
        return False
    
    validator.validate_all()
    report = validator.generate_report()
    print(report)
    
    return len(validator.issues) == 0


def validate_directory(directory: str, pattern: str = "*.md", code_base_path: str = '.'):
    """验证目录中的所有文档"""
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
        print(f"验证：{file.name}")
        print(f"{'='*60}\n")
        results[file.name] = validate_file(str(file), code_base_path)
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
    parser = argparse.ArgumentParser(description='代码引用验证工具')
    parser.add_argument('path', help='文档文件或目录路径')
    parser.add_argument('-c', '--code-base', default='.',
                        help='代码库根目录（默认：当前目录）')
    parser.add_argument('-d', '--directory', action='store_true',
                        help='目录模式：验证目录中的所有文档')
    parser.add_argument('-p', '--pattern', default='*.md',
                        help='文件匹配模式（仅目录模式，默认：*.md）')
    
    args = parser.parse_args()
    
    if args.directory:
        validate_directory(args.path, args.pattern, args.code_base)
    else:
        validate_file(args.path, args.code_base)


if __name__ == '__main__':
    main()
