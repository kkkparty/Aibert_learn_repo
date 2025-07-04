#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
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

def test_encoding():
    """测试中文编码是否正常"""
    logger.info("测试中文编码")
    print("测试中文字符: 比特币、以太坊、加密货币")
    
    # 写入文件测试
    with open("encoding_test.txt", "w", encoding="utf-8") as f:
        f.write("测试中文字符: 比特币、以太坊、加密货币\n")
    
    # 读取文件测试
    with open("encoding_test.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"从文件读取: {content}")
    return True

def test_mock_btc_eth():
    """测试BTC/ETH分析和通知（使用模拟数据）"""
    try:
        from binance_crypto_recommender import BinanceCryptoRecommender
        
        # 初始化推荐系统（使用模拟数据）
        recommender = BinanceCryptoRecommender(mock_data=True)
        
        # 设置邮箱
        recommender.use_preset_email(1)  # 使用预设邮箱配置1
        
        # 分析BTC
        logger.info("开始分析比特币(BTC)...")
        btc_analysis = recommender.analyze_single_coin('bitcoin')
        
        if btc_analysis:
            logger.info(f"BTC分析结果: 价格=${btc_analysis['price']:.2f}, "
                       f"24h变化={btc_analysis['price_change_24h']:.2f}%, "
                       f"RSI={btc_analysis['rsi']:.2f}, 趋势={btc_analysis['trend']}")
        else:
            logger.error("BTC分析失败")
            return False
        
        # 分析ETH
        logger.info("开始分析以太坊(ETH)...")
        eth_analysis = recommender.analyze_single_coin('ethereum')
        
        if eth_analysis:
            logger.info(f"ETH分析结果: 价格=${eth_analysis['price']:.2f}, "
                       f"24h变化={eth_analysis['price_change_24h']:.2f}%, "
                       f"RSI={eth_analysis['rsi']:.2f}, 趋势={eth_analysis['trend']}")
        else:
            logger.error("ETH分析失败")
            return False
        
        # 创建通知内容（不实际发送）
        email_subject = f"BTC和ETH市场状态 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        email_content = f"BTC和ETH市场状态 (Binance数据源)\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if btc_analysis:
            email_content += f"BTC (比特币) 数据:\n"
            email_content += f"价格: ${btc_analysis['price']:.2f}\n"
            email_content += f"24小时变化: {btc_analysis['price_change_24h']:.2f}%\n"
            email_content += f"RSI指标: {btc_analysis['rsi']:.2f}\n"
            email_content += f"市场趋势: {btc_analysis['trend']}\n\n"
        
        if eth_analysis:
            email_content += f"ETH (以太坊) 数据:\n"
            email_content += f"价格: ${eth_analysis['price']:.2f}\n"
            email_content += f"24小时变化: {eth_analysis['price_change_24h']:.2f}%\n"
            email_content += f"RSI指标: {eth_analysis['rsi']:.2f}\n"
            email_content += f"市场趋势: {eth_analysis['trend']}\n"
        
        # 保存通知内容到文件（用于验证）
        with open("btc_eth_notification.txt", "w", encoding="utf-8") as f:
            f.write(email_subject + "\n\n")
            f.write(email_content)
        
        logger.info(f"BTC/ETH通知内容已保存到 btc_eth_notification.txt")
        return True
    
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n===== 修复脚本测试 =====\n")
    
    # 测试中文编码
    print("\n[测试1] 中文编码测试")
    encoding_result = test_encoding()
    
    # 测试BTC/ETH分析和通知
    print("\n[测试2] BTC/ETH分析和通知测试（模拟数据）")
    btc_eth_result = test_mock_btc_eth()
    
    # 总结测试结果
    print("\n===== 测试结果摘要 =====")
    print(f"中文编码测试: {'成功' if encoding_result else '失败'}")
    print(f"BTC/ETH分析和通知测试: {'成功' if btc_eth_result else '失败'}")
    
    if encoding_result and btc_eth_result:
        print("\n总体测试结果: 成功")
        return 0
    else:
        print("\n总体测试结果: 部分失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 