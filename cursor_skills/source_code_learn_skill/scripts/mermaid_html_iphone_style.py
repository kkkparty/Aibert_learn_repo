#!/usr/bin/env python3
"""
生成 iPhone 风格的美化 Mermaid HTML 文件
参考 iPhone 设计理念：简洁、优雅、大量留白、柔和阴影
"""

import re
from pathlib import Path


IPHONE_STYLE_TEMPLATE = """<!DOCTYPE html>
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

        /* Mermaid 图表样式优化 */
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}

        /* 渲染完成标记 */
        #mermaid-render-complete {{
            display: none;
        }}

        /* 加载动画 */
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

        /* 响应式设计 */
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

        /* 打印样式 */
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .card {{
                box-shadow: none;
                border-radius: 0;
                padding: 20px;
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
                // iPhone 风格颜色
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
                // 优化字体
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

        // 等待渲染完成后隐藏加载动画
        (function() {{
            var loadingEl = document.getElementById('loading');
            var renderComplete = false;

            var checkRender = setInterval(function() {{
                var svg = document.querySelector('.mermaid svg');
                if (svg && svg.children.length > 0 && !renderComplete) {{
                    loadingEl.classList.remove('active');
                    document.getElementById('mermaid-render-complete').style.display = 'block';
                    renderComplete = true;
                    clearInterval(checkRender);
                }}
            }}, 100);

            // 超时保护：15秒后强制完成
            setTimeout(function() {{
                if (!renderComplete) {{
                    loadingEl.classList.remove('active');
                    document.getElementById('mermaid-render-complete').style.display = 'block';
                    clearInterval(checkRender);
                }}
            }}, 15000);
        }})();
    </script>
</body>
</html>"""


def extract_title_from_code(code: str, default: str = "Mermaid Diagram") -> str:
    """从 Mermaid 代码中提取标题"""
    # 尝试从 gantt 图表提取
    match = re.search(r'title\s+([^\n]+)', code, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 尝试从其他图表类型提取
    lines = code.split('\n')
    for line in lines[:5]:
        if line.strip() and not line.strip().startswith(('graph', 'flowchart', 'sequence', 'state', 'class')):
            return line.strip()[:50]

    return default


def generate_iphone_style_html(title: str, code: str, output_path: Path):
    """生成 iPhone 风格的 HTML 文件"""
    # 如果标题是默认值，尝试从代码中提取
    if title == "diagram" or title == "Mermaid Diagram":
        title = extract_title_from_code(code, title)

    html = IPHONE_STYLE_TEMPLATE.format(title=title, code=code)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成 iPhone 风格的 Mermaid HTML")
    parser.add_argument("input", help="输入 Markdown 文件或 Mermaid 代码文件")
    parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("-t", "--title", default="Mermaid Diagram", help="图表标题")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.suffix == '.md':
        # 从 Markdown 提取 Mermaid 代码
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取第一个 Mermaid 代码块
        match = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            print("错误: 未找到 Mermaid 代码块")
            return
    else:
        # 直接读取代码文件
        with open(input_path, 'r', encoding='utf-8') as f:
            code = f.read().strip()

    generate_iphone_style_html(args.title, code, output_path)
    print(f"✓ 已生成: {output_path}")


if __name__ == "__main__":
    main()
