import asyncio
import logging
from tests.test_basic_scraper import run_article_test
from pathlib import Path

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行文章抓取测试
    result = await run_article_test()
    
    if result['success']:
        print(f"\nSuccessfully scraped {result['articles_count']} articles!")
        
        # 打印保存路径
        data_dir = Path("data/basic_articles")
        print("\nResults saved in:")
        print(f"1. Articles JSON: {list(data_dir.glob('articles_*.json'))[-1]}")
        print(f"2. Images: {data_dir}/images/")
        print(f"3. Log file: test_results/article_scraper.log")
    else:
        print(f"\nFailed to scrape articles: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main()) 