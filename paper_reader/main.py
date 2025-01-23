import argparse
import os
import PyPDF2
from tqdm import tqdm
from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator
import time

def translate_with_api(text: str) -> str:
    """使用翻译API进行翻译"""
    translators = [
        ('google', lambda: GoogleTranslator(source='en', target='zh')),
        ('mymemory', lambda: MyMemoryTranslator(source='en', target='zh')),
        ('libre', lambda: LibreTranslator(source='en', target='zh', host='https://libretranslate.de', port=443))
    ]

    for name, create_translator in translators:
        try:
            # 添加延时避免请求过快
            time.sleep(1)
            translator = create_translator()
            translated = translator.translate(text)
            if translated and isinstance(translated, str):
                print(f"Successfully translated using {name}")
                return translated
        except Exception as e:
            print(f"Translation error with {name}: {e}")
            continue

    return "[翻译失败]"

def translate_content(text: str) -> str:
    """改进的翻译函数"""
    # 专业术语词典
    terms = {
        'deep learning': '深度学习',
        'Natural Language Processing': '自然语言处理',
        'machine learning': '机器学习',
        'artificial intelligence': '人工智能',
        'neural network': '神经网络',
        'computer vision': '计算机视觉',
        'robotics': '机器人技术',
        'research': '研究',
        'paper': '论文',
        'survey': '综述',
        'analysis': '分析'
    }

    # 先尝试API翻译
    translation = translate_with_api(text)

    # 如果翻译成功，处理专业术语
    if translation != "[翻译失败]":
        # 替换专业术语
        for eng, chn in terms.items():
            # 在翻译后的文本中查找可能的错误翻译并替换
            translation = translation.replace(eng.lower(), chn)
        return translation

    # 如果API翻译失败，使用基础替换
    result = text
    for eng, chn in terms.items():
        result = result.replace(eng, f"{chn}({eng})")

    return f"{result}\n[机器翻译质量不佳，建议人工校对]"

def convert_pdf_to_markdown(pdf_path: str):
    """第一步：将PDF转换为markdown中间文件"""
    print(f"Step 1: Converting PDF to markdown")
    output_path = pdf_path.replace('.pdf', '_content.md')

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = []
            print(f"PDF loaded, pages: {len(reader.pages)}")

            for i in tqdm(range(len(reader.pages)), desc="Extracting pages"):
                text = reader.pages[i].extract_text()
                content.append(text)

            markdown_content = "# " + os.path.basename(pdf_path).replace('.pdf', '') + "\n\n"
            for text in content:
                markdown_content += text + "\n\n"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✓ Content saved to: {output_path}")
            return output_path

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def create_bilingual_markdown(input_path: str):
    """创建优化的双语对照版本"""
    print("\nStep 2: Creating bilingual version")
    output_path = input_path.replace('_content.md', '_bilingual.md')

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("✓ Original content loaded")

        sections = content.split('\n\n')
        bilingual_content = []
        section_count = 0

        # 添加文件头
        bilingual_content.extend([
            "# 双语对照翻译\n",
            "本文件包含原文与中文翻译的对照。专业术语格式：中文（English）\n",
            "*由机器翻译生成，仅供参考。如有错误，欢迎指出。*\n",
            "---\n\n"
        ])

        print("\nProcessing sections:")
        for section in tqdm(sections, desc="Translating"):
            if not section.strip():
                continue

            section_count += 1

            # 添加章节分隔线和编号
            separator = f"{'=' * 30} Section {section_count} {'=' * 30}"
            bilingual_content.extend([
                "\n\n" + separator + "\n\n"
            ])

            # 处理标题
            if section.startswith('#'):
                level = len(section) - len(section.lstrip('#'))
                title = section.lstrip('# ').strip()
                cn_title = translate_content(title)

                bilingual_content.extend([
                    f"{'#' * level} {title}",
                    f"{'#' * level} {cn_title}",
                    "\n"
                ])

            # 处理正文
            else:
                # 英文原文
                bilingual_content.extend([
                    "### Original Text（原文）",
                    f"{section.strip()}",
                    "\n"
                ])

                # 中文翻译
                bilingual_content.extend([
                    "### 中文翻译（Chinese Translation）",
                    f"{translate_content(section.strip())}",
                    "\n---\n"  # 添加分隔线
                ])

        print("\nSaving bilingual file...")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(bilingual_content))

        print(f"✓ Bilingual version saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # 执行两步转换
    print("Starting conversion process...\n")

    # 步骤1：PDF转markdown
    content_file = convert_pdf_to_markdown("agent-ai.pdf")

    if content_file:
        # 步骤2：创建双语版本
        bilingual_file = create_bilingual_markdown(content_file)

        if bilingual_file:
            print("\nConversion completed successfully!")
            print(f"1. Content file: {content_file}")
            print(f"2. Bilingual file: {bilingual_file}")