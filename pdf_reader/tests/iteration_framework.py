import asyncio
import time
import psutil
import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from scraper.column import ColumnScraper

class IterationTester:
    def __init__(self, max_iterations=100):
        self.max_iterations = max_iterations
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        self.metrics = []
        
    async def run_single_iteration(self, iteration):
        """运行单次迭代测试"""
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        scraper = ColumnScraper()
        success = False
        error_count = 0
        columns_count = 0
        articles_count = 0
        
        try:
            await scraper.scrape_all()
            
            # 验证数据完整性
            success = await self.verify_data(scraper.data_dir)
            columns_count = len(list(scraper.data_dir.glob("**/metadata.json")))
            articles_count = len(list(scraper.data_dir.glob("**/articles/*.json")))
            
        except Exception as e:
            error_count += 1
            print(f"Iteration {iteration} failed: {e}")
            
        end_time = time.time()
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            'iteration': iteration,
            'success': success,
            'duration': end_time - start_time,
            'memory_usage': memory_end - memory_start,
            'error_count': error_count,
            'columns_count': columns_count,
            'articles_count': articles_count,
            'timestamp': datetime.now().isoformat()
        }
        
    async def verify_data(self, data_dir):
        """验证爬取的数据完整性"""
        try:
            # 检查专栏数据
            for metadata_file in data_dir.glob("**/metadata.json"):
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    if not all(k in metadata for k in ['name', 'description', 'article_count', 'url']):
                        return False
                        
            # 检查文章数据
            for article_file in data_dir.glob("**/articles/*.json"):
                with open(article_file) as f:
                    article = json.load(f)
                    if not all(k in article for k in ['title', 'content', 'url']):
                        return False
                        
            return True
        except Exception:
            return False
            
    def plot_metrics(self):
        """绘制性能指标图表"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
        
        iterations = [m['iteration'] for m in self.metrics]
        durations = [m['duration'] for m in self.metrics]
        memory_usage = [m['memory_usage'] for m in self.metrics]
        success_rate = [sum(1 for m in self.metrics[:i+1] if m['success']) / (i+1) 
                       for i in range(len(self.metrics))]
        
        ax1.plot(iterations, durations)
        ax1.set_title('Execution Time per Iteration')
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Duration (s)')
        
        ax2.plot(iterations, memory_usage)
        ax2.set_title('Memory Usage per Iteration')
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Memory (MB)')
        
        ax3.plot(iterations, success_rate)
        ax3.set_title('Success Rate')
        ax3.set_xlabel('Iteration')
        ax3.set_ylabel('Success Rate')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'metrics.png')
        
    async def run_iterations(self):
        """运行所有迭代测试"""
        for i in range(self.max_iterations):
            print(f"\nStarting iteration {i+1}/{self.max_iterations}")
            
            result = await self.run_single_iteration(i+1)
            self.metrics.append(result)
            
            # 保存结果
            with open(self.results_dir / f"iteration_{i+1}.json", 'w') as f:
                json.dump(result, f, indent=2)
                
            # 每10次迭代绘制一次图表
            if (i + 1) % 10 == 0:
                self.plot_metrics()
                
            # 检查是否达到目标
            if self.check_completion_criteria():
                print(f"\nSuccess criteria met after {i+1} iterations!")
                break
                
    def check_completion_criteria(self):
        """检查是否达到完成标准"""
        if len(self.metrics) < 5:  # 需要至少5次迭代来评估
            return False
            
        recent_metrics = self.metrics[-5:]  # 最近5次迭代
        
        # 检查成功率
        success_rate = sum(1 for m in recent_metrics if m['success']) / len(recent_metrics)
        if success_rate < 0.9:  # 90%成功率
            return False
            
        # 检查数据完整性
        min_columns = 10  # 至少应该有10个专栏
        min_articles = 50  # 每个专栏至少5篇文章
        if any(m['columns_count'] < min_columns or m['articles_count'] < min_articles 
               for m in recent_metrics):
            return False
            
        # 检查性能指标
        avg_duration = sum(m['duration'] for m in recent_metrics) / len(recent_metrics)
        if avg_duration > 300:  # 平均执行时间不超过5分钟
            return False
            
        return True 