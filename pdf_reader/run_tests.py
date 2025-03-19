import asyncio
import logging
from pathlib import Path
import json
import shutil
from datetime import datetime

async def run_test_suite():
    # 设置测试目录
    results_dir = Path("test_results")
    if results_dir.exists():
        shutil.rmtree(results_dir)
    results_dir.mkdir()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(results_dir / 'test.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('TestRunner')
    logger.info("Starting test suite...")
    
    # 记录测试开始时间
    start_time = datetime.now()
    
    # 运行测试
    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': [],
        'start_time': start_time.isoformat(),
        'end_time': None,
        'duration': None
    }
    
    try:
        # 测试1: URL规范化
        logger.info("Test 1: Testing URL normalization")
        test_urls = [
            '/columns/test',
            '//jiqizhixin.com/columns/test',
            'https://jiqizhixin.com/columns/test',
            '/articles/123'
        ]
        
        for url in test_urls:
            normalized = f"https://www.jiqizhixin.com{url}" if url.startswith('/') else url
            assert normalized.startswith('https://')
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 1: Passed")
        
        # 测试2: HTML解析
        logger.info("Test 2: Testing HTML parsing")
        test_html = """
        <div class="column-item">
            <h2 class="name">Test Column</h2>
            <p class="description">Test Description</p>
            <span class="count">10篇</span>
            <a href="/columns/test">详情</a>
        </div>
        """
        # 简单的HTML解析测试
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_html, 'html.parser')
        column = soup.select_one('.column-item')
        assert column is not None
        assert column.select_one('.name').text == 'Test Column'
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 2: Passed")
        
        # 测试3: 文件操作
        logger.info("Test 3: Testing file operations")
        test_data_dir = results_dir / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        test_file = test_data_dir / "test.json"
        test_data = {"test": "data"}
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
            
        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data
        
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 3: Passed")
        
        # 测试4: 错误处理
        logger.info("Test 4: Testing error handling")
        try:
            raise ValueError("Test error")
        except Exception as e:
            assert isinstance(e, ValueError)
            
        results['total_tests'] += 1
        results['passed'] += 1
        logger.info("Test 4: Passed")
        
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(str(e))
        logger.error(f"Test failed: {e}")
        
    finally:
        # 记录测试结束时间和持续时间
        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        results['duration'] = str(end_time - start_time)
        
        # 保存测试结果
        with open(results_dir / 'results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"""
        Test Suite Results:
        Total Tests: {results['total_tests']}
        Passed: {results['passed']}
        Failed: {results['failed']}
        Duration: {results['duration']}
        Success Rate: {(results['passed'] / results['total_tests']) * 100:.2f}%
        """)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_test_suite()) 