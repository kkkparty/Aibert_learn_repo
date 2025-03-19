import pytest
import aiohttp
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from scraper.column import ColumnScraper
from scraper.article import ArticleScraper

@pytest.fixture
def sample_column_html():
    return """
    <div class="column-list">
        <div class="column-item">
            <h2 class="name">PaperWeekly</h2>
            <p class="description">AI论文解读</p>
            <span class="count">100篇</span>
            <a href="/columns/paperweekly">查看详情</a>
        </div>
        <div class="column-item">
            <h2 class="name">AMiner</h2> 
            <p class="description">AI科技动态</p>
            <span class="count">50篇</span>
            <a href="/columns/aminer">查看详情</a>
        </div>
    </div>
    """

@pytest.fixture
def sample_article_html():
    return """
    <div class="article">
        <h1 class="title">测试文章</h1>
        <div class="content">
            <p>这是测试内容</p>
        </div>
    </div>
    """

@pytest.fixture
async def mock_session(sample_column_html, sample_article_html):
    async def mock_get(url):
        response = Mock()
        if 'columns' in url:
            response.text.return_value = sample_column_html
        else:
            response.text.return_value = sample_article_html
        return response
    
    session = Mock()
    session.get = mock_get
    return session

@pytest.mark.asyncio
async def test_parse_columns(sample_column_html):
    scraper = ColumnScraper()
    columns = await scraper.parse_columns(sample_column_html)
    
    assert len(columns) == 2
    assert columns[0]['name'] == 'PaperWeekly'
    assert columns[0]['description'] == 'AI论文解读'
    assert columns[0]['article_count'] == '100篇'
    assert columns[0]['url'] == '/columns/paperweekly'

@pytest.mark.asyncio 
async def test_save_column(tmp_path):
    scraper = ColumnScraper()
    scraper.data_dir = tmp_path
    
    column = {
        'name': 'test_column',
        'description': 'test description',
        'article_count': '10篇',
        'url': '/test'
    }
    
    await scraper.save_column(column)
    
    saved_path = tmp_path / 'test_column' / 'metadata.json'
    assert saved_path.exists()

@pytest.mark.asyncio
async def test_scrape_all(mock_session, tmp_path):
    scraper = ColumnScraper()
    scraper.session = mock_session
    scraper.data_dir = tmp_path
    
    await scraper.scrape_all()
    
    # 验证是否创建了相应的目录和文件
    assert (tmp_path / 'PaperWeekly').exists()
    assert (tmp_path / 'AMiner').exists()
    assert (tmp_path / 'PaperWeekly' / 'metadata.json').exists()

@pytest.mark.asyncio
async def test_error_handling():
    scraper = ColumnScraper()
    
    # 测试网络错误
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = aiohttp.ClientError
        
        await scraper.init_session()
        result = await scraper.fetch_page('http://test.com')
        assert result is None

@pytest.mark.asyncio
async def test_rate_limiting():
    scraper = ColumnScraper()
    await scraper.init_session()
    
    start_time = asyncio.get_event_loop().time()
    
    # 连续发送3个请求
    for _ in range(3):
        await scraper.fetch_page('http://test.com')
    
    end_time = asyncio.get_event_loop().time()
    
    # 验证是否遵守了延迟设置
    assert end_time - start_time >= 2  # 至少2秒延迟 