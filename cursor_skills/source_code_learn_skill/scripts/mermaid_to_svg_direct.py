#!/usr/bin/env python3
"""
直接使用 Mermaid CLI 或在线 API 生成 SVG/PNG
不依赖浏览器渲染
"""

import subprocess
import sys
import requests
import base64
from pathlib import Path


def mermaid_to_svg_online(code: str) -> bytes:
    """使用 Mermaid Ink API 在线生成 SVG"""
    try:
        # Mermaid Ink API
        url = "https://mermaid.ink/svg"
        response = requests.post(url, data=code, timeout=30)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"在线 API 失败: {e}")
    return None


def svg_to_png(svg_content: bytes, output_path: Path):
    """使用 rsvg-convert 或 inkscape 将 SVG 转换为 PNG"""
    # 尝试 rsvg-convert
    rsvg = subprocess.which('rsvg-convert')
    if rsvg:
        try:
            result = subprocess.run(
                [rsvg, '-w', '1200', '-f', 'png'],
                input=svg_content,
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                with open(output_path, 'wb') as f:
                    f.write(result.stdout)
                return True
        except Exception as e:
            print(f"rsvg-convert 失败: {e}")

    # 尝试 inkscape
    inkscape = subprocess.which('inkscape')
    if inkscape:
        # 先保存 SVG
        svg_path = output_path.with_suffix('.svg')
        with open(svg_path, 'wb') as f:
            f.write(svg_content)
        try:
            result = subprocess.run(
                [inkscape, '--export-type=png', f'--export-filename={output_path}', str(svg_path)],
                capture_output=True,
                timeout=30
            )
            svg_path.unlink()
            if result.returncode == 0:
                return True
        except Exception as e:
            print(f"inkscape 失败: {e}")
            svg_path.unlink(missing_ok=True)

    return False


def main():
    if len(sys.argv) < 3:
        print("用法: mermaid_to_svg_direct.py <mermaid_code_file> <output.png>")
        sys.exit(1)

    code_file = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    with open(code_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # 尝试在线生成
    print("尝试使用在线 API 生成 SVG...")
    svg_content = mermaid_to_svg_online(code)

    if svg_content:
        print("✓ SVG 生成成功")
        if svg_to_png(svg_content, output_path):
            print(f"✓ PNG 已生成: {output_path}")
        else:
            # 直接保存 SVG
            svg_path = output_path.with_suffix('.svg')
            with open(svg_path, 'wb') as f:
                f.write(svg_content)
            print(f"✓ SVG 已保存: {svg_path}")
    else:
        print("✗ 无法生成图片")


if __name__ == "__main__":
    main()
