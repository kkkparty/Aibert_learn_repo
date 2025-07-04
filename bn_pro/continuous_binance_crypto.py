#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import json
from datetime import datetime, timedelta
import signal
import traceback
from pathlib import Path

# 导入核心模块
try:
    from binance_crypto_recommender import BinanceCryptoRecommender
except Exception as e:
    print(f"无法加载Binance加密货币推荐系统: {e}")
    print(traceback.format_exc())
    sys.exit(1)

# 配置日志
logger = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler()
    ]
)

# 添加文件日志处理器
try:
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建当天的日志文件
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}_binance_crypto.log"
    
    # 添加文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(file_handler)
    
    logger.info(f"日志文件: {log_file}")
except Exception as e:
    logger.warning(f"无法创建日志文件处理器: {e}")

# 全局变量
running = True
last_gc_time = time.time()

def signal_handler(sig, frame):
    """处理Ctrl+C等信号，优雅退出程序"""
    global running
    logger.info("收到退出信号，程序将在当前分析完成后退出...")
    running = False

def format_time_remaining(seconds):
    """格式化剩余时间"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}小时{int(minutes)}分钟{int(seconds)}秒"

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Binance加密货币分析系统')
    parser.add_argument('--hours', type=float, default=24, help='运行时间（小时）')
    parser.add_argument('--interval', type=int, default=60, help='分析间隔（分钟）')
    parser.add_argument('--coins', type=int, default=100, help='分析币种数量')
    parser.add_argument('--top', type=int, default=10, help='推荐币种数量')
    parser.add_argument('--cache-only', action='store_true', help='仅使用缓存数据，不发送API请求')
    parser.add_argument('--refresh-cache', action='store_true', help='强制刷新缓存')
    parser.add_argument('--use-proxies', action='store_true', help='使用代理IP')
    parser.add_argument('--mock-data', action='store_true', help='使用模拟数据进行测试')
    parser.add_argument('--use-mock-data', action='store_true', help='使用模拟数据进行测试（等同于--mock-data）')
    parser.add_argument('--force-real-api', action='store_true', help='强制使用真实API（即使检测不可用）')
    parser.add_argument('--email', type=str, default=None, help='发送结果到指定邮箱')
    parser.add_argument('--email-preset', type=int, default=1, choices=[1, 2], help='使用预设邮箱配置(1或2)')
    parser.add_argument('--btc-eth-only', action='store_true', help='仅分析BTC和ETH')
    parser.add_argument('--retry-interval', type=int, default=5, help='API请求失败重试间隔（分钟）')
    parser.add_argument('--max-retries', type=int, default=3, help='API请求最大重试次数')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                      help='日志级别: DEBUG, INFO, WARNING, ERROR')
    return parser.parse_args()

def perform_memory_management():
    """执行内存管理，清理不需要的对象"""
    global last_gc_time
    
    # 每10分钟执行一次垃圾回收
    if time.time() - last_gc_time > 600:
        logger.debug("执行内存管理...")
        try:
            import gc
            # 强制执行垃圾回收
            gc.collect()
            last_gc_time = time.time()
            logger.debug("内存管理完成")
        except Exception as e:
            logger.warning(f"内存管理失败: {e}")

def analyze_btc_eth(recommender, email_configured):
    """分析BTC和ETH"""
    logger.info("开始分析比特币(BTC)...")
    btc_analysis = None
    eth_analysis = None
    max_retries = 3
    retry_count = 0
    
    # 尝试分析BTC，带重试机制
    while retry_count < max_retries and btc_analysis is None:
        try:
            btc_analysis = recommender.analyze_single_coin('bitcoin')
            if btc_analysis:
                logger.info(f"BTC分析结果: 价格=${btc_analysis['price']:.2f}, "
                           f"24h变化={btc_analysis['price_change_24h']:.2f}%, "
                           f"RSI={btc_analysis['rsi']:.2f}, 趋势={btc_analysis['trend']}, "
                           f"建议={btc_analysis['action']}")
            else:
                logger.error("BTC分析返回空结果")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"将在5秒后重试BTC分析 ({retry_count}/{max_retries})...")
                    time.sleep(5)
        except Exception as e:
            logger.error(f"BTC分析失败: {e}")
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"将在5秒后重试BTC分析 ({retry_count}/{max_retries})...")
                time.sleep(5)
    
    # 重置重试计数
    retry_count = 0
    
    # 尝试分析ETH，带重试机制
    logger.info("开始分析以太坊(ETH)...")
    while retry_count < max_retries and eth_analysis is None:
        try:
            eth_analysis = recommender.analyze_single_coin('ethereum')
            if eth_analysis:
                logger.info(f"ETH分析结果: 价格=${eth_analysis['price']:.2f}, "
                           f"24h变化={eth_analysis['price_change_24h']:.2f}%, "
                           f"RSI={eth_analysis['rsi']:.2f}, 趋势={eth_analysis['trend']}, "
                           f"建议={eth_analysis['action']}")
            else:
                logger.error("ETH分析返回空结果")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"将在5秒后重试ETH分析 ({retry_count}/{max_retries})...")
                    time.sleep(5)
        except Exception as e:
            logger.error(f"ETH分析失败: {e}")
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"将在5秒后重试ETH分析 ({retry_count}/{max_retries})...")
                time.sleep(5)
    
    # 如果两者都分析成功，发送通知
    if btc_analysis and eth_analysis and email_configured:
        logger.info("尝试发送BTC/ETH邮件通知...")
        try:
            result = recommender.send_btc_eth_notification(btc_analysis, eth_analysis)
            logger.info(f"邮件发送结果: {'成功' if result else '失败'}")
        except Exception as e:
            logger.error(f"发送BTC/ETH邮件通知时出错: {e}")
    elif not btc_analysis or not eth_analysis:
        logger.error("由于分析失败，无法发送完整的BTC/ETH邮件通知")
    elif not email_configured:
        logger.warning("未配置邮箱，跳过BTC/ETH邮件通知")
    
    return btc_analysis, eth_analysis

def analyze_all_coins(recommender, args, email_configured):
    """分析所有币种"""
    logger.info(f"开始分析市场，处理 {args.coins} 个币种，推荐前 {args.top} 名...")
    results = None
    max_retries = args.max_retries
    retry_count = 0
    
    # 尝试分析所有币种，带重试机制
    while retry_count < max_retries and results is None:
        try:
            results = recommender.analyze_crypto_market(args.coins, args.top)
            
            if not results or not results.get('top_coins'):
                logger.error("分析返回空结果或无推荐币种")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"将在{args.retry_interval}分钟后重试分析 ({retry_count}/{max_retries})...")
                    time.sleep(args.retry_interval * 60)
                continue
                
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_dir = Path(args.data_dir)
            data_dir.mkdir(exist_ok=True)
            
            # 保存推荐结果
            recommendations_file = data_dir / f"recommendations_{timestamp}.json"
            try:
                with open(recommendations_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"推荐结果已保存到 {recommendations_file}")
            except Exception as e:
                logger.error(f"保存JSON推荐结果时出错: {e}")
            
            # 保存CSV格式
            try:
                csv_file = data_dir / f"recommendations_{timestamp}.csv"
                recommender.save_recommendations_csv(results, csv_file)
                logger.info(f"CSV格式推荐结果已保存到 {csv_file}")
                
                # 创建最新结果的软链接或复制
                latest_csv = data_dir / "recommendations.csv"
                try:
                    if os.path.exists(latest_csv):
                        os.remove(latest_csv)
                    if sys.platform == 'win32':
                        # Windows不支持软链接，使用复制代替
                        import shutil
                        shutil.copy2(csv_file, latest_csv)
                    else:
                        os.symlink(csv_file, latest_csv)
                    logger.info(f"已更新最新推荐结果链接: {latest_csv}")
                except Exception as e:
                    logger.error(f"创建最新结果链接时出错: {e}")
            except Exception as e:
                logger.error(f"保存CSV推荐结果时出错: {e}")
            
            # 发送邮件通知
            if email_configured:
                logger.info("尝试发送推荐结果邮件通知...")
                try:
                    result = recommender.send_email_notification(results)
                    logger.info(f"邮件发送结果: {'成功' if result else '失败'}")
                except Exception as e:
                    logger.error(f"发送推荐结果邮件通知时出错: {e}")
                    
        except Exception as e:
            logger.error(f"分析过程中出错: {e}")
            logger.error(traceback.format_exc())
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"将在{args.retry_interval}分钟后重试分析 ({retry_count}/{max_retries})...")
                time.sleep(args.retry_interval * 60)
    
    if retry_count >= max_retries and not results:
        logger.error(f"达到最大重试次数({max_retries})，分析失败")
        
    return results

def main():
    """主函数"""
    global running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 参数解析
    args = parse_args()
    
    # 设置日志级别
    logging_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(logging_level)
    
    # 设置数据目录
    args.data_dir = "crypto_data"
    
    # 打印启动信息
    logger.info("Binance加密货币分析系统已启动")
    logger.info(f"日志级别: {args.log_level}")
    
    # 计算结束时间
    end_time = datetime.now() + timedelta(hours=args.hours)
    logger.info(f"将运行 {args.hours} 小时，每 {args.interval} 分钟分析一次，预计 {end_time.strftime('%Y-%m-%d %H:%M:%S')} 结束")
    
    # 创建数据目录
    data_dir = Path(args.data_dir)
    data_dir.mkdir(exist_ok=True)
    
    # 初始化推荐器
    if args.cache_only:
        logger.info("使用缓存模式")
    if args.refresh_cache:
        logger.info("使用强制刷新模式")
    if args.use_proxies:
        logger.info("使用代理模式")
    if args.mock_data or args.use_mock_data:
        logger.info("使用模拟数据模式")
    if args.force_real_api:
        logger.info("强制使用真实API模式")
    
    recommender = BinanceCryptoRecommender(
        use_cache_only=args.cache_only,
        refresh_cache=args.refresh_cache,
        use_proxies=args.use_proxies,
        mock_data=args.mock_data or args.use_mock_data,
        force_real_api=args.force_real_api
    )
    
    # 设置邮箱
    email_configured = False
    if args.email:
        logger.info(f"设置邮箱: {args.email}")
        recommender.set_email(args.email)
        email_configured = True
    elif args.email_preset:
        logger.info(f"使用预设邮箱配置: {args.email_preset}")
        recommender.use_preset_email(args.email_preset)
        email_configured = True
    
    if not email_configured:
        logger.warning("未配置邮箱，不会发送邮件通知")
    
    # 显示模式信息
    if args.cache_only:
        print("[MODE] 缓存模式 - 仅使用缓存数据")
    elif args.refresh_cache:
        print("[MODE] 强制刷新模式 - 忽略现有缓存")
    elif args.use_proxies:
        print("[MODE] 代理模式 - 使用代理IP池")
    elif args.mock_data or args.use_mock_data:
        print("[MODE] 模拟数据模式 - 使用生成的测试数据")
    else:
        print("[MODE] 标准模式 - 正常API请求")
    
    # 循环运行，直到达到指定时间
    run_count = 0
    while running and datetime.now() < end_time:
        run_count += 1
        remaining_time = (end_time - datetime.now()).total_seconds()
        logger.info(f"开始第 {run_count} 次分析 | 剩余时间: {format_time_remaining(remaining_time)}")
        
        try:
            # 执行内存管理
            perform_memory_management()
            
            # 分析加密货币
            if args.btc_eth_only:
                # 仅分析BTC和ETH
                logger.info("仅分析BTC和ETH模式")
                analyze_btc_eth(recommender, email_configured)
            else:
                # 分析所有币种
                analyze_all_coins(recommender, args, email_configured)
        except Exception as e:
            logger.error(f"分析过程中出错: {e}")
            logger.error(traceback.format_exc())
        
        # 如果已经到了结束时间，就不再等待
        if datetime.now() >= end_time or not running:
            break
            
        # 计算下次运行时间
        next_run_time = datetime.now() + timedelta(minutes=args.interval)
        next_run_time_str = next_run_time.strftime("%H:%M:%S")
        
        # 等待到下次运行
        wait_seconds = (next_run_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            logger.info(f"等待 {args.interval} 分钟到下次分析... (预计 {next_run_time_str} 开始)")
            
            # 使用小间隔检查是否需要退出
            start_wait = datetime.now()
            while (datetime.now() - start_wait).total_seconds() < wait_seconds and running:
                time.sleep(min(5, wait_seconds))  # 最多等待5秒进行一次检查
            
    logger.info(f"分析完成，共运行 {run_count} 次")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

