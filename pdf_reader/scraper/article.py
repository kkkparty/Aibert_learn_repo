import asyncio
import json
from pathlib import Path
import logging
from bs4 import BeautifulSoup
import aiofiles
import aiohttp
from .utils import rate_limit, setup_logger

logger = setup_logger(__name__)

class ArticleScraper:
    def __init__(self, session, data_dir):
        self.session = session
        self.data_dir = Path(data_dir)
        self.image_dir = self.data_dir / 'images'
        self.image_dir.mkdir(exist_ok=True)

    async def parse_article(self, html, url):
        """解析文章HTML内容"""
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        article = {
            'url': url,
            'title': '',
            'author': '',
            'date': '',
            'content': '',
            'tags': [],
            'images': []
        }
        
        try:
            # 提取标题
            title_elem = soup.select_one('.article-title')
            if title_elem:
                article['title'] = title_elem.text.strip()
                
            # 提取作者和日期
            meta = soup.select_one('.article-meta')
            if meta:
                author_elem = meta.select_one('.author')
                date_elem = meta.select_one('.date')
                if author_elem:
                    article['author'] = author_elem.text.strip()
                if date_elem:
                    article['date'] = date_elem.text.strip()
                    
            # 提取正文内容
            content_elem = soup.select_one('.article-content')
            if content_elem:
                # 处理图片
                for img in content_elem.find_all('img'):
                    if img.get('src'):
                        article['images'].append(img['src'])
                        
                # 处理代码块
                for code in content_elem.find_all('pre'):
                    code.string = f"\n```\n{code.text.strip()}\n```\n"
                    
                article['content'] = content_elem.get_text(separator='\n').strip()
                
            # 提取标签
            tags = soup.select('.article-tags .tag')
            article['tags'] = [tag.text.strip() for tag in tags]
            
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}")
            return None
            
        return article

    async def save_article(self, article, column_name):
        """保存文章数据到JSON文件"""
        article_dir = self.data_dir / column_name / 'articles'
        article_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成安全的文件名
        safe_title = self._sanitize_filename(article['title'])
        file_path = article_dir / f"{safe_title}.json"
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(article, ensure_ascii=False, indent=2))
                
            # 下载文章中的图片
            if article.get('images'):
                await self.download_images(article['images'], column_name)
                
        except Exception as e:
            logger.error(f"Error saving article {article['title']}: {e}")
            return False
            
        return True

    async def download_images(self, image_urls, column_name):
        """下载文章中的图片"""
        image_dir = self.image_dir / column_name
        image_dir.mkdir(exist_ok=True)
        
        for url in image_urls:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        image_name = url.split('/')[-1]
                        image_path = image_dir / image_name
                        
                        async with aiofiles.open(image_path, 'wb') as f:
                            await f.write(content)
            except Exception as e:
                logger.error(f"Error downloading image {url}: {e}")

    def _sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip() 