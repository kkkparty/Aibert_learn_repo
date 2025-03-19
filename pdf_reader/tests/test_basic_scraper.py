import pytest
import asyncio
import logging
from pathlib import Path
import json
from bs4 import BeautifulSoup
from datetime import datetime
import aiohttp
import re
import random
import aiofiles

class ArticleContentScraper:
    def __init__(self, base_url="https://www.jiqizhixin.com"):
        self.base_url = base_url
        self.session = None
        self.data_dir = Path("data/basic_articles")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('ArticleScraper')

    async def init_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/xml, text/xml, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_page(self, url, retries=3):
        if not self.session:
            await self.init_session()
            
        for attempt in range(retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = 60 * (attempt + 1)  # 递增等待时间
                        self.logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    return None
        return None

    async def parse_article_content(self, html, url):
        """解析文章详细内容"""
        if not html:
            return None
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            article = {
                'url': url,
                'title': '',
                'author': '',
                'date': '',
                'content': '',
                'tags': [],
                'category': '',
                'images': []
            }
            
            # 提取标题
            title_selectors = [
                '.article__title',
                '.article-title',
                'h1.title',
                'h1[class*="title"]',
                'h1'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    article['title'] = title_elem.get_text(strip=True)
                    break
                    
            # 提取作者和日期
            meta_selectors = [
                '.article__meta',
                '.article-meta',
                '.meta',
                '[class*="meta"]'
            ]
            for selector in meta_selectors:
                meta = soup.select_one(selector)
                if meta:
                    # 提取作者
                    author_elem = meta.select_one('.author, [class*="author"]')
                    if author_elem:
                        article['author'] = author_elem.get_text(strip=True)
                        
                    # 提取日期
                    date_elem = meta.select_one('.date, time, [class*="date"], [class*="time"]')
                    if date_elem:
                        article['date'] = date_elem.get_text(strip=True)
                    break
                    
            # 提取正文内容
            content_selectors = [
                '.article__content',
                '.article-content',
                '[class*="article-body"]',
                '[class*="content"]',
                'article'
            ]
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除不需要的元素
                    for elem in content_elem.select('script, style, iframe, .ad, .advertisement'):
                        elem.decompose()
                        
                    # 处理图片
                    for img in content_elem.find_all('img'):
                        if 'src' in img.attrs:
                            img_url = self._normalize_url(img['src'])
                            if img_url not in article['images']:
                                article['images'].append(img_url)
                                # 替换图片为标记
                                img.replace_with(f'[图片: {img_url}]')
                                
                    # 处理代码块
                    for pre in content_elem.find_all('pre'):
                        pre.string = f"\n```\n{pre.get_text(strip=True)}\n```\n"
                        
                    # 处理链接
                    for a in content_elem.find_all('a'):
                        if 'href' in a.attrs:
                            href = self._normalize_url(a['href'])
                            text = a.get_text(strip=True)
                            if text and href != text:
                                a.replace_with(f"{text} ({href})")
                            else:
                                a.replace_with(href)
                                
                    # 获取清理后的文本
                    article['content'] = content_elem.get_text(separator='\n', strip=True)
                    # 移除多余的空行
                    article['content'] = re.sub(r'\n{3,}', '\n\n', article['content'])
                    break
                    
            # 提取标签
            tag_selectors = [
                '.article__tags .tag',
                '.tags .tag',
                '[class*="tag"]'
            ]
            for selector in tag_selectors:
                tags = soup.select(selector)
                if tags:
                    article['tags'] = [tag.get_text(strip=True) for tag in tags]
                    break
                    
            # 提取分类
            category_selectors = [
                '.article__category',
                '.category',
                '[class*="category"]'
            ]
            for selector in category_selectors:
                category_elem = soup.select_one(selector)
                if category_elem:
                    article['category'] = category_elem.get_text(strip=True)
                    break
                    
            # 验证必要字段
            if not article['title'] or not article['content']:
                self.logger.warning(f"Missing required fields for {url}")
                return None
                
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing article content for {url}: {e}")
            self.logger.exception(e)
            return None

    async def get_article_list(self, max_articles=10):
        """从RSS源获取文章列表"""
        all_articles = []
        
        if not self.session:
            await self.init_session()
            
        try:
            # 获取RSS源
            url = f"{self.base_url}/rss"
            self.logger.info(f"Fetching RSS feed from {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    try:
                        content = await response.text()
                        
                        # 保存响应以供调试
                        debug_file = self.data_dir / 'rss_feed.xml'
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        # 解析RSS内容
                        soup = BeautifulSoup(content, 'xml')
                        
                        # 获取所有文章条目
                        items = soup.find_all('item')
                        self.logger.info(f"Found {len(items)} articles in RSS feed")
                        
                        # 提取文章URL
                        for item in items:
                            link = item.find('link')
                            if link and link.text:
                                article_url = link.text.strip()
                                if self._is_valid_article_url(article_url) and article_url not in all_articles:
                                    all_articles.append(article_url)
                                    if len(all_articles) >= max_articles:
                                        break
                                        
                    except Exception as e:
                        self.logger.error(f"Failed to parse RSS feed: {e}")
                        self.logger.exception(e)
                        
                else:
                    self.logger.error(f"HTTP {response.status} for {url}")
                    # 保存错误响应以供调试
                    try:
                        error_response = await response.text()
                        debug_file = self.data_dir / 'rss_error.txt'
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(error_response)
                    except Exception:
                        pass
                        
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed: {e}")
            self.logger.exception(e)
            
        self.logger.info(f"Total unique articles found: {len(all_articles)}")
        return all_articles

    def _is_valid_article_url(self, url):
        """验证是否为有效的文章URL"""
        if not url:
            return False
            
        # 文章URL模式
        patterns = [
            r'/articles/\d+',
            r'/article/[\w-]+',
            r'/post/[\w-]+',
            r'/\d{4}/\d{2}/[\w-]+',
            r'/p/[\w-]+',
            r'/posts/[\w-]+'
        ]
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            
            # 检查URL模式
            return any(re.search(pattern, path) for pattern in patterns)
            
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return False

    async def scrape_articles(self, num_articles=10):
        """抓取指定数量的文章"""
        try:
            # 获取文章列表
            article_urls = await self.get_article_list()
            if not article_urls:
                self.logger.error("No articles found")
                return []
                
            # 限制文章数量
            article_urls = article_urls[:num_articles]
            self.logger.info(f"Preparing to scrape {len(article_urls)} articles")
            
            # 创建信号量控制并发
            sem = asyncio.Semaphore(3)
            
            async def scrape_single_article(url):
                async with sem:
                    self.logger.info(f"Scraping article: {url}")
                    html = await self.fetch_page(url)
                    if html:
                        article = await self.parse_article_content(html, url)
                        if article:
                            return article
                    return None
                    
            # 并发抓取文章
            tasks = [scrape_single_article(url) for url in article_urls]
            articles = await asyncio.gather(*tasks)
            
            # 过滤掉失败的结果
            articles = [a for a in articles if a]
            
            # 保存结果
            if articles:
                await self.save_articles(articles)
                
            return articles
            
        except Exception as e:
            self.logger.error(f"Error in scrape_articles: {e}")
            return []

    def _normalize_url(self, url):
        """标准化URL"""
        if not url:
            return ''
            
        url = url.strip()
        if url.startswith('//'):
            return f'https:{url}'
        elif url.startswith('/'):
            return f'https://www.jiqizhixin.com{url}'
        elif not url.startswith(('http://', 'https://')):
            return f'https://www.jiqizhixin.com/{url}'
            
        return url

    async def save_articles(self, articles):
        """保存文章内容和图片"""
        try:
            # 保存文章内容
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.data_dir / f'articles_{timestamp}.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved {len(articles)} articles to {output_file}")
            
            # 下载图片
            image_dir = self.data_dir / 'images'
            image_dir.mkdir(exist_ok=True)
            
            async def download_image(url):
                try:
                    # 生成安全的文件名
                    filename = re.sub(r'[^\w\-.]', '_', url.split('/')[-1])
                    image_path = image_dir / filename
                    
                    if image_path.exists():
                        return
                        
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            async with aiofiles.open(image_path, 'wb') as f:
                                await f.write(content)
                                
                except Exception as e:
                    self.logger.error(f"Error downloading image {url}: {e}")
                    
            # 收集所有图片URL
            image_urls = set()
            for article in articles:
                image_urls.update(article['images'])
                
            # 并发下载图片
            tasks = []
            async with asyncio.Semaphore(5) as sem:  # 限制并发数
                for url in image_urls:
                    task = asyncio.create_task(download_image(url))
                    tasks.append(task)
                    
            await asyncio.gather(*tasks)
            self.logger.info(f"Downloaded {len(image_urls)} images")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving articles: {e}")
            self.logger.exception(e)
            return None

async def run_article_test():
    """运行文章抓取测试"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_results/article_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('ArticleTest')
    logger.info("Starting article scraper test...")
    
    try:
        scraper = ArticleContentScraper()
        articles = await scraper.scrape_articles(num_articles=10)
        
        if not articles:
            logger.error("No articles scraped")
            return {
                'success': False,
                'error': 'No articles found',
                'articles_count': 0
            }
            
        # 验证文章内容
        valid_articles = []
        for article in articles:
            if all(article.get(field) for field in ['title', 'content', 'url']):
                valid_articles.append(article)
                
        success = len(valid_articles) >= 10
        
        logger.info(f"""
        Test Results:
        Total articles scraped: {len(articles)}
        Valid articles: {len(valid_articles)}
        Success: {success}
        """)
        
        # 输出前5篇文章的信息
        logger.info("\nFirst 5 articles details:")
        for i, article in enumerate(valid_articles[:5], 1):
            logger.info(f"\n{i}. Title: {article['title']}")
            logger.info(f"   URL: {article['url']}")
            logger.info(f"   Date: {article['date']}")
            logger.info(f"   Content length: {len(article['content'])} chars")
            logger.info(f"   Tags: {', '.join(article['tags'])}")
            
        return {
            'success': success,
            'articles_count': len(valid_articles),
            'articles': valid_articles
        }
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'articles_count': 0
        }
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(run_article_test()) 