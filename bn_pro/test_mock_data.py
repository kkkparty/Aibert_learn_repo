#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试模拟数据生成器
"""

import os
import json
import logging
from mock_data_generator import mock_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_klines():
    """测试K线数据生成"""
    logger.info("测试K线数据生成...")
    
    # 生成BTC的K线数据
    klines = mock_data.generate_klines("BTCUSDT", "1d", 30)
    logger.info(f"生成了 {len(klines)} 条BTC K线数据")
    
    # 打印第一条数据
    logger.info("第一条K线数据:")
    logger.info(json.dumps(klines[0], indent=2))
    
    return len(klines) == 30

def test_ticker_24hr():
    """测试24小时行情数据生成"""
    logger.info("测试24小时行情数据生成...")
    
    # 生成单个币种的数据
    btc_ticker = mock_data.generate_ticker_24hr("BTCUSDT")
    logger.info("BTC 24小时行情数据:")
    logger.info(json.dumps(btc_ticker, indent=2))
    
    # 生成所有币种的数据
    all_tickers = mock_data.generate_ticker_24hr()
    logger.info(f"生成了 {len(all_tickers)} 种币种的24小时行情数据")
    
    return len(all_tickers) > 0

def test_exchange_info():
    """测试交易所信息生成"""
    logger.info("测试交易所信息生成...")
    
    # 生成交易所信息
    exchange_info = mock_data.generate_exchange_info()
    logger.info(f"生成了 {len(exchange_info['symbols'])} 个交易对的信息")
    
    # 打印第一个交易对的信息
    logger.info("第一个交易对信息:")
    logger.info(json.dumps(exchange_info['symbols'][0], indent=2))
    
    return len(exchange_info['symbols']) > 0

def test_mock_response():
    """测试模拟响应生成"""
    logger.info("测试模拟响应生成...")
    
    # 测试K线接口
    klines_response = mock_data.generate_mock_response(
        "/api/v3/klines", 
        {"symbol": "BTCUSDT", "interval": "1d", "limit": 10}
    )
    logger.info(f"K线接口返回了 {len(klines_response)} 条数据")
    
    # 测试24小时行情接口
    ticker_response = mock_data.generate_mock_response(
        "/api/v3/ticker/24hr", 
        {"symbol": "ETHUSDT"}
    )
    logger.info("24小时行情接口返回数据:")
    logger.info(json.dumps(ticker_response, indent=2))
    
    # 测试交易所信息接口
    exchange_info_response = mock_data.generate_mock_response("/api/v3/exchangeInfo")
    logger.info(f"交易所信息接口返回了 {len(exchange_info_response['symbols'])} 个交易对")
    
    return True

def main():
    """主函数"""
    logger.info("开始测试模拟数据生成器...")
    
    # 运行所有测试
    tests = [
        ("K线数据测试", test_klines),
        ("24小时行情测试", test_ticker_24hr),
        ("交易所信息测试", test_exchange_info),
        ("模拟响应测试", test_mock_response)
    ]
    
    # 记录测试结果
    results = []
    for name, test_func in tests:
        logger.info(f"运行测试: {name}")
        try:
            result = test_func()
            status = "通过" if result else "失败"
            logger.info(f"测试结果: {status}")
            results.append((name, status))
        except Exception as e:
            logger.error(f"测试出错: {e}")
            results.append((name, "错误"))
    
    # 打印测试汇总
    logger.info("\n测试汇总:")
    for name, status in results:
        logger.info(f"{name}: {status}")
    
    # 检查是否所有测试都通过
    all_passed = all(status == "通过" for _, status in results)
    logger.info(f"\n总体结果: {'全部通过' if all_passed else '部分失败'}")
    
    return all_passed

if __name__ == "__main__":
    main() 