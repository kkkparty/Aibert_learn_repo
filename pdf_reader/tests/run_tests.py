import pytest
import asyncio
import logging
from pathlib import Path
import json
import shutil
from scraper.column import ColumnScraper
from scraper.article import ArticleScraper

async def run_test_suite():
    # 设置测试目录
    test_dir = Path("test_results")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(test_dir / 'test.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('TestRunner')
    logger.info("Starting test suite...")
    
    # 运行测试
    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # 测试1: 基本初始化
        logger.info("Test 1: Testing initialization")
        scraper = ColumnScraper()
        await scraper.init_session()
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 1: Passed")
        
        # 测试2: URL规范化
        logger.info("Test 2: Testing URL normalization")
        test_urls = [
            '/columns/test',
            '//jiqizhixin.com/columns/test',
            'https://jiqizhixin.com/columns/test',
            '/articles/123'
        ]
        
        for url in test_urls:
            normalized = scraper._normalize_url(url)
            assert normalized.startswith('https://')
            
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 2: Passed")
        
        # 测试3: HTML解析
        logger.info("Test 3: Testing HTML parsing")
        test_html = """
        <div class="column-item">
            <h2 class="name">Test Column</h2>
            <p class="description">Test Description</p>
            <span class="count">10篇</span>
            <a href="/columns/test">详情</a>
        </div>
        """
        columns = await scraper.parse_columns(test_html)
        assert len(columns) > 0
        assert columns[0]['name'] == 'Test Column'
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 3: Passed")
        
        # 测试4: 文章URL验证
        logger.info("Test 4: Testing article URL validation")
        test_article_urls = [
            'https://jiqizhixin.com/articles/123',
            'https://jiqizhixin.com/posts/456',
            'https://jiqizhixin.com/invalid'
        ]
        
        valid_count = sum(1 for url in test_article_urls if scraper._is_article_url(url))
        assert valid_count == 2
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 4: Passed")
        
        # 测试5: 文件保存
        logger.info("Test 5: Testing file saving")
        test_column = {
            'name': 'Test Column',
            'description': 'Test Description',
            'article_count': '10篇',
            'url': 'https://jiqizhixin.com/columns/test'
        }
        
        saved = await scraper.save_column(test_column)
        assert saved
        assert (scraper.data_dir / 'Test Column' / 'metadata.json').exists()
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 5: Passed")
        
        # 测试6: 错误处理
        logger.info("Test 6: Testing error handling")
        result = await scraper.fetch_page('https://invalid.url')
        assert result is None
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 6: Passed")
        
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(str(e))
        logger.error(f"Test failed: {e}")
        
    finally:
        await scraper.close()
        
    # 保存测试结果
    with open(test_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"""
    Test Suite Results:
    Total Tests: {results['total_tests']}
    Passed: {results['passed']}
    Failed: {results['failed']}
    Success Rate: {(results['passed'] / results['total_tests']) * 100:.2f}%
    """)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_test_suite()) 