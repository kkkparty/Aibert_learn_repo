import pytest
import asyncio
import aiohttp
from pathlib import Path
import json
import shutil
from bs4 import BeautifulSoup
from scraper.column import ColumnScraper
from scraper.article import ArticleScraper

class TestFullScraper:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.test_dir = tmp_path / "test_scraper"
        self.test_dir.mkdir(exist_ok=True)
        yield
        shutil.rmtree(self.test_dir)

    @pytest.fixture
    def mock_column_response(self):
        async def mock_get(*args, **kwargs):
            class MockResponse:
                async def text(self):
                    return """
                    <div class="column-list">
                        <div class="column-item">
                            <h2 class="name">PaperWeekly</h2>
                            <p class="description">AI论文解读平台</p>
                            <span class="count">367篇</span>
                            <a href="/columns/paperweekly">详情</a>
                        </div>
                        <div class="column-item">
                            <h2 class="name">AMiner</h2>
                            <p class="description">AI学术平台</p>
                            <span class="count">257篇</span>
                            <a href="/columns/aminer">详情</a>
                        </div>
                    </div>
                    """
                @property
                def status(self):
                    return 200
            return MockResponse()
        return mock_get

    @pytest.fixture
    def mock_article_list_response(self):
        async def mock_get(*args, **kwargs):
            class MockResponse:
                async def text(self):
                    return """
                    <div class="article-list">
                        <div class="article-item">
                            <h3><a href="/articles/1">文章1</a></h3>
                        </div>
                        <div class="article-item">
                            <h3><a href="/articles/2">文章2</a></h3>
                        </div>
                    </div>
                    <div class="pagination">
                        <a href="?page=2">下一页</a>
                    </div>
                    """
                @property
                def status(self):
                    return 200
            return MockResponse()
        return mock_get

    @pytest.fixture
    def mock_article_response(self):
        async def mock_get(*args, **kwargs):
            class MockResponse:
                async def text(self):
                    return """
                    <div class="article-container">
                        <h1 class="article-title">测试文章</h1>
                        <div class="article-meta">
                            <span class="author">测试作者</span>
                            <span class="date">2024-01-01</span>
                        </div>
                        <div class="article-content">
                            <p>测试内容第一段</p>
                            <p>测试内容第二段</p>
                            <img src="test.jpg" alt="测试图片">
                        </div>
                        <div class="article-tags">
                            <span class="tag">AI</span>
                            <span class="tag">机器学习</span>
                        </div>
                    </div>
                    """
                async def read(self):
                    return b"fake image data"
                @property
                def status(self):
                    return 200
            return MockResponse()
        return mock_get

    @pytest.mark.asyncio
    async def test_full_scraping_process(self, mock_column_response, mock_article_list_response, mock_article_response):
        # 1. 初始化爬虫
        scraper = ColumnScraper(base_url="https://www.jiqizhixin.com/columns")
        scraper.data_dir = self.test_dir
        
        # 模拟session
        class MockSession:
            def __init__(self, mock_responses):
                self.mock_responses = mock_responses
                self.closed = False
                
            async def get(self, url, *args, **kwargs):
                if 'columns' in url and '/articles/' not in url:
                    return await self.mock_responses['column']()
                elif 'page=' in url:
                    return await self.mock_responses['article_list']()
                else:
                    return await self.mock_responses['article']()
                    
            async def close(self):
                self.closed = True
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.close()

        mock_session = MockSession({
            'column': mock_column_response,
            'article_list': mock_article_list_response,
            'article': mock_article_response
        })
        
        scraper.session = mock_session

        # 2. 执行爬取过程
        await scraper.scrape_all()

        # 3. 验证结果
        # 检查专栏数据
        assert (self.test_dir / "PaperWeekly").exists()
        assert (self.test_dir / "AMiner").exists()

        # 检查专栏元数据
        with open(self.test_dir / "PaperWeekly" / "metadata.json") as f:
            metadata = json.load(f)
            assert metadata['name'] == 'PaperWeekly'
            assert metadata['article_count'] == '367篇'

        # 检查文章数据
        articles_dir = self.test_dir / "PaperWeekly" / "articles"
        assert articles_dir.exists()
        article_files = list(articles_dir.glob("*.json"))
        assert len(article_files) > 0

        # 检查文章内容
        with open(article_files[0]) as f:
            article = json.load(f)
            assert article['title'] == '测试文章'
            assert article['author'] == '测试作者'
            assert article['date'] == '2024-01-01'
            assert len(article['content']) > 0
            assert len(article['tags']) == 2

        # 检查图片下载
        images_dir = self.test_dir / "images" / "PaperWeekly"
        assert images_dir.exists()
        assert len(list(images_dir.glob("*.jpg"))) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_column_response):
        scraper = ColumnScraper()
        scraper.data_dir = self.test_dir

        # 模拟网络错误
        class ErrorSession:
            async def get(self, *args, **kwargs):
                raise aiohttp.ClientError("Network error")
            async def close(self):
                pass

        scraper.session = ErrorSession()
        
        # 验证错误处理
        await scraper.scrape_all()
        assert not (self.test_dir / "PaperWeekly").exists()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_column_response):
        scraper = ColumnScraper()
        scraper.data_dir = self.test_dir
        
        start_time = asyncio.get_event_loop().time()
        
        # 连续发送3个请求
        for _ in range(3):
            await scraper.fetch_page("test_url")
            
        end_time = asyncio.get_event_loop().time()
        
        # 验证请求间隔
        assert end_time - start_time >= 2

    @pytest.mark.asyncio
    async def test_data_integrity(self, mock_column_response, mock_article_response):
        scraper = ColumnScraper()
        scraper.data_dir = self.test_dir
        
        # 执行爬取
        await scraper.scrape_all()
        
        # 验证数据完整性
        def verify_data():
            # 检查专栏数据
            columns = list(self.test_dir.glob("**/metadata.json"))
            if not columns:
                return False
                
            for col_file in columns:
                with open(col_file) as f:
                    metadata = json.load(f)
                    if not all(k in metadata for k in ['name', 'description', 'article_count']):
                        return False
                        
            # 检查文章数据
            articles = list(self.test_dir.glob("**/articles/*.json"))
            if not articles:
                return False
                
            for art_file in articles:
                with open(art_file) as f:
                    article = json.load(f)
                    if not all(k in article for k in ['title', 'content', 'url']):
                        return False
                        
            return True
            
        assert verify_data()

    def test_completion_criteria(self):
        """验证完成标准"""
        # 检查专栏数量
        columns = list(self.test_dir.glob("**/metadata.json"))
        assert len(columns) >= 10, "专栏数量不足"
        
        # 检查每个专栏的文章数量
        for col_dir in self.test_dir.glob("*"):
            if col_dir.is_dir() and col_dir.name != "images":
                articles = list((col_dir / "articles").glob("*.json"))
                assert len(articles) >= 5, f"{col_dir.name} 文章数量不足"
                
        # 检查数据完整性
        for article_file in self.test_dir.glob("**/articles/*.json"):
            with open(article_file) as f:
                article = json.load(f)
                assert all(k in article for k in ['title', 'content', 'url']), \
                    f"{article_file} 数据不完整" 