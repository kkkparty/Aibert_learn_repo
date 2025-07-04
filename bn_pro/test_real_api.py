#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Binance加密货币分析系统 - 真实API测试脚本
测试与Binance API的实际连接
"""

import os
import json
import time
import logging
import requests
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_direct_api_connection():
    """直接测试Binance API连接"""
    logger.info("测试直接API连接...")
    
    endpoints = [
        {"url": "https://api.binance.com/api/v3/ping", "name": "Ping测试"},
        {"url": "https://api.binance.com/api/v3/time", "name": "服务器时间"},
        {"url": "https://api.binance.com/api/v3/exchangeInfo", "name": "交易所信息"}
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            logger.info(f"测试 {endpoint['name']} ({endpoint['url']})...")
            start_time = time.time()
            response = requests.get(endpoint['url'], timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"✓ {endpoint['name']}请求成功! 响应时间: {elapsed:.2f}秒")
                if endpoint['name'] == "交易所信息":
                    data = response.json()
                    symbols_count = len(data.get('symbols', []))
                    logger.info(f"  获取到 {symbols_count} 个交易对信息")
                success_count += 1
            else:
                logger.error(f"✗ {endpoint['name']}请求失败! 状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"  错误信息: {error_data}")
                except:
                    logger.error(f"  响应内容: {response.text[:200]}")
        except Exception as e:
            logger.error(f"✗ {endpoint['name']}请求异常: {e}")
    
    success_rate = success_count / len(endpoints) * 100
    logger.info(f"直接API连接测试完成: {success_count}/{len(endpoints)} 成功 ({success_rate:.1f}%)")
    return success_count > 0

def test_api_adapter():
    """测试API适配器"""
    logger.info("测试 BinanceAPIAdapter...")
    
    try:
        from binance_api_adapter import BinanceAPIAdapter
        
        # 创建API适配器实例
        api = BinanceAPIAdapter()
        logger.info("API适配器创建成功")
        
        # 测试获取交易所信息
        logger.info("获取交易所信息...")
        start_time = time.time()
        exchange_info = api.get_exchange_info()
        elapsed = time.time() - start_time
        
        if exchange_info and 'symbols' in exchange_info:
            symbols_count = len(exchange_info['symbols'])
            logger.info(f"✓ 获取交易所信息成功! 响应时间: {elapsed:.2f}秒")
            logger.info(f"  获取到 {symbols_count} 个交易对信息")
            
            # 显示一些USDT交易对
            usdt_pairs = [s for s in exchange_info['symbols'] if s['quoteAsset'] == 'USDT'][:5]
            logger.info(f"  USDT交易对示例: {', '.join([s['symbol'] for s in usdt_pairs])}")
            
            # 测试获取K线数据
            if usdt_pairs:
                test_symbol = usdt_pairs[0]['symbol']
                logger.info(f"获取 {test_symbol} K线数据...")
                start_time = time.time()
                klines = api.get_klines(test_symbol, "1d", 10)
                elapsed = time.time() - start_time
                
                if klines and len(klines) > 0:
                    logger.info(f"✓ 获取K线数据成功! 响应时间: {elapsed:.2f}秒")
                    logger.info(f"  获取到 {len(klines)} 条K线数据")
                else:
                    logger.error(f"✗ 获取K线数据失败!")
                
                # 测试获取24小时行情
                logger.info(f"获取 {test_symbol} 24小时行情...")
                start_time = time.time()
                ticker = api.get_ticker_24hr(test_symbol)
                elapsed = time.time() - start_time
                
                if ticker and 'symbol' in ticker:
                    logger.info(f"✓ 获取24小时行情成功! 响应时间: {elapsed:.2f}秒")
                    price = float(ticker.get('lastPrice', 0))
                    change = float(ticker.get('priceChangePercent', 0))
                    logger.info(f"  {test_symbol} 价格: {price:.2f} USDT, 24小时变化: {change:.2f}%")
                else:
                    logger.error(f"✗ 获取24小时行情失败!")
            
            return True
        else:
            logger.error("✗ 获取交易所信息失败!")
            return False
    except Exception as e:
        logger.error(f"API适配器测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_recommender():
    """测试推荐系统"""
    logger.info("测试 BinanceCryptoRecommender...")
    
    try:
        from binance_crypto_recommender import BinanceCryptoRecommender
        
        # 创建推荐系统实例
        recommender = BinanceCryptoRecommender()
        logger.info("推荐系统创建成功")
        
        # 测试分析单个币种
        logger.info("分析比特币(BTC)...")
        start_time = time.time()
        btc_analysis = recommender.analyze_single_coin("bitcoin")
        elapsed = time.time() - start_time
        
        if btc_analysis:
            logger.info(f"✓ BTC分析成功! 耗时: {elapsed:.2f}秒")
            logger.info(f"  RSI: {btc_analysis.get('rsi', 'N/A')}")
            logger.info(f"  趋势: {btc_analysis.get('trend', 'N/A')}")
            logger.info(f"  建议: {btc_analysis.get('recommendation', 'N/A')}")
            
            # 测试市场分析
            logger.info("分析市场 (仅分析5个币种)...")
            start_time = time.time()
            market_analysis = recommender.analyze_crypto_market(coin_count=5)
            elapsed = time.time() - start_time
            
            if market_analysis and 'recommendations' in market_analysis:
                recommendations = market_analysis['recommendations']
                logger.info(f"✓ 市场分析成功! 耗时: {elapsed:.2f}秒")
                logger.info(f"  获取到 {len(recommendations)} 个推荐")
                
                # 打印推荐结果
                for idx, rec in enumerate(recommendations[:3], 1):
                    logger.info(f"  推荐 #{idx}: {rec.get('symbol', 'N/A')} - 评分: {rec.get('score', 'N/A')}")
                
                return True
            else:
                logger.error("✗ 市场分析失败!")
                return False
        else:
            logger.error("✗ BTC分析失败!")
            return False
    except Exception as e:
        logger.error(f"推荐系统测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_network_connectivity():
    """测试网络连接性"""
    logger.info("测试网络连接性...")
    
    test_urls = [
        {"url": "https://www.google.com", "name": "Google"},
        {"url": "https://www.binance.com", "name": "Binance官网"},
        {"url": "https://api.binance.com", "name": "Binance API"}
    ]
    
    success_count = 0
    for site in test_urls:
        try:
            logger.info(f"连接 {site['name']} ({site['url']})...")
            start_time = time.time()
            response = requests.get(site['url'], timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"✓ {site['name']}连接成功! 响应时间: {elapsed:.2f}秒")
                success_count += 1
            else:
                logger.error(f"✗ {site['name']}连接失败! 状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ {site['name']}连接异常: {e}")
    
    success_rate = success_count / len(test_urls) * 100
    logger.info(f"网络连接测试完成: {success_count}/{len(test_urls)} 成功 ({success_rate:.1f}%)")
    
    # 检查是否可能存在地区限制
    if success_count < len(test_urls):
        if any("Binance" in site["name"] for site in test_urls):
            logger.warning("⚠ 可能存在Binance地区限制，建议使用代理或VPN")
    
    return success_count > 0

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Binance加密货币分析系统真实API测试")
    parser.add_argument("--network-only", action="store_true", help="仅测试网络连接")
    parser.add_argument("--api-only", action="store_true", help="仅测试API连接")
    parser.add_argument("--use-proxy", action="store_true", help="使用代理")
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    logger.info("=" * 50)
    logger.info("Binance加密货币分析系统 - 真实API测试")
    logger.info("=" * 50)
    
    # 检查代理设置
    if args.use_proxy:
        logger.info("使用代理模式")
        # 这里可以添加代理设置的代码
    
    # 运行测试
    tests = []
    
    # 如果指定了仅测试网络，只运行网络测试
    if args.network_only:
        tests.append(("网络连接测试", test_network_connectivity))
    # 如果指定了仅测试API，只运行API测试
    elif args.api_only:
        tests.append(("直接API连接测试", test_direct_api_connection))
        tests.append(("API适配器测试", test_api_adapter))
    # 否则运行所有测试
    else:
        tests = [
            ("网络连接测试", test_network_connectivity),
            ("直接API连接测试", test_direct_api_connection),
            ("API适配器测试", test_api_adapter),
            ("推荐系统测试", test_recommender)
        ]
    
    # 运行测试并收集结果
    results = []
    for name, test_func in tests:
        logger.info(f"\n开始 {name}...")
        success = test_func()
        status = "通过" if success else "失败"
        logger.info(f"{name} {status}")
        results.append((name, status))
    
    # 打印测试汇总
    logger.info("\n" + "=" * 50)
    logger.info("测试结果汇总")
    logger.info("=" * 50)
    for name, status in results:
        logger.info(f"{name}: {status}")
    
    # 检查是否所有测试都通过
    all_passed = all(status == "通过" for _, status in results)
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("所有测试通过！系统可以正常连接到Binance API。")
    else:
        logger.info("部分测试失败，可能存在连接问题。")
        # 提供一些建议
        logger.info("\n可能的解决方案:")
        logger.info("1. 检查网络连接")
        logger.info("2. 使用代理或VPN绕过地区限制")
        logger.info("3. 使用模拟数据模式进行测试和开发")
    logger.info("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    main() 