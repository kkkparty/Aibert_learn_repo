import asyncio
import functools
import logging
import structlog
from datetime import datetime

def setup_logger(name):
    """设置结构化日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'test_results/article_scraper.log')
        ]
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return logging.getLogger(name)

def rate_limit(delay=1.0):
    """请求速率限制装饰器"""
    def decorator(func):
        last_call_time = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取上次调用时间
            key = id(func)
            if key in last_call_time:
                elapsed = datetime.now().timestamp() - last_call_time[key]
                if elapsed < delay:
                    await asyncio.sleep(delay - elapsed)
                    
            result = await func(*args, **kwargs)
            last_call_time[key] = datetime.now().timestamp()
            return result
            
        return wrapper
    return decorator 