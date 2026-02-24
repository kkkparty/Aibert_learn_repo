#!/usr/bin/env python3
"""
源码分析工具
功能：
1. 提取文件中的所有函数/类定义
2. 统计代码行数
3. 生成函数调用图
4. 导出为 Markdown 格式
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Set
import argparse


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code: str, filename: str):
        self.source_code = source_code
        self.filename = filename
        self.lines = source_code.split('\n')
        
        # 存储分析结果
        self.classes = []  # [(name, lineno, end_lineno, docstring, methods)]
        self.functions = []  # [(name, lineno, end_lineno, docstring, args)]
        self.imports = []  # [(module, names)]
        self.current_class = None
        
    def visit_ClassDef(self, node):
        # 获取文档字符串
        docstring = ast.get_docstring(node)
        
        # 获取方法
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'lineno': item.lineno,
                    'args': [arg.arg for arg in item.args.args],
                    'docstring': ast.get_docstring(item)
                })
        
        self.classes.append({
            'name': node.name,
            'lineno': node.lineno,
            'end_lineno': node.end_lineno,
            'docstring': docstring,
            'methods': methods,
            'bases': [self._get_name(base) for base in node.bases]
        })
        
        # 继续遍历
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None
        
    def visit_FunctionDef(self, node):
        # 跳过类方法（已在 visit_ClassDef 中处理）
        if self.current_class is None:
            docstring = ast.get_docstring(node)
            args = [arg.arg for arg in node.args.args]
            
            self.functions.append({
                'name': node.name,
                'lineno': node.lineno,
                'end_lineno': node.end_lineno,
                'docstring': docstring,
                'args': args
            })
        
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'asname': alias.asname,
                'type': 'import'
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'asname': alias.asname,
                'type': 'from'
            })
        self.generic_visit(node)
    
    def _get_name(self, node):
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def generate_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append(f"# 源码分析报告：{self.filename}\n")
        
        # 统计信息
        total_lines = len(self.lines)
        code_lines = sum(1 for line in self.lines if line.strip() and not line.strip().startswith('#'))
        
        report.append("## 统计信息\n")
        report.append(f"- 总行数：{total_lines}")
        report.append(f"- 代码行数：{code_lines}")
        report.append(f"- 类定义：{len(self.classes)}")
        report.append(f"- 函数定义：{len(self.functions)}")
        report.append(f"- 导入语句：{len(self.imports)}\n")
        
        # 导入列表
        if self.imports:
            report.append("## 导入列表\n")
            for imp in self.imports:
                if imp['type'] == 'import':
                    report.append(f"- `import {imp['module']}`")
                else:
                    report.append(f"- `from {imp['module']} import {imp['name']}`")
            report.append("")
        
        # 类定义
        if self.classes:
            report.append("## 类定义\n")
            for cls in self.classes:
                report.append(f"### {cls['name']} (行 {cls['lineno']}-{cls['end_lineno']})\n")
                
                if cls['bases']:
                    report.append(f"**继承**：`{', '.join(cls['bases'])}`\n")
                
                if cls['docstring']:
                    report.append(f"**文档**：\n```\n{cls['docstring']}\n```\n")
                
                if cls['methods']:
                    report.append("**方法**：")
                    for method in cls['methods']:
                        args_str = ', '.join(method['args'])
                        report.append(f"- `{method['name']}({args_str})` (行 {method['lineno']})")
                        if method['docstring']:
                            first_line = method['docstring'].split('\n')[0]
                            report.append(f"  - {first_line}")
                    report.append("")
        
        # 函数定义
        if self.functions:
            report.append("## 函数定义\n")
            for func in self.functions:
                args_str = ', '.join(func['args'])
                report.append(f"### {func['name']}({args_str}) (行 {func['lineno']}-{func['end_lineno']})\n")
                
                if func['docstring']:
                    report.append(f"**文档**：\n```\n{func['docstring']}\n```\n")
        
        return '\n'.join(report)


def analyze_file(filepath: str, output: str = None):
    """分析单个 Python 文件"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"错误：文件 {filepath} 不存在")
        return
    
    # 读取源码
    with open(path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # 解析 AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"语法错误：{e}")
        return
    
    # 分析代码
    analyzer = CodeAnalyzer(source_code, path.name)
    analyzer.visit(tree)
    
    # 生成报告
    report = analyzer.generate_report()
    
    # 输出报告
    if output:
        output_path = Path(output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ 报告已保存到：{output}")
    else:
        print(report)


def main():
    parser = argparse.ArgumentParser(description='源码分析工具')
    parser.add_argument('file', help='要分析的 Python 文件')
    parser.add_argument('-o', '--output', help='输出文件路径（默认输出到终端）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    analyze_file(args.file, args.output)


if __name__ == '__main__':
    main()
