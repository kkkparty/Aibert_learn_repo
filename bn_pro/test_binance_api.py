#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Binance API连接
简单检查是否能成功请求Binance API
"""

import requests
import json
import time
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_binance_api():
    """测试Binance API连接"""
    
    # Binance API基础URL
    base_url = "https://api.binance.com"
    
    # 测试端点
    endpoints = [
        "/api/v3/ping",  # 简单连接测试
        "/api/v3/time",  # 服务器时间
        "/api/v3/exchangeInfo",  # 交易规则和交易对信息
        "/api/v3/ticker/24hr?symbol=BTCUSDT"  # BTC/USDT 24小时价格统计
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"测试API: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"请求成功! 响应时间: {elapsed:.2f}秒")
                
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    # 对于ping端点，响应是空的
                    if endpoint == "/api/v3/ping":
                        logger.info("Ping测试成功")
                    # 对于时间端点，显示服务器时间
                    elif endpoint == "/api/v3/time":
                        server_time = data.get("serverTime")
                        if server_time:
                            logger.info(f"服务器时间: {server_time}")
                    # 对于24小时统计，显示BTC价格
                    elif "ticker/24hr" in endpoint:
                        price = data.get("lastPrice")
                        if price:
                            logger.info(f"BTC当前价格: ${price}")
                            
                    results.append({
                        "endpoint": endpoint,
                        "status": "成功",
                        "time": f"{elapsed:.2f}秒",
                        "data": "有效JSON响应"
                    })
                except json.JSONDecodeError:
                    logger.error("响应不是有效的JSON格式")
                    results.append({
                        "endpoint": endpoint,
                        "status": "失败",
                        "time": f"{elapsed:.2f}秒",
                        "error": "无效JSON响应"
                    })
            else:
                logger.error(f"请求失败! 状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"错误信息: {error_data}")
                    results.append({
                        "endpoint": endpoint,
                        "status": "失败",
                        "time": f"{elapsed:.2f}秒",
                        "error": f"状态码 {response.status_code}: {error_data}"
                    })
                except:
                    results.append({
                        "endpoint": endpoint,
                        "status": "失败",
                        "time": f"{elapsed:.2f}秒",
                        "error": f"状态码 {response.status_code}"
                    })
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            results.append({
                "endpoint": endpoint,
                "status": "失败",
                "error": str(e)
            })
    
    # 总结结果
    success_count = sum(1 for r in results if r["status"] == "成功")
    logger.info(f"测试完成: {success_count}/{len(endpoints)} 个端点请求成功")
    
    if success_count == len(endpoints):
        logger.info("所有API请求均成功，Binance API可以正常访问!")
        return True
    else:
        logger.warning("部分API请求失败，可能存在连接问题或地区限制")
        return False

if __name__ == "__main__":
    print("开始测试Binance API连接...")
    result = test_binance_api()
    print(f"测试结果: {'成功' if result else '失败'}")
    print("如果测试失败，请考虑使用模拟数据模式或代理") 