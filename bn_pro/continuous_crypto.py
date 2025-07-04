#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import logging
import argparse
from bn2bc import CryptoRecommender, send_results_to_qq_email

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_continuous_analysis(hours=24, interval_minutes=15, limit=1000, use_proxies=True, 
                           refresh_cache=True, save_raw=True, email=None, notify_btc_eth=True):
    """
    持续运行加密货币分析，间隔指定分钟数
    
    参数:
    hours -- 运行总小时数
    interval_minutes -- 每次分析之间的间隔（分钟）
    limit -- 每次分析的币种数量
    use_proxies -- 是否使用代理
    refresh_cache -- 是否强制刷新缓存
    save_raw -- 是否保存原始数据
    email -- 接收结果的邮箱地址（如果为None则不发送邮件）
    notify_btc_eth -- 是否每次都发送BTC和ETH的邮件通知
    """
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(hours=hours)
    
    logger.info(f"开始连续分析任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"将连续运行 {hours} 小时，到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"分析间隔: {interval_minutes} 分钟")
    
    # 初始化邮箱列表
    email_addresses = []
    if email:
        email_addresses = [email.strip() for email in email.split(',') if email.strip()]
    
    run_count = 0
    
    try:
        while datetime.datetime.now() < end_time:
            run_count += 1
            current_time = datetime.datetime.now()
            elapsed = current_time - start_time
            remaining = end_time - current_time
            
            logger.info(f"===== 开始第 {run_count} 次分析 =====")
            logger.info(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"已运行: {elapsed.total_seconds() / 3600:.2f} 小时")
            logger.info(f"剩余时间: {remaining.total_seconds() / 3600:.2f} 小时")
            
            try:
                # 初始化推荐器
                recommender = CryptoRecommender(
                    use_cache_only=False, 
                    use_proxies=use_proxies,
                    refresh_cache=refresh_cache
                )
                
                # 执行分析
                results = recommender.simulate_daily_reminders(
                    days=1, 
                    limit=limit,
                    sort_by='score',
                    save_timestamp=True,
                    save_all_data=save_raw,
                    email_addresses=email_addresses,
                    high_score_threshold=50
                )
                
                if results:
                    logger.info(f"分析完成: 共分析了 {results['analyzed_count']}/{results['total_count']} 种加密货币")
                    logger.info(f"发现 {results['recommendations_count']} 个购买推荐")
                    
                    # 发送BTC和ETH数据邮件通知
                    if notify_btc_eth and email_addresses:
                        # 获取BTC和ETH数据
                        btc_data = None
                        eth_data = None
                        
                        # 获取BTC数据
                        try:
                            btc_history = recommender.fetch_price_history('bitcoin')
                            if btc_history is not None:
                                btc_indicators = recommender.calculate_technical_indicators(btc_history)
                                btc_trend = recommender.analyze_market_trend(btc_history)
                                if btc_indicators:
                                    btc_data = {
                                        'symbol': 'BTC',
                                        'name': 'Bitcoin',
                                        'price': btc_history['close'].iloc[-1],
                                        'price_change_24h': btc_history['close'].pct_change(1).iloc[-1] * 100,
                                        'price_change_7d': btc_history['close'].pct_change(7).iloc[-1] * 100,
                                        'rsi': btc_indicators['rsi'],
                                        'trend': btc_trend
                                    }
                        except Exception as e:
                            logger.error(f"获取BTC数据失败: {e}")
                            
                        # 获取ETH数据
                        try:
                            eth_history = recommender.fetch_price_history('ethereum')
                            if eth_history is not None:
                                eth_indicators = recommender.calculate_technical_indicators(eth_history)
                                eth_trend = recommender.analyze_market_trend(eth_history)
                                if eth_indicators:
                                    eth_data = {
                                        'symbol': 'ETH',
                                        'name': 'Ethereum',
                                        'price': eth_history['close'].iloc[-1],
                                        'price_change_24h': eth_history['close'].pct_change(1).iloc[-1] * 100,
                                        'price_change_7d': eth_history['close'].pct_change(7).iloc[-1] * 100,
                                        'rsi': eth_indicators['rsi'],
                                        'trend': eth_trend
                                    }
                        except Exception as e:
                            logger.error(f"获取ETH数据失败: {e}")
                            
                        # 发送BTC和ETH数据邮件
                        if btc_data or eth_data:
                            email_subject = f"BTC和ETH数据更新 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                            email_content = f"BTC和ETH数据更新\n时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            
                            if btc_data:
                                email_content += f"BTC (比特币) 数据:\n"
                                email_content += f"价格: ${btc_data['price']:.2f}\n"
                                email_content += f"24小时变化: {btc_data['price_change_24h']:.2f}%\n"
                                email_content += f"7天变化: {btc_data['price_change_7d']:.2f}%\n"
                                email_content += f"RSI指标: {btc_data['rsi']:.2f}\n"
                                email_content += f"市场趋势: {btc_data['trend']}\n\n"
                                
                            if eth_data:
                                email_content += f"ETH (以太坊) 数据:\n"
                                email_content += f"价格: ${eth_data['price']:.2f}\n"
                                email_content += f"24小时变化: {eth_data['price_change_24h']:.2f}%\n"
                                email_content += f"7天变化: {eth_data['price_change_7d']:.2f}%\n"
                                email_content += f"RSI指标: {eth_data['rsi']:.2f}\n"
                                email_content += f"市场趋势: {eth_data['trend']}\n"
                                
                            # 为每个邮箱发送通知
                            for email_address in email_addresses:
                                if email_address and email_address.strip():
                                    try:
                                        send_results_to_qq_email(
                                            to_email=email_address.strip(),
                                            subject=email_subject,
                                            text_content=email_content,
                                            use_obfuscation=False
                                        )
                                        logger.info(f"已发送BTC和ETH数据更新通知到 {email_address}")
                                    except Exception as e:
                                        logger.error(f"发送BTC和ETH数据通知邮件失败: {e}")
                else:
                    logger.warning("分析完成但未返回结果")
            
            except Exception as e:
                logger.error(f"本轮分析出错: {e}")
            
            # 计算下次运行时间
            next_run = current_time + datetime.timedelta(minutes=interval_minutes)
            
            # 如果已经超过结束时间，跳出循环
            if next_run > end_time:
                logger.info("已达到预定运行时间，任务结束")
                break
            
            # 等待到下次运行时间
            wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.info(f"等待 {wait_seconds:.2f} 秒到下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(wait_seconds)
    
    except KeyboardInterrupt:
        logger.info("接收到中断信号，任务结束")
    
    finally:
        logger.info(f"连续分析任务结束，共执行了 {run_count} 次分析")
        logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总运行时间: {(datetime.datetime.now() - start_time).total_seconds() / 3600:.2f} 小时")

def main():
    try:
        # 设置命令行参数解析
        parser = argparse.ArgumentParser(description='连续加密货币分析工具')
        parser.add_argument('--hours', type=int, default=24, help='连续运行的总小时数')
        parser.add_argument('--interval', type=int, default=15, help='每次分析之间的间隔（分钟）')
        parser.add_argument('--limit', '--coins', type=int, default=1000, help='每次分析的币种数量')
        parser.add_argument('--no-proxies', action='store_true', help='不使用代理')
        parser.add_argument('--no-cache-refresh', action='store_true', help='不强制刷新缓存')
        parser.add_argument('--no-save-raw', action='store_true', help='不保存原始数据')
        parser.add_argument('--email', '--qq-email', type=str, help='接收结果的QQ邮箱地址，多个邮箱用逗号分隔')
        parser.add_argument('--no-btc-eth-notify', action='store_true', help='不发送BTC和ETH数据的邮件通知')
        args = parser.parse_args()
        
        # 运行连续分析
        run_continuous_analysis(
            hours=args.hours,
            interval_minutes=args.interval,
            limit=args.limit,
            use_proxies=not args.no_proxies,
            refresh_cache=not args.no_cache_refresh,
            save_raw=not args.no_save_raw,
            email=args.email,
            notify_btc_eth=not args.no_btc_eth_notify
        )
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 