#!/usr/bin/env python3
"""
函数依赖分析工具
功能：
1. 分析函数调用关系
2. 生成调用图
3. 查找特定函数的调用链
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class DependencyAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code: str, filename: str):
        self.source_code = source_code
        self.filename = filename

        # 存储结果
        self.functions = {}  # {func_name: {calls: [...], called_by: [...]}}
        self.current_function = None

    def visit_FunctionDef(self, node):
        func_name = node.name

        if func_name not in self.functions:
            self.functions[func_name] = {
                'calls': [],
                'called_by': [],
                'lineno': node.lineno
            }

        # 记录当前函数
        prev_function = self.current_function
        self.current_function = func_name

        # 继续遍历函数体
        self.generic_visit(node)

        # 恢复
        self.current_function = prev_function

    def visit_Call(self, node):
        if self.current_function:
            # 提取被调用的函数名
            func_name = self._get_func_name(node.func)

            if func_name:
                # 记录调用关系
                self.functions[self.current_function]['calls'].append(func_name)

                # 如果被调用的函数在本文件中，记录反向关系
                if func_name in self.functions:
                    self.functions[func_name]['called_by'].append(self.current_function)

        self.generic_visit(node)

    def _get_func_name(self, node):
        """获取函数名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def find_call_chain(self, target_func: str, max_depth: int = 5) -> List[List[str]]:
        """查找到目标函数的调用链"""
        chains = []

        def dfs(current, chain, depth):
            if depth > max_depth:
                return

            if current == target_func:
                chains.append(chain + [current])
                return

            if current in self.functions:
                for callee in self.functions[current]['calls']:
                    if callee not in chain:  # 避免循环
                        dfs(callee, chain + [current], depth + 1)

        # 从所有函数开始搜索
        for func in self.functions:
            dfs(func, [], 0)

        return chains

    def generate_call_graph(self) -> str:
        """生成调用图（DOT 格式）"""
        lines = []
        lines.append('digraph CallGraph {')
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box];')
        lines.append('')

        # 添加节点
        for func in self.functions:
            lines.append(f'  "{func}";')

        lines.append('')

        # 添加边
        for func, info in self.functions.items():
            for callee in set(info['calls']):  # 去重
                if callee in self.functions:  # 只显示内部调用
                    lines.append(f'  "{func}" -> "{callee}";')

        lines.append('}')

        return '\n'.join(lines)

    def generate_report(self, target_func: str = None) -> str:
        """生成依赖分析报告"""
        lines = []
        lines.append(f"# 依赖分析报告：{self.filename}\n")

        # 统计信息
        lines.append("## 统计信息\n")
        lines.append(f"- 函数数量：{len(self.functions)}")

        if self.functions:
            avg_calls = sum(len(f['calls']) for f in self.functions.values()) / len(self.functions)
            lines.append(f"- 平均调用数：{avg_calls:.2f}\n")

        # 如果指定了目标函数
        if target_func:
            if target_func in self.functions:
                lines.append(f"## 目标函数：{target_func}\n")

                info = self.functions[target_func]
                lines.append(f"**位置**：行 {info['lineno']}\n")

                if info['calls']:
                    lines.append("**调用**：")
                    for callee in set(info['calls']):
                        lines.append(f"- `{callee}()`")
                    lines.append("")

                if info['called_by']:
                    lines.append("**被调用**：")
                    for caller in set(info['called_by']):
                        lines.append(f"- `{caller}()`")
                    lines.append("")

                # 查找调用链
                chains = self.find_call_chain(target_func)
                if chains:
                    lines.append(f"**调用链**（到达 {target_func}）：")
                    for i, chain in enumerate(chains[:5], 1):  # 只显示前 5 条
                        chain_str = ' → '.join(chain)
                        lines.append(f"{i}. {chain_str}")
                    lines.append("")
            else:
                lines.append(f"## 错误\n")
                lines.append(f"函数 `{target_func}` 未找到\n")

        # 所有函数列表
        lines.append("## 函数列表\n")

        for func, info in sorted(self.functions.items()):
            calls_count = len(info['calls'])
            called_by_count = len(info['called_by'])

            lines.append(f"### {func}() (行 {info['lineno']})\n")
            lines.append(f"- 调用：{calls_count} 个函数")
            lines.append(f"- 被调用：{called_by_count} 次\n")

            if info['calls']:
                unique_calls = list(set(info['calls']))[:5]
                calls_str = ', '.join(f"`{c}()`" for c in unique_calls)
                lines.append(f"  调用：{calls_str}")
                if len(info['calls']) > 5:
                    lines.append(f"  （还有 {len(info['calls']) - 5} 个）")
                lines.append("")

        return '\n'.join(lines)


def analyze_dependencies(filepath: str,
                         target_func: str = None,
                         output: str = None,
                         graph: str = None):
    """分析文件依赖"""
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

    # 分析依赖
    analyzer = DependencyAnalyzer(source_code, path.name)
    analyzer.visit(tree)

    # 生成报告
    report = analyzer.generate_report(target_func)

    # 输出报告
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ 报告已保存到：{output}")
    else:
        print(report)

    # 生成调用图
    if graph:
        call_graph = analyzer.generate_call_graph()
        with open(graph, 'w', encoding='utf-8') as f:
            f.write(call_graph)
        print(f"✓ 调用图已保存到：{graph}")
        print(f"  使用 Graphviz 可视化：dot -Tpng {graph} -o call_graph.png")


def main():
    parser = argparse.ArgumentParser(description='函数依赖分析工具')
    parser.add_argument('file', help='要分析的 Python 文件')
    parser.add_argument('-f', '--function', help='目标函数名')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-g', '--graph', help='调用图输出路径（DOT 格式）')

    args = parser.parse_args()

    analyze_dependencies(args.file, args.function, args.output, args.graph)


if __name__ == '__main__':
    main()
