#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Binance加密货币分析系统 - 功能测试脚本
测试系统的所有主要功能
"""

import os
import json
import logging
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_adapter(use_mock_data=True):
    """测试API适配器"""
    logger.info("测试 BinanceAPIAdapter...")
    
    try:
        from binance_api_adapter import BinanceAPIAdapter
        
        # 创建API适配器实例
        api = BinanceAPIAdapter(use_mock_data=use_mock_data)
        logger.info(f"API适配器创建成功，使用模拟数据: {use_mock_data}")
        
        # 测试获取交易所信息
        exchange_info = api.get_exchange_info()
        symbols_count = len(exchange_info.get('symbols', []))
        logger.info(f"获取到 {symbols_count} 个交易对信息")
        
        # 测试获取K线数据
        btc_klines = api.get_klines("BTCUSDT", "1d", 10)
        logger.info(f"获取到 {len(btc_klines)} 条BTC K线数据")
        
        # 测试获取24小时行情
        btc_ticker = api.get_ticker_24hr("BTCUSDT")
        logger.info(f"获取到BTC 24小时行情数据: {btc_ticker.get('symbol', 'N/A')}")
        
        # 测试获取多个币种数据
        coins = api.fetch_coin_data(count=5)
        logger.info(f"获取到 {len(coins)} 个币种数据")
        
        return True, "API适配器测试通过"
    except Exception as e:
        logger.error(f"API适配器测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"API适配器测试失败: {e}"

def test_recommender(use_mock_data=True):
    """测试推荐系统"""
    logger.info("测试 BinanceCryptoRecommender...")
    
    try:
        from binance_crypto_recommender import BinanceCryptoRecommender
        from binance_api_adapter import BinanceAPIAdapter
        
        # 创建API适配器和推荐系统实例
        api = BinanceAPIAdapter(use_mock_data=use_mock_data)
        recommender = BinanceCryptoRecommender(api)
        logger.info(f"推荐系统创建成功，使用模拟数据: {use_mock_data}")
        
        # 测试分析单个币种
        btc_analysis = recommender.analyze_single_coin("bitcoin")
        if btc_analysis:
            logger.info(f"BTC分析结果: RSI={btc_analysis.get('rsi', 'N/A')}, 趋势={btc_analysis.get('trend', 'N/A')}")
        else:
            logger.warning("BTC分析结果为空")
        
        # 测试市场分析
        market_analysis = recommender.analyze_crypto_market(coin_count=5, top_count=3)
        if market_analysis and 'recommendations' in market_analysis:
            recommendations = market_analysis['recommendations']
            logger.info(f"市场分析完成，获取到 {len(recommendations)} 个推荐")
            
            # 打印推荐结果
            for idx, rec in enumerate(recommendations[:3], 1):
                logger.info(f"推荐 #{idx}: {rec.get('symbol', 'N/A')} - 评分: {rec.get('score', 'N/A')}")
        else:
            logger.warning("市场分析结果为空")
        
        return True, "推荐系统测试通过"
    except Exception as e:
        logger.error(f"推荐系统测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"推荐系统测试失败: {e}"

def test_notification():
    """测试邮件通知功能"""
    logger.info("测试邮件通知功能...")
    
    try:
        from binance_crypto_recommender import BinanceCryptoRecommender
        from binance_api_adapter import BinanceAPIAdapter
        
        # 创建API适配器和推荐系统实例
        api = BinanceAPIAdapter(use_mock_data=True)
        recommender = BinanceCryptoRecommender(api)
        
        # 检查环境变量中是否有QQ邮箱密码
        password = os.environ.get('QQ_EMAIL_PASSWORD')
        if not password:
            logger.warning("未设置QQ_EMAIL_PASSWORD环境变量，跳过邮件测试")
            return False, "未设置QQ_EMAIL_PASSWORD环境变量"
        
        # 设置邮箱配置
        test_email = "840137950@qq.com"  # 使用默认测试邮箱
        recommender.set_email_config(test_email, password)
        logger.info(f"邮箱配置设置为: {test_email}")
        
        # 创建测试通知内容
        test_content = {
            "subject": "Binance分析系统测试邮件",
            "body": f"这是一封测试邮件，发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # 发送测试邮件
        result = recommender.send_email(test_content["subject"], test_content["body"])
        if result:
            logger.info("测试邮件发送成功")
            return True, "邮件通知测试通过"
        else:
            logger.warning("测试邮件发送失败")
            return False, "邮件通知测试失败"
    except Exception as e:
        logger.error(f"邮件通知测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"邮件通知测试失败: {e}"

def test_encoding():
    """测试中文编码处理"""
    logger.info("测试中文编码处理...")
    
    try:
        # 测试中文字符串
        test_string = "这是一段中文测试文本，包含特殊字符：！@#￥%……&*（）"
        
        # 测试写入文件
        test_file = "encoding_test.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_string)
        logger.info(f"已写入测试文件: {test_file}")
        
        # 测试读取文件
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 验证内容
        if content == test_string:
            logger.info("中文编码测试通过")
            return True, "中文编码测试通过"
        else:
            logger.warning("中文编码测试失败：内容不匹配")
            return False, "中文编码测试失败：内容不匹配"
    except Exception as e:
        logger.error(f"中文编码测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, f"中文编码测试失败: {e}"

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Binance加密货币分析系统功能测试")
    parser.add_argument("--real-api", action="store_true", help="使用真实API而非模拟数据")
    parser.add_argument("--test-email", action="store_true", help="测试邮件功能")
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    use_mock_data = not args.real_api
    
    logger.info("=" * 50)
    logger.info("Binance加密货币分析系统功能测试")
    logger.info("=" * 50)
    logger.info(f"使用模拟数据: {use_mock_data}")
    
    # 运行测试
    tests = [
        ("API适配器测试", lambda: test_api_adapter(use_mock_data)),
        ("推荐系统测试", lambda: test_recommender(use_mock_data)),
        ("中文编码测试", test_encoding)
    ]
    
    # 如果指定了测试邮件，添加邮件测试
    if args.test_email:
        tests.append(("邮件通知测试", test_notification))
    
    # 运行测试并收集结果
    results = []
    for name, test_func in tests:
        logger.info(f"\n开始 {name}...")
        success, message = test_func()
        status = "通过" if success else "失败"
        logger.info(f"{name} {status}: {message}")
        results.append((name, status, message))
    
    # 打印测试汇总
    logger.info("\n" + "=" * 50)
    logger.info("测试结果汇总")
    logger.info("=" * 50)
    for name, status, message in results:
        logger.info(f"{name}: {status}")
    
    # 检查是否所有测试都通过
    all_passed = all(status == "通过" for _, status, _ in results)
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("所有测试通过！系统功能正常。")
    else:
        logger.info("部分测试失败，请查看上面的错误信息。")
    logger.info("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    main() 