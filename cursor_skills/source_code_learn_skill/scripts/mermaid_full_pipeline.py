#!/usr/bin/env python3
"""
Mermaid 全自动处理流水线
功能：Markdown (Mermaid) → HTML → 图片（Cursor Browser Extension） → 替换 Markdown → 导出 PDF
使用 Cursor Browser Extension 的 browser 工具进行截图
"""

import re
import sys
import os
import base64
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple


# ============================================================
# 步骤 1：从 Markdown 提取 Mermaid 代码
# ============================================================

def extract_mermaid_blocks(content: str) -> List[Tuple[str, str, int]]:
    """提取 Mermaid 代码块"""
    blocks = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('```mermaid'):
            title = "diagram"
            for j in range(i - 1, max(0, i - 10), -1):
                if lines[j].strip().startswith('#'):
                    title = lines[j].strip().lstrip('#').strip()
                    break
            i += 1
            mermaid_lines = []
            start_line = i
            while i < len(lines) and not lines[i].strip().startswith('```'):
                mermaid_lines.append(lines[i])
                i += 1
            mermaid_code = '\n'.join(mermaid_lines)
            blocks.append((title, mermaid_code, start_line))
        i += 1
    return blocks


# ============================================================
# 步骤 2：生成 Mermaid SVG（使用 wkhtmltopdf 内置的渲染引擎）
# ============================================================

MERMAID_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
body {{ margin: 0; padding: 20px; background: white; font-family: sans-serif; }}
.mermaid {{ text-align: center; min-height: 200px; }}
h2 {{ color: #333; text-align: center; }}
#render-complete {{ display: none; }}
</style>
</head>
<body>
<h2>{title}</h2>
<div class="mermaid">
{code}
</div>
<div id="render-complete">RENDERED</div>
<script>
mermaid.initialize({{
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose'
}});

// 等待渲染完成后显示标记
window.addEventListener('load', function() {{
    setTimeout(function() {{
        var svg = document.querySelector('svg');
        if (svg) {{
            document.getElementById('render-complete').style.display = 'block';
        }}
    }}, 5000); // 等待 5 秒确保完全渲染
}});
</script>
</body>
</html>"""


def generate_mermaid_html(title: str, code: str, output_path: Path):
    """生成 iPhone 风格的 Mermaid HTML 文件"""
    # iPhone 风格模板：简洁、优雅、大量留白、柔和阴影
    iphone_style_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
                        'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.08),
                0 8px 24px rgba(0, 0, 0, 0.04),
                0 0 0 0.5px rgba(0, 0, 0, 0.02);
            max-width: 1400px;
            width: 100%;
            padding: 60px 50px;
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg,
                #007AFF 0%,
                #5AC8FA 25%,
                #34C759 50%,
                #FF9500 75%,
                #FF3B30 100%);
            opacity: 0.6;
        }}

        .header {{
            margin-bottom: 50px;
            text-align: center;
        }}

        h1 {{
            font-size: 32px;
            font-weight: 700;
            color: #1d1d1f;
            letter-spacing: -0.5px;
            margin-bottom: 12px;
            line-height: 1.2;
        }}

        .subtitle {{
            font-size: 17px;
            color: #86868b;
            font-weight: 400;
            letter-spacing: -0.2px;
        }}

        .mermaid-container {{
            background: #ffffff;
            border-radius: 16px;
            padding: 40px;
            margin: 30px 0;
            box-shadow:
                inset 0 1px 3px rgba(0, 0, 0, 0.06),
                0 1px 0 rgba(255, 255, 255, 0.8);
            position: relative;
            overflow: visible;
        }}

        .mermaid {{
            text-align: center;
            margin: 0 auto;
            max-width: 100%;
        }}

        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}

        #mermaid-render-complete {{
            display: none;
        }}

        .loading {{
            display: none;
            text-align: center;
            padding: 40px;
            color: #86868b;
            font-size: 15px;
        }}

        .loading.active {{
            display: block;
        }}

        .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #e5e5e7;
            border-top-color: #007AFF;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 12px;
            vertical-align: middle;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 20px 10px;
            }}

            .card {{
                padding: 40px 30px;
                border-radius: 20px;
            }}

            h1 {{
                font-size: 28px;
            }}

            .mermaid-container {{
                padding: 30px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">Mermaid Diagram</div>
        </div>

        <div class="loading active" id="loading">
            <span class="spinner"></span>
            <span>正在渲染图表...</span>
        </div>

        <div class="mermaid-container">
            <div class="mermaid">
{code}
            </div>
        </div>

        <div id="mermaid-render-complete">RENDERED</div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            themeVariables: {{
                primaryColor: '#007AFF',
                primaryTextColor: '#1d1d1f',
                primaryBorderColor: '#007AFF',
                lineColor: '#d2d2d7',
                secondaryColor: '#34C759',
                tertiaryColor: '#FF9500',
                background: '#ffffff',
                mainBkgColor: '#ffffff',
                textColor: '#1d1d1f',
                border1: '#e5e5e7',
                border2: '#d2d2d7',
                noteBkgColor: '#f5f5f7',
                noteTextColor: '#1d1d1f',
                noteBorderColor: '#d2d2d7',
                fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif',
                fontSize: '15px'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis',
                padding: 20
            }},
            gantt: {{
                useMaxWidth: true,
                leftPadding: 75,
                gridLineStartPadding: 35,
                fontSize: 14
            }},
            sequence: {{
                useMaxWidth: true,
                diagramMarginX: 50,
                diagramMarginY: 10,
                actorMargin: 50,
                width: 150,
                height: 65,
                boxMargin: 10,
                boxTextMargin: 5,
                noteMargin: 10,
                messageMargin: 35
            }}
        }});

        (function() {{
            var loadingEl = document.getElementById('loading');
            var renderComplete = false;
            var checkCount = 0;
            var minChecks = 10; // 至少检查 10 次（1 秒）确保稳定

            var checkRender = setInterval(function() {{
                checkCount++;
                var svg = document.querySelector('.mermaid svg');

                // 检查 SVG 是否存在且有内容
                if (svg && svg.children.length > 0) {{
                    // 进一步检查 SVG 是否有实际渲染内容（不是空的）
                    var hasContent = svg.getBBox().width > 0 && svg.getBBox().height > 0;

                    if (hasContent && checkCount >= minChecks && !renderComplete) {{
                        // 额外等待 2 秒确保完全渲染
                        setTimeout(function() {{
                            loadingEl.classList.remove('active');
                            document.getElementById('mermaid-render-complete').style.display = 'block';
                            renderComplete = true;
                            clearInterval(checkRender);
                        }}, 2000);
                    }}
                }}
            }}, 100);

            // 超时保护：90 秒后强制完成（与 --javascript-delay 匹配）
            setTimeout(function() {{
                if (!renderComplete) {{
                    loadingEl.classList.remove('active');
                    document.getElementById('mermaid-render-complete').style.display = 'block';
                    clearInterval(checkRender);
                }}
            }}, 90000);
        }})();
    </script>
</body>
</html>"""
    html = iphone_style_template.format(title=title, code=code)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ============================================================
# 步骤 3：HTML → 图片（使用 Cursor Browser Extension）
# ============================================================

def html_to_image(html_path: Path, output_path: Path, verbose: bool = False):
    """使用 Cursor Browser Extension 的 browser 工具将 HTML 转换为图片

    注意：此函数需要在 Cursor 对话环境中调用 browser 工具
    实际的工具调用由 AI 在对话中完成
    """

    if verbose:
        print(f"  使用 browser 工具截图: {html_path.name}")
        print(f"  输出: {output_path.name}")
        print(f"  注意: 需要在 Cursor 对话中使用 browser 工具")

    # 生成 browser 工具调用指令
    html_abs = html_path.absolute()
    file_url = f"file://{html_abs}"

    instruction = f"""请使用 Cursor Browser Extension 的 browser 工具，帮我截图以下 HTML 文件：

**HTML 文件**: `{file_url}`
**输出文件**: `{output_path}`

**操作步骤**:
1. 使用 browser_navigate 工具导航到: `{file_url}`
2. 使用 browser_wait_for 工具等待元素出现:
   - selector: `.mermaid svg`
   - timeout: 10000
3. 等待 2-3 秒确保 Mermaid 动画完成
4. 使用 browser_take_screenshot 工具截图:
   - filename: `{output_path.name}`
   - type: `png`
   - fullPage: false
   - ref: `.card` (可选，截取卡片容器)

请开始截图并告知结果。"""

    if verbose:
        print(f"  生成的指令已包含在任务清单中")

    # 返回 False，表示需要手动调用 browser 工具
    # 注意：只使用 Cursor Browser Extension，不使用任何备选方案
    return False


# ============================================================
# 步骤 4：替换 Markdown 中的 Mermaid 为图片
# ============================================================

def replace_mermaid_in_markdown(content: str, image_dir: Path,
                                 image_files: List[Path]) -> str:
    """替换 Mermaid 代码块为图片引用"""
    lines = content.split('\n')
    blocks = []

    # 找到所有 mermaid 块
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('```mermaid'):
            start = i
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                i += 1
            end = i
            blocks.append((start, end))
        i += 1

    # 从后往前替换
    for idx, (start, end) in enumerate(reversed(blocks)):
        img_idx = len(blocks) - 1 - idx
        if img_idx < len(image_files):
            img_file = image_files[img_idx]
            rel_path = str(img_file.relative_to(image_dir.parent)) if image_dir.parent in img_file.parents else img_file.name

            # 获取标题
            title = "Mermaid Diagram"
            for j in range(start - 1, max(0, start - 5), -1):
                if lines[j].strip().startswith('#'):
                    title = lines[j].strip().lstrip('#').strip()
                    break

            # 保留原始代码在折叠区域
            original_code = '\n'.join(lines[start:end+1])
            replacement = [
                f"![{title}]({rel_path})",
                "",
                "<details>",
                "<summary>查看 Mermaid 源码</summary>",
                "",
                original_code,
                "",
                "</details>",
                ""
            ]

            lines[start:end+1] = replacement

    return '\n'.join(lines)


# ============================================================
# 步骤 5：Markdown → PDF
# ============================================================

def markdown_to_pdf(md_path: Path, pdf_path: Path, verbose: bool = False):
    """使用 pandoc + wkhtmltopdf 将 Markdown 转换为 PDF"""

    # 方案 1: 使用 pandoc
    pandoc = shutil.which('pandoc')
    if pandoc:
        cmd = [
            pandoc,
            str(md_path),
            '-o', str(pdf_path),
            '--pdf-engine=wkhtmltopdf',
            '-V', 'mainfont=WenQuanYi Micro Hei',
            '-V', 'geometry:margin=2cm',
            '--standalone',
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                if verbose:
                    print(f"✓ PDF 已生成: {pdf_path}")
                return True
            else:
                if verbose:
                    print(f"Pandoc 方案失败: {result.stderr[:200]}")
        except Exception as e:
            if verbose:
                print(f"Pandoc 方案异常: {e}")

    # 方案 2: 使用 Python markdown + wkhtmltopdf
    try:
        import markdown

        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 转换为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        # 包装为完整 HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: sans-serif; margin: 2cm; line-height: 1.6; }}
h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
h2 {{ color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
h3 {{ color: #666; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f8f8f8; }}
img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; }}
details {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
summary {{ cursor: pointer; font-weight: bold; color: #555; }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""

        # 保存临时 HTML
        temp_html = md_path.with_suffix('.tmp.html')
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(full_html)

        # 使用 wkhtmltopdf 转换
        wkhtmltopdf = shutil.which('wkhtmltopdf')
        if wkhtmltopdf:
            cmd = [
                wkhtmltopdf,
                '--quiet',
                '--enable-local-file-access',
                '--encoding', 'UTF-8',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--margin-right', '20mm',
                str(temp_html),
                str(pdf_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # 清理临时文件
            temp_html.unlink(missing_ok=True)

            if result.returncode == 0 or pdf_path.exists():
                if verbose:
                    print(f"✓ PDF 已生成: {pdf_path}")
                return True
            else:
                if verbose:
                    print(f"wkhtmltopdf 失败: {result.stderr[:200]}")

        # 清理
        temp_html.unlink(missing_ok=True)

    except ImportError:
        if verbose:
            print("需要安装 markdown 库: pip install markdown")
    except Exception as e:
        if verbose:
            print(f"PDF 生成失败: {e}")

    return False


# ============================================================
# 步骤 6：完整流水线
# ============================================================

def full_pipeline(input_md: Path, output_dir: Path, verbose: bool = True):
    """
    完整流水线：Mermaid → HTML → 图片 → 替换 → PDF
    """
    print("=" * 60)
    print("  Mermaid 全自动处理流水线")
    print("=" * 60)
    print()

    # 创建输出目录
    html_dir = output_dir / 'html'
    img_dir = output_dir / 'images'
    html_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    # 读取 Markdown
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # 步骤 1: 提取 Mermaid
    print("[1/5] 提取 Mermaid 代码块...")
    blocks = extract_mermaid_blocks(content)
    print(f"  ✓ 找到 {len(blocks)} 个 Mermaid 代码块")
    print()

    if not blocks:
        print("  ⚠️ 未找到 Mermaid 代码块，跳过图片生成")
        print()

    # 步骤 2: 生成 HTML
    print("[2/5] 生成 HTML 文件...")
    html_files = []
    for idx, (title, code, line) in enumerate(blocks, 1):
        safe_title = re.sub(r'[^\w\s-]', '', title)[:30]
        safe_title = re.sub(r'[\s]+', '-', safe_title)
        html_file = html_dir / f"mermaid-{idx:02d}-{safe_title}.html"
        generate_mermaid_html(title, code, html_file)
        html_files.append(html_file)
        if verbose:
            print(f"  ✓ [{idx}/{len(blocks)}] {html_file.name}")
    print()

    # 步骤 3: HTML → 图片（使用 Cursor Browser Extension）
    print("[3/5] 生成图片（使用 Cursor Browser Extension）...")
    image_files = []
    success_count = 0

    print("  ℹ️ 使用 Cursor Browser Extension 的 browser 工具截图")
    print("  ℹ️ 将在 Cursor 对话中使用 browser 工具")
    print()

    # 生成 browser 工具任务清单
    print("  请使用以下指令在 Cursor 对话中使用 browser 工具：")
    print()
    print("  " + "=" * 66)
    print("  请使用 Cursor Browser Extension 的 browser 工具，帮我批量截图以下 HTML 文件：")
    print()

    for idx, html_file in enumerate(html_files, 1):
        img_file = img_dir / html_file.with_suffix('.png').name
        html_abs = html_file.absolute()
        file_url = f"file://{html_abs}"

        print(f"  ### 文件 {idx}/{len(html_files)}: {html_file.name}")
        print(f"  **HTML**: `{file_url}`")
        print(f"  **输出**: `{img_file}`")
        print()

        image_files.append(img_file)  # 添加到列表，等待截图

    print("  " + "=" * 66)
    print()
    print("  ⚠️ 注意: 需要在 Cursor 对话中使用 browser 工具完成截图")
    print(f"  ⚠️ 截图完成后，请验证图片文件是否已生成在: {img_dir}")
    print()

    # 暂时标记为未完成，等待 webshot-mcp 截图
    success_count = 0
    print(f"  ⚠️ 等待 browser 工具截图完成（0/{len(blocks)} 个图片）")
    print()

    # 步骤 4: 替换 Markdown
    print("[4/5] 更新 Markdown（替换 Mermaid 为图片引用）...")
    # 检查图片文件是否存在
    valid_images = [f for f in image_files if f.exists()]

    if valid_images:
        new_content = replace_mermaid_in_markdown(content, img_dir, valid_images)
        output_md = output_dir / input_md.name
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ 已保存: {output_md}")
    else:
        output_md = input_md
        print("  ⚠️ 无图片可替换，使用原始文档")
    print()

    # 步骤 5: 导出 PDF
    print("[5/5] 导出 PDF...")
    pdf_path = output_dir / input_md.with_suffix('.pdf').name

    if markdown_to_pdf(output_md if valid_images else input_md, pdf_path, verbose):
        print(f"  ✓ PDF 已生成: {pdf_path}")
        print(f"  ✓ 文件大小: {pdf_path.stat().st_size / 1024:.1f} KB")
    else:
        print("  ⚠️ PDF 生成失败，请手动导出")

    print()
    print("=" * 60)
    print("  完成！")
    print("=" * 60)
    print()
    print(f"输出目录: {output_dir}")
    print(f"├── html/     ({len(html_files)} 个 HTML 文件)")
    print(f"├── images/   ({success_count} 个图片文件)")
    if valid_images:
        print(f"├── {output_md.name}")
    if pdf_path.exists():
        print(f"└── {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")
    print()


def create_mermaid_svg_placeholder(title: str, code: str, index: int) -> str:
    """创建 Mermaid SVG 占位符（当无法渲染时）"""
    # 简单的 SVG 占位符，显示代码文本
    escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    lines = escaped_code.split('\n')
    text_lines = '\n'.join(
        f'<text x="20" y="{40 + i * 18}" font-size="12" fill="#333">{line}</text>'
        for i, line in enumerate(lines[:30])  # 最多显示 30 行
    )

    height = min(40 + len(lines) * 18 + 20, 600)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}">
  <rect width="100%" height="100%" fill="#f8f9fa" rx="8"/>
  <rect x="10" y="10" width="780" height="30" fill="#e9ecef" rx="4"/>
  <text x="400" y="30" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">
    {title} (Mermaid Diagram #{index})
  </text>
  <rect x="10" y="45" width="780" height="{height - 55}" fill="white" rx="4" stroke="#dee2e6"/>
  <g font-family="monospace">
    {text_lines}
  </g>
</svg>"""


def main():
    parser = argparse.ArgumentParser(
        description='Mermaid 全自动处理流水线: Markdown → HTML → 图片 → PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基本用法
  python mermaid_full_pipeline.py document.md

  # 指定输出目录
  python mermaid_full_pipeline.py document.md -o output/

  # 只生成 PDF（不替换 Mermaid）
  python mermaid_full_pipeline.py document.md --pdf-only

  # 详细模式
  python mermaid_full_pipeline.py document.md -v
        """
    )
    parser.add_argument('input', help='输入 Markdown 文件')
    parser.add_argument('-o', '--output', default=None, help='输出目录（默认: 输入文件名_output）')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--pdf-only', action='store_true', help='只生成 PDF，不处理 Mermaid')

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"错误：文件不存在 {input_path}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_output"

    if args.pdf_only:
        # 只生成 PDF
        pdf_path = output_dir / input_path.with_suffix('.pdf').name
        output_dir.mkdir(parents=True, exist_ok=True)
        print("生成 PDF...")
        if markdown_to_pdf(input_path, pdf_path, verbose=True):
            print(f"✓ PDF 已生成: {pdf_path}")
        else:
            print("✗ PDF 生成失败")
    else:
        # 完整流水线
        full_pipeline(input_path, output_dir, verbose=args.verbose or True)


if __name__ == '__main__':
    main()
