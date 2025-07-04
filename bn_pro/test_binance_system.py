#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_btc_eth_analysis():
    """测试BTC和ETH分析和邮件通知功能"""
    logger.info("开始测试BTC/ETH分析和邮件通知功能")
    
    try:
        # 导入推荐系统
        from binance_crypto_recommender import BinanceCryptoRecommender
        
        # 打印当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"当前时间: {current_time}")
        
        # 初始化推荐系统
        recommender = BinanceCryptoRecommender(
            use_cache_only=False,
            refresh_cache=True,
            use_proxies=False
        )
        
        # 设置默认QQ邮箱
        recommender.use_preset_email(1)  # 使用预设邮箱配置1
        
        # 分析BTC
        logger.info("开始分析比特币(BTC)...")
        btc_analysis = recommender.analyze_single_coin('bitcoin')
        
        if btc_analysis:
            logger.info(f"BTC分析结果: 价格=${btc_analysis['price']:.2f}, "
                        f"24h变化={btc_analysis['price_change_24h']:.2f}%, "
                        f"RSI={btc_analysis['rsi']:.2f}, 趋势={btc_analysis['trend']}, "
                        f"建议={btc_analysis['action']}")
        else:
            logger.error("BTC分析失败")
            return False
        
        # 分析ETH
        logger.info("开始分析以太坊(ETH)...")
        eth_analysis = recommender.analyze_single_coin('ethereum')
        
        if eth_analysis:
            logger.info(f"ETH分析结果: 价格=${eth_analysis['price']:.2f}, "
                        f"24h变化={eth_analysis['price_change_24h']:.2f}%, "
                        f"RSI={eth_analysis['rsi']:.2f}, 趋势={eth_analysis['trend']}, "
                        f"建议={eth_analysis['action']}")
        else:
            logger.error("ETH分析失败")
            return False
        
        # 发送BTC/ETH邮件通知
        logger.info("发送BTC/ETH邮件通知...")
        result = recommender.send_btc_eth_notification(btc_analysis, eth_analysis)
        
        if result:
            logger.info("邮件通知发送成功")
        else:
            logger.error("邮件通知发送失败")
            return False
        
        logger.info("BTC/ETH分析和邮件通知测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_analysis():
    """测试市场分析功能"""
    logger.info("开始测试市场分析功能")
    
    try:
        # 导入推荐系统
        from binance_crypto_recommender import BinanceCryptoRecommender
        
        # 打印当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"当前时间: {current_time}")
        
        # 初始化推荐系统
        recommender = BinanceCryptoRecommender(
            use_cache_only=False,
            refresh_cache=True,
            use_proxies=False
        )
        
        # 设置默认QQ邮箱
        recommender.use_preset_email(1)  # 使用预设邮箱配置1
        
        # 分析市场 (仅限制分析10个币种，节省测试时间)
        logger.info("开始分析加密货币市场...")
        results = recommender.analyze_crypto_market(10, 5)
        
        if results and 'analyzed_count' in results:
            logger.info(f"市场分析结果: 分析了 {results['analyzed_count']} 种币")
            if 'recommendations' in results and results['recommendations']:
                logger.info(f"找到 {len(results['recommendations'])} 种推荐币种")
                for i, rec in enumerate(results['recommendations'][:3], 1):
                    logger.info(f"推荐 {i}: {rec['symbol']} - {rec['name']}")
            else:
                logger.warning("没有找到推荐币种")
        else:
            logger.error("市场分析失败")
            return False
        
        # 保存结果
        logger.info("保存分析结果...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = recommender.save_results_with_timestamp(results, f"test_{timestamp}")
        logger.info(f"结果已保存到: {file_path}")
        
        logger.info("市场分析测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n===== Binance API 加密货币分析系统测试 =====\n")
    
    # 测试BTC/ETH分析
    print("\n[测试1] BTC/ETH分析和邮件通知功能")
    btc_eth_result = test_btc_eth_analysis()
    
    # 测试市场分析
    print("\n[测试2] 市场分析功能")
    market_result = test_market_analysis()
    
    # 总结测试结果
    print("\n===== 测试结果摘要 =====")
    print(f"BTC/ETH分析和邮件通知: {'成功' if btc_eth_result else '失败'}")
    print(f"市场分析功能: {'成功' if market_result else '失败'}")
    
    if btc_eth_result and market_result:
        print("\n总体测试结果: 成功")
        return 0
    else:
        print("\n总体测试结果: 部分失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 