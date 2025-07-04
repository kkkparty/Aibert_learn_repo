#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
from binance_filter import BinanceFilter, filter_binance_coins

def test_specific_symbols():
    """测试特定的币种符号是否在币安上可用"""
    test_symbols = ["BTC", "ETH", "USDT", "BNB", "ADA", "DOGE", "SOL", "XRP", 
                   "DOT", "UNI", "BCH", "LTC", "LINK", "MATIC", "XLM", "FAKE1", 
                   "NOTREAL", "TEST123", "IMAGINARY"]
    
    bf = BinanceFilter()
    
    print("\n测试特定币种是否在币安上可用:")
    print("-" * 40)
    for symbol in test_symbols:
        is_supported = bf.is_supported_by_binance(symbol)
        print(f"{symbol:10} | {'支持 ✓' if is_supported else '不支持 ✗'}")

def process_recommendation_file(file_path):
    """处理一个特定的推荐文件，应用币安过滤器"""
    if not os.path.exists(file_path):
        print(f"错误: 文件 {file_path} 不存在")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                results = json.load(f)
                
                # 检查结果格式
                if 'recommendations' not in results:
                    print(f"错误: 文件 {file_path} 不包含推荐列表")
                    return
                
                # 应用币安过滤
                filtered_results = filter_binance_coins(results, True)
                
                # 保存过滤后的结果
                filtered_file_path = file_path.replace('.json', '_binance_only.json')
                with open(filtered_file_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_results, f, ensure_ascii=False, indent=2)
                
                print(f"\n已保存币安过滤后的结果到: {filtered_file_path}")
            else:
                print(f"错误: 文件 {file_path} 格式不支持，请提供JSON文件")
    except Exception as e:
        print(f"处理文件时出错: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    parser = argparse.ArgumentParser(description='测试币安过滤器')
    parser.add_argument('--file', type=str, help='要处理的推荐文件路径')
    parser.add_argument('--test-symbols', action='store_true', help='测试特定币种符号是否在币安上可用')
    
    args = parser.parse_args()
    
    if args.test_symbols:
        test_specific_symbols()
        return
    
    if args.file:
        process_recommendation_file(args.file)
    else:
        # 默认测试最新的推荐文件
        crypto_data_dir = "crypto_data"
        if not os.path.exists(crypto_data_dir):
            print(f"错误: 目录 {crypto_data_dir} 不存在")
            return
            
        recommendation_files = [f for f in os.listdir(crypto_data_dir) 
                              if f.startswith("recommendations_") and f.endswith(".json")]
        
        if not recommendation_files:
            print(f"错误: 在 {crypto_data_dir} 中未找到推荐文件")
            test_specific_symbols()
            return
            
        # 按字母顺序排序，获取最新的文件 (推荐文件名包含时间戳，所以这样排序可以获取最新的)
        latest_file = sorted(recommendation_files)[-1]
        file_path = os.path.join(crypto_data_dir, latest_file)
        
        print(f"处理最新的推荐文件: {file_path}")
        process_recommendation_file(file_path)

if __name__ == "__main__":
    main() 