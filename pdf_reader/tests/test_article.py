import pytest
from scraper.article import ArticleScraper
from bs4 import BeautifulSoup

@pytest.fixture
def sample_article_html():
    return """
    <div class="article-container">
        <h1 class="article-title">测试文章标题</h1>
        <div class="article-meta">
            <span class="author">作者名</span>
            <span class="date">2024-01-01</span>
        </div>
        <div class="article-content">
            <p>第一段内容</p>
            <p>第二段内容</p>
            <img src="test.jpg" alt="测试图片">
            <pre><code>代码块内容</code></pre>
        </div>
        <div class="article-tags">
            <span class="tag">标签1</span>
            <span class="tag">标签2</span>
        </div>
    </div>
    """

@pytest.mark.asyncio
async def test_article_parsing(sample_article_html):
    scraper = ArticleScraper(None, "test_data")
    article = await scraper.parse_article(sample_article_html, "test_url")
    
    assert article['title'] == '测试文章标题'
    assert article['author'] == '作者名'
    assert article['date'] == '2024-01-01'
    assert len(article['content']) > 0
    assert len(article['tags']) == 2
    assert article['images'] == ['test.jpg']

@pytest.mark.asyncio
async def test_article_save(tmp_path):
    scraper = ArticleScraper(None, tmp_path)
    article = {
        'title': '测试文章',
        'content': '测试内容',
        'url': 'test_url'
    }
    
    await scraper.save_article(article, 'test_column')
    
    saved_path = tmp_path / 'test_column' / 'articles' / '测试文章.json'
    assert saved_path.exists() 