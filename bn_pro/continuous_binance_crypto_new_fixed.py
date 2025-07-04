#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Binance加密货币分析系统
连续运行版本，支持定时分析和邮件通知
修复版本 - 解决编码问题
"""

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

# 导入自定义模块
    from binance_crypto_recommender import BinanceCryptoRecommender
from binance_api_adapter import BinanceAPIAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
running = True

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

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Binance加密货币分析系统')
    parser.add_argument('--hours', type=float, default=24.0, help='运行小时数')
    parser.add_argument('--interval', type=int, default=15, help='分析间隔（分钟）')
    parser.add_argument('--coins', type=int, default=100, help='分析的币种数量')
    parser.add_argument('--top', type=int, default=10, help='推荐币种数量')
    parser.add_argument('--email', type=str, help='通知邮箱，多个邮箱用逗号分隔')
    parser.add_argument('--cache-only', action='store_true', help='仅使用缓存数据，不发送API请求')
    parser.add_argument('--use-proxies', action='store_true', help='使用代理')
    parser.add_argument('--refresh-cache', action='store_true', help='强制刷新缓存')
    parser.add_argument('--mock-data', action='store_true', help='使用模拟数据')
    parser.add_argument('--email-preset', type=int, default=1, choices=[1, 2], help='使用预设邮箱配置(1或2)')
    parser.add_argument('--no-btc-eth-notify', action='store_true', help='不发送BTC和ETH数据的邮件通知')
    return parser.parse_args()

def main():
    """主函数"""
    global running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 参数解析
    args = parse_arguments()
    
    # 打印启动信息
    logger.info("Binance加密货币分析系统已启动")
    
    # 计算结束时间
    end_time = datetime.now() + timedelta(hours=args.hours)
    logger.info(f"将运行 {args.hours} 小时，每 {args.interval} 分钟分析一次，预计 {end_time.strftime('%Y-%m-%d %H:%M:%S')} 结束")
    
    # 创建数据目录
    data_dir = Path("crypto_data")
    data_dir.mkdir(exist_ok=True)
    
    # 初始化推荐器
    if args.mock_data:
        logger.info("使用模拟数据模式")
    elif args.cache_only:
        logger.info("使用缓存模式 - 仅使用缓存数据，不发送API请求")
    elif args.refresh_cache:
        logger.info("使用强制刷新模式 - 不使用缓存数据")
    else:
        logger.info("使用API请求模式")
    
    # 打印模式信息
    if args.cache_only:
        print("已激活缓存模式 - 仅使用缓存数据，不发送API请求")
    elif args.refresh_cache:
        print("已激活强制刷新模式 - 不使用缓存数据")
    else:
        print("使用API请求模式 - 会发送网络请求获取最新数据")
    
    # 创建API适配器
    api = BinanceAPIAdapter(
        use_cache_only=args.cache_only,
        use_proxies=args.use_proxies,
        refresh_cache=args.refresh_cache,
        use_mock_data=args.mock_data
    )
    
    # 创建推荐器
    recommender = BinanceCryptoRecommender(api)
    
    # 设置邮箱
    email_configured = False
    if args.email:
        emails = args.email.split(',')
        logger.info(f"设置邮箱: {args.email}")
        
        # 获取QQ邮箱密码
        qq_email = None
        for email in emails:
            if email.endswith('@qq.com'):
                qq_email = email
                break
        
        if qq_email:
            logger.info(f"使用QQ邮箱: {qq_email}")
            password = os.environ.get('QQ_EMAIL_PASSWORD')
            if password:
                recommender.set_email_config(qq_email, password)
        email_configured = True
            else:
                logger.warning("未设置QQ_EMAIL_PASSWORD环境变量，无法发送邮件")
        else:
            logger.warning("未找到QQ邮箱，无法发送邮件")
    
    # 显示模式信息
    if args.mock_data:
        print("[MODE] 模拟数据模式 - 使用生成的测试数据")
    elif args.cache_only:
        print("[MODE] 缓存模式 - 仅使用本地缓存数据")
    elif args.refresh_cache:
        print("[MODE] 强制刷新模式 - 忽略缓存")
    else:
        print("[MODE] 标准模式 - 正常API请求")
    
    # 循环运行，直到达到指定时间
    run_count = 0
    while running and datetime.now() < end_time:
        run_count += 1
        remaining_time = (end_time - datetime.now()).total_seconds()
        logger.info(f"开始第 {run_count} 次分析 | 剩余时间: {format_time_remaining(remaining_time)}")
        
        try:
            # 无论是否只分析BTC和ETH，都先获取并发送BTC/ETH数据
            if email_configured and not args.no_btc_eth_notify:
                # 分析BTC
                logger.info("开始分析比特币(BTC)...")
                btc_analysis = recommender.analyze_single_coin('bitcoin')
                
                # 分析ETH
                logger.info("开始分析以太坊(ETH)...")
                eth_analysis = recommender.analyze_single_coin('ethereum')
                
                # 发送BTC/ETH邮件通知
                if btc_analysis or eth_analysis:
                        logger.info("尝试发送BTC/ETH邮件通知...")
                        try:
                        # 如果两个数据都有，使用内置方法发送
                        if btc_analysis and eth_analysis:
                            result = recommender.send_btc_eth_notification(btc_analysis, eth_analysis)
                            logger.info(f"邮件发送结果: {'成功' if result else '失败'}")
                        else:
                            # 如果某个数据缺失，自己构建邮件内容
                            email_subject = f"BTC和ETH市场状态 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            email_content = f"BTC和ETH市场状态 (Binance数据源)\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            
                            if btc_analysis:
                                email_content += f"BTC (比特币) 数据:\n"
                                email_content += f"价格: ${btc_analysis['price']:.2f}\n"
                                email_content += f"24小时变化: {btc_analysis['price_change_24h']:.2f}%\n"
                                email_content += f"RSI指标: {btc_analysis['rsi']:.2f}\n"
                                email_content += f"市场趋势: {btc_analysis['trend']}\n\n"
                            else:
                                email_content += "无法获取BTC数据\n\n"
                                
                            if eth_analysis:
                                email_content += f"ETH (以太坊) 数据:\n"
                                email_content += f"价格: ${eth_analysis['price']:.2f}\n"
                                email_content += f"24小时变化: {eth_analysis['price_change_24h']:.2f}%\n"
                                email_content += f"RSI指标: {eth_analysis['rsi']:.2f}\n"
                                email_content += f"市场趋势: {eth_analysis['trend']}\n"
                            else:
                                email_content += "无法获取ETH数据\n"
                            
                            # 导入发送邮件函数
                            try:
                                from bn2bc import send_results_to_qq_email
                                # 获取邮箱地址列表
                                email_addresses = []
                                if args.email:
                                    email_addresses = [email.strip() for email in args.email.split(',') if email.strip()]
                                elif args.email_preset == 1:
                                    email_addresses = ['840137950@qq.com']
                                elif args.email_preset == 2:
                                    email_addresses = ['3077463778@qq.com']
                                
                                # 为每个邮箱发送
                                for email_address in email_addresses:
                                    if email_address:
                                        send_results_to_qq_email(
                                            to_email=email_address,
                                            subject=email_subject,
                                            text_content=email_content,
                                            use_obfuscation=False
                                        )
                                        logger.info(f"已发送BTC/ETH数据更新通知到 {email_address}")
                            except Exception as e:
                                logger.error(f"发送邮件失败: {e}")
                        except Exception as e:
                            logger.error(f"发送BTC/ETH邮件通知时出错: {e}")
                    else:
                    logger.error("无法获取BTC和ETH数据，无法发送通知")
            
                # 分析所有币种
                logger.info(f"开始分析市场，处理 {args.coins} 个币种，推荐前 {args.top} 名...")
                results = recommender.analyze_crypto_market(args.coins, args.top)
                
            if results and 'recommendations' in results and results['recommendations']:
                    # 保存结果
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
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
                        
                        # 创建最新结果的软链接
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
                        # 修复键名不匹配问题
                        if 'recommendations' in results and not 'top_coins' in results:
                            # 创建兼容格式
                            compatible_results = results.copy()
                            compatible_results['top_coins'] = results['recommendations']
                            result = recommender.send_email_notification(compatible_results)
                        else:
                            result = recommender.send_email_notification(results)
                            logger.info(f"邮件发送结果: {'成功' if result else '失败'}")
                        except Exception as e:
                            logger.error(f"发送推荐结果邮件通知时出错: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.warning("分析未返回结果或结果为空")
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

