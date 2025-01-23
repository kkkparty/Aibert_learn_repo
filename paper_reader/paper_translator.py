import PyPDF2
import re
from typing import List, Dict, Tuple
from googletrans import Translator
import spacy
import json

class PaperTranslator:
    def __init__(self):
        # 初始化翻译器和NLP模型
        self.translator = Translator()
        self.nlp = spacy.load('en_core_web_sm')

        # 定义专业术语词典
        self.technical_terms = {
            'deep learning': '深度学习',
            'natural language processing': '自然语言处理',
            'neural network': '神经网络',
            # 可以继续添加更多术语
        }

        self.figure_pattern = re.compile(r'(Figure|Fig\.)\s*\d+.*?(?=\n\n)', re.DOTALL)

    def extract_from_pdf(self, pdf_path: str) -> List[Dict]:
        """从PDF文件提取结构化内容"""
        sections = []
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    # 解析章节结构
                    parsed_sections = self._parse_sections(text)
                    sections.extend(parsed_sections)
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return sections

    def _parse_sections(self, text: str) -> List[Dict]:
        """解析文本的章节结构"""
        sections = []
        current_section = {"level": 0, "title": "", "content": ""}

        # 使用正则表达式匹配标题
        title_pattern = r'^(\d+\.)*\d+\s+[A-Z].*$'

        for line in text.split('\n'):
            if re.match(title_pattern, line):
                # 保存当前章节
                if current_section["content"]:
                    sections.append(current_section.copy())

                # 开始新章节
                level = line.count('.')
                current_section = {
                    "level": level + 1,
                    "title": line.strip(),
                    "content": ""
                }
            else:
                current_section["content"] += line + "\n"

        # 添加最后一个章节
        if current_section["content"]:
            sections.append(current_section)

        return sections

    def translate_section(self, section: Dict) -> Dict:
        """翻译章节内容"""
        translated = section.copy()

        # 翻译标题
        title_en = section["title"]
        title_zh = self._translate_with_terms(title_en)
        translated["title_zh"] = title_zh

        # 翻译内容
        content_en = section["content"]
        content_zh = self._translate_with_terms(content_en)
        translated["content_zh"] = content_zh

        return translated

    def _translate_with_terms(self, text: str) -> str:
        """保留专业术语的翻译"""
        # 使用NLP识别专业术语
        doc = self.nlp(text)

        # 替换专业术语为占位符
        placeholders = {}
        for term in self.technical_terms:
            if term in text.lower():
                placeholder = f"__TERM_{len(placeholders)}__"
                text = text.replace(term, placeholder)
                placeholders[placeholder] = term

        # 翻译修改后的文本
        translated = self.translator.translate(text, dest='zh-cn').text

        # 恢复专业术语
        for placeholder, term in placeholders.items():
            translated = translated.replace(
                placeholder,
                f"{self.technical_terms[term]}({term})"
            )

        return translated

    def generate_markdown(self, sections: List[Dict]) -> str:
        """生成双语对照的Markdown文档"""
        markdown = ""

        for section in sections:
            # 添加标题
            level = "#" * section["level"]
            markdown += f"{level} {section['title']}\n"
            markdown += f"{level} {section['title_zh']}\n\n"

            # 添加内容
            if section["content"].strip():
                markdown += f"{section['content']}\n"
                markdown += f"{section['content_zh']}\n\n"

        return markdown

    def _extract_figures(self, text: str) -> List[Dict]:
        """提取图片及其说明"""
        figures = []
        matches = self.figure_pattern.finditer(text)

        for match in matches:
            figure_text = match.group(0)
            figures.append({
                "original": figure_text,
                "translated": self._translate_with_terms(figure_text)
            })

        return figures

    def _handle_references(self, text: str) -> Tuple[str, List[str]]:
        """处理参考文献"""
        # 分离正文和参考文献
        ref_pattern = r'References|Bibliography'
        parts = re.split(ref_pattern, text, maxsplit=1)

        if len(parts) > 1:
            content, references = parts
            # 提取参考文献条目
            ref_items = re.findall(r'\[\d+\].*?(?=\[\d+\]|\Z)', references, re.DOTALL)
            return content.strip(), [ref.strip() for ref in ref_items]

        return text.strip(), []

class TranslationCache:
    """翻译结果缓存"""
    def __init__(self, cache_file: str = "translation_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def get(self, text: str) -> str:
        return self.cache.get(text)

    def set(self, text: str, translation: str):
        self.cache[text] = translation
        self.save_cache()

class MarkdownGenerator:
    """Markdown文档生成器"""
    def __init__(self):
        self.current_section = 0

    def generate_header(self, level: int, text: str, translation: str) -> str:
        marks = "#" * level
        return f"{marks} {text}\n{marks} {translation}\n\n"

    def generate_figure(self, figure: Dict) -> str:
        return f"![{figure['translated']}]({figure['image_path']})\n\n"

    def generate_reference(self, references: List[str]) -> str:
        if not references:
            return ""

        md = "## References\n\n"
        for i, ref in enumerate(references, 1):
            md += f"{i}. {ref}\n"
        return md