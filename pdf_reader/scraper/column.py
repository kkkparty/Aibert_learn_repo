import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from pathlib import Path
import logging
from tqdm import tqdm
from .utils import setup_logger, rate_limit
from .article import ArticleScraper
import random
import re

logger = setup_logger(__name__)

class ColumnScraper:
    def __init__(self, base_url="https://www.jiqizhixin.com/columns", max_concurrency=5):
        self.base_url = base_url
        self.session = None
        self.data_dir = Path("data/columns")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.progress = None
        self.article_scraper = None

    async def init_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.article_scraper = ArticleScraper(self.session, self.data_dir)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    @rate_limit(delay=1)
    async def fetch_page(self, url, retries=3):
        async with self.semaphore:
            for attempt in range(retries):
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:  # Too Many Requests
                            await asyncio.sleep(60)  # Wait longer for rate limit
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                except Exception as e:
                    if attempt == retries - 1:
                        logger.error(f"Failed to fetch {url} after {retries} attempts: {e}")
                        return None
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            return None

    async def parse_columns(self, html):
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        columns = []
        
        # 扩展选择器以适应不同的HTML结构
        selectors = [
            '.column-item',
            '.columns-item',
            '.article-column',
            'div[class*="column"]',
            'div[class*="专栏"]'
        ]
        
        for selector in selectors:
            cols = soup.select(selector)
            if cols:
                logger.info(f"Found {len(cols)} columns using selector: {selector}")
                for col in cols:
                    try:
                        # 扩展名称选择器
                        name_selectors = [
                            '.name', '.title', 'h2', 'h3', 
                            '[class*="title"]', '[class*="name"]',
                            'a[href*="columns"]'
                        ]
                        name_elem = None
                        for name_sel in name_selectors:
                            name_elem = col.select_one(name_sel)
                            if name_elem:
                                break
                            
                        # 扩展描述选择器    
                        desc_selectors = [
                            '.description', '.desc', 'p',
                            '[class*="desc"]', '[class*="intro"]'
                        ]
                        desc_elem = None
                        for desc_sel in desc_selectors:
                            desc_elem = col.select_one(desc_sel)
                            if desc_elem:
                                break
                            
                        # 扩展文章数量选择器
                        count_selectors = [
                            '.count', '.article-count', 'span',
                            '[class*="count"]', '[class*="num"]'
                        ]
                        count_elem = None
                        for count_sel in count_selectors:
                            count_elem = col.select_one(count_sel)
                            if count_elem:
                                break
                            
                        # 扩展链接选择器
                        link_selectors = [
                            'a[href*="columns"]',
                            'a[href*="专栏"]',
                            'a[href]:not([href="#"])'
                        ]
                        link_elem = None
                        for link_sel in link_selectors:
                            link_elem = col.select_one(link_sel)
                            if link_elem:
                                break
                        
                        if not name_elem or not link_elem:
                            continue
                            
                        # 提取并清理文本
                        name = name_elem.get_text(strip=True)
                        if not name:
                            name = link_elem.get_text(strip=True)
                            
                        description = ''
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                            
                        article_count = '0篇'
                        if count_elem:
                            count_text = count_elem.get_text(strip=True)
                            # 提取数字
                            import re
                            numbers = re.findall(r'\d+', count_text)
                            if numbers:
                                article_count = f"{numbers[0]}篇"
                            
                        url = self._normalize_url(link_elem['href'])
                        
                        # 验证数据有效性
                        if len(name) > 0 and len(url) > 0:
                            column = {
                                'name': name,
                                'description': description,
                                'article_count': article_count,
                                'url': url,
                                'selector_used': selector  # 记录使用的选择器，用于调试
                            }
                            
                            # 检查是否重复
                            if not any(c['name'] == name for c in columns):
                                columns.append(column)
                                logger.debug(f"Added column: {name} using selector {selector}")
                            
                    except Exception as e:
                        logger.error(f"Error parsing column with selector {selector}: {e}")
                        continue
                    
        logger.info(f"Total columns found: {len(columns)}")
        return columns

    def _normalize_url(self, url):
        """改进的URL标准化"""
        try:
            # 处理空URL
            if not url:
                return ''
            
            # 移除首尾空白
            url = url.strip()
            
            # 处理相对路径
            if url.startswith('//'):
                return f'https:{url}'
            elif url.startswith('/'):
                return f'https://www.jiqizhixin.com{url}'
            elif not url.startswith(('http://', 'https://')):
                return f'https://www.jiqizhixin.com/{url}'
            
            # 处理特殊字符
            from urllib.parse import quote, urlparse, urlunparse
            parsed = urlparse(url)
            path = quote(parsed.path)
            return urlunparse(parsed._replace(path=path))
            
        except Exception as e:
            logger.error(f"Error normalizing URL {url}: {e}")
            return ''

    def _build_page_url(self, base_url, page):
        """构建分页URL"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(base_url)
        query_dict = parse_qs(parsed.query) if parsed.query else {}
        query_dict['page'] = [str(page)]
        new_query = urlencode(query_dict, doseq=True)
        
        return urlunparse(parsed._replace(query=new_query))

    async def get_article_list(self, column_url):
        """改进的文章列表获取"""
        article_urls = set()  # 使用集合去重
        page = 1
        consecutive_empty = 0
        max_empty_pages = 3  # 连续空页面的最大数量
        
        async def extract_article_urls(html):
            """提取文章URL的辅助函数"""
            if not html:
                return set()
            
            soup = BeautifulSoup(html, 'html.parser')
            urls = set()
            
            # 扩展文章链接选择器
            selectors = [
                '.article-item a',
                '.article-list a',
                '.article h3 a',
                'a[href*="articles"]',
                'a[href*="article"]',
                'a[href*="post"]',
                '.content a[href]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    if 'href' not in link.attrs:
                        continue
                        
                    url = self._normalize_url(link['href'])
                    # 验证是否为文章URL
                    if self._is_article_url(url):
                        urls.add(url)
                        
            return urls
        
        def get_next_page_url(html, current_page):
            """获取下一页URL的辅助函数"""
            soup = BeautifulSoup(html, 'html.parser')
            
            # 检查多种分页形式
            # 1. 标准分页链接
            next_selectors = [
                'a.next',
                '.pagination a[rel="next"]',
                'a[href*="page"][href*="next"]',
                '.pagination a:contains("下一页")',
                f'a[href*="page={current_page + 1}"]'
            ]
            
            for selector in next_selectors:
                next_link = soup.select_one(selector)
                if next_link and 'href' in next_link.attrs:
                    return self._normalize_url(next_link['href'])
                
            # 2. 检查是否有更多页面的标记
            more_selectors = [
                '.load-more',
                '.show-more',
                '[class*="more"]',
                '[class*="pagination"]'
            ]
            
            for selector in more_selectors:
                if soup.select_one(selector):
                    # 构造下一页URL
                    return self._build_page_url(column_url, current_page + 1)
                
            return None
        
        while True:
            try:
                url = self._build_page_url(column_url, page)
                logger.debug(f"Fetching article list page {page} from {url}")
                
                html = await self.fetch_page(url)
                if not html:
                    consecutive_empty += 1
                    if consecutive_empty >= max_empty_pages:
                        logger.info(f"Stopped after {consecutive_empty} empty pages")
                        break
                    continue
                
                new_urls = await extract_article_urls(html)
                if not new_urls:
                    consecutive_empty += 1
                    if consecutive_empty >= max_empty_pages:
                        logger.info(f"No more articles found after {consecutive_empty} attempts")
                        break
                else:
                    consecutive_empty = 0
                    article_urls.update(new_urls)
                    logger.debug(f"Found {len(new_urls)} articles on page {page}")
                
                next_url = get_next_page_url(html, page)
                if not next_url:
                    logger.info("No more pages found")
                    break
                
                page += 1
                # 添加随机延迟，避免请求过快
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"Error fetching article list page {page}: {e}")
                break
            
        logger.info(f"Total unique articles found: {len(article_urls)}")
        return list(article_urls)

    def _is_article_url(self, url):
        """验证URL是否为文章链接"""
        if not url:
            return False
        
        # 文章URL的特征
        article_patterns = [
            r'/articles/\d+',
            r'/posts/\d+',
            r'/\d{4}/\d{2}/\d{2}/',
            r'/article/[a-zA-Z0-9-]+',
            r'/post/[a-zA-Z0-9-]+'
        ]
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path
            
            # 检查URL模式
            return any(re.search(pattern, path) for pattern in article_patterns)
        
        except Exception:
            return False

    async def scrape_column_articles(self, column):
        """抓取专栏下的所有文章"""
        article_urls = await self.get_article_list(column['url'])
        logger.info(f"Found {len(article_urls)} articles in column {column['name']}")
        
        tasks = []
        async with asyncio.Semaphore(3) as sem:  # 限制每个专栏的并发
            for url in article_urls:
                task = asyncio.create_task(self._scrape_single_article(sem, url, column['name']))
                tasks.append(task)
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r and not isinstance(r, Exception))
        logger.info(f"Successfully scraped {success_count}/{len(article_urls)} articles in {column['name']}")
        
        # 更新专栏状态
        await self._update_column_status(column, success_count)
        
        return success_count

    async def _scrape_single_article(self, sem, url, column_name):
        """抓取单篇文章"""
        async with sem:
            try:
                html = await self.fetch_page(url)
                if not html:
                    return False
                    
                article = await self.article_scraper.parse_article(html, url)
                if not article:
                    return False
                    
                return await self.article_scraper.save_article(article, column_name)
            except Exception as e:
                logger.error(f"Error scraping article {url}: {e}")
                return False

    async def _update_column_status(self, column, article_count):
        """更新专栏状态"""
        metadata_path = self.data_dir / self._sanitize_filename(column['name']) / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            metadata['scraped_articles'] = article_count
            metadata['completed'] = article_count >= 5  # 至少5篇文章算完成
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

    async def scrape_all(self):
        """抓取所有专栏内容"""
        await self.init_session()
        try:
            html = await self.fetch_page(self.base_url)
            if not html:
                return
                
            columns = await self.parse_columns(html)
            logger.info(f"Found {len(columns)} columns")
            
            self.progress = tqdm(total=len(columns), desc="Scraping columns")
            
            tasks = []
            for column in columns:
                if await self.save_column(column):
                    task = asyncio.create_task(self.scrape_column_articles(column))
                    tasks.append(task)
                self.progress.update(1)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r and not isinstance(r, Exception))
            logger.info(f"Successfully scraped {success_count}/{len(columns)} columns")
            
            self.progress.close()
            
        finally:
            await self.close()

    def _sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()

    async def save_column(self, column):
        """保存专栏元数据"""
        col_dir = self.data_dir / self._sanitize_filename(column['name'])
        col_dir.mkdir(exist_ok=True)
        
        metadata_path = col_dir / 'metadata.json'
        
        # 检查是否已经处理过
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if existing.get('completed'):
                    logger.info(f"Skipping completed column: {column['name']}")
                    return False
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(column, f, ensure_ascii=False, indent=2)
            
        return True 