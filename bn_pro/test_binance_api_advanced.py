#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
高级Binance API测试脚本
尝试多种方法访问Binance API
"""

import requests
import json
import time
import logging
import random
import os
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Binance API基础URL和备用URL
BINANCE_URLS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api4.binance.com"
]

# 其他交易所API (用于比较)
OTHER_EXCHANGES = [
    {"name": "OKX", "url": "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"},
    {"name": "Huobi", "url": "https://api.huobi.pro/market/detail/merged?symbol=btcusdt"},
    {"name": "Bybit", "url": "https://api.bybit.com/v2/public/tickers?symbol=BTCUSD"}
]

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

def get_random_headers():
    """生成随机请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

def test_direct_access():
    """测试直接访问Binance API"""
    logger.info("=== 测试直接访问Binance API ===")
    
    for base_url in BINANCE_URLS:
        logger.info(f"测试Binance URL: {base_url}")
        
        # 测试端点
        endpoints = [
            "/api/v3/ping",  # 简单连接测试
            "/api/v3/time",  # 服务器时间
            "/api/v3/ticker/24hr?symbol=BTCUSDT"  # BTC/USDT 24小时价格统计
        ]
        
        success_count = 0
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            logger.info(f"测试API: {url}")
            
            try:
                headers = get_random_headers()
                start_time = time.time()
                response = requests.get(url, headers=headers, timeout=10)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    logger.info(f"请求成功! 响应时间: {elapsed:.2f}秒")
                    success_count += 1
                    
                    # 解析响应
                    try:
                        data = response.json()
                        if endpoint == "/api/v3/ticker/24hr?symbol=BTCUSDT":
                            price = data.get("lastPrice")
                            if price:
                                logger.info(f"BTC当前价格: ${price}")
                    except:
                        pass
                else:
                    logger.error(f"请求失败! 状态码: {response.status_code}")
                    try:
                        error_data = response.json()
                        logger.error(f"错误信息: {error_data}")
                    except:
                        logger.error(f"无法解析错误响应: {response.text}")
            except Exception as e:
                logger.error(f"请求异常: {e}")
        
        logger.info(f"URL {base_url} 测试结果: {success_count}/{len(endpoints)} 个端点成功")
        
        if success_count > 0:
            logger.info(f"找到可用的Binance API URL: {base_url}")
            return base_url
    
    logger.warning("所有Binance API URL均无法直接访问")
    return None

def test_other_exchanges():
    """测试其他交易所API"""
    logger.info("=== 测试其他交易所API ===")
    
    for exchange in OTHER_EXCHANGES:
        name = exchange["name"]
        url = exchange["url"]
        
        logger.info(f"测试 {name} API: {url}")
        
        try:
            headers = get_random_headers()
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"{name} API请求成功! 响应时间: {elapsed:.2f}秒")
                
                # 尝试解析价格
                try:
                    data = response.json()
                    price = None
                    
                    if name == "OKX":
                        if data.get("data") and len(data["data"]) > 0:
                            price = data["data"][0].get("last")
                    elif name == "Huobi":
                        if data.get("tick"):
                            price = data["tick"].get("close")
                    elif name == "Bybit":
                        if data.get("result") and len(data["result"]) > 0:
                            price = data["result"][0].get("last_price")
                    
                    if price:
                        logger.info(f"{name} BTC当前价格: ${price}")
                except Exception as e:
                    logger.error(f"解析{name}价格失败: {e}")
            else:
                logger.error(f"{name} API请求失败! 状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"{name} API请求异常: {e}")

def test_binance_websocket():
    """测试Binance WebSocket API"""
    logger.info("=== 测试Binance WebSocket API ===")
    
    try:
        import websocket
        import threading
        import time
        
        # WebSocket连接URL
        ws_url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
        
        # 标记是否收到数据
        received_data = False
        
        def on_message(ws, message):
            nonlocal received_data
            logger.info("收到WebSocket消息")
            try:
                data = json.loads(message)
                price = data.get("c")  # 当前价格
                if price:
                    logger.info(f"WebSocket BTC当前价格: ${price}")
                received_data = True
                ws.close()
            except Exception as e:
                logger.error(f"解析WebSocket消息失败: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket错误: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket连接关闭")
        
        def on_open(ws):
            logger.info("WebSocket连接已建立")
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(ws_url,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        ws.on_open = on_open
        
        # 在后台线程中运行WebSocket
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # 等待数据或超时
        timeout = 10
        start_time = time.time()
        while not received_data and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # 检查是否收到数据
        if received_data:
            logger.info("成功通过WebSocket获取Binance数据")
            return True
        else:
            logger.warning("WebSocket连接超时，未收到数据")
            return False
    except ImportError:
        logger.error("未安装websocket-client库，无法测试WebSocket API")
        logger.info("可以通过运行 'pip install websocket-client' 安装")
        return False
    except Exception as e:
        logger.error(f"WebSocket测试失败: {e}")
        return False

def test_binance_v3_api():
    """测试Binance V3 API的不同端点"""
    logger.info("=== 测试Binance V3 API的不同端点 ===")
    
    base_url = "https://api.binance.com"
    
    # 测试不同的端点
    endpoints = [
        "/api/v3/exchangeInfo",  # 交易规则和交易对
        "/api/v3/ticker/price?symbol=BTCUSDT",  # BTC价格
        "/api/v3/ticker/bookTicker?symbol=BTCUSDT",  # BTC最优买卖价
        "/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1"  # BTC K线数据
    ]
    
    success_count = 0
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"测试API: {url}")
        
        try:
            headers = get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"请求成功!")
                success_count += 1
            else:
                logger.error(f"请求失败! 状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"请求异常: {e}")
    
    logger.info(f"V3 API测试结果: {success_count}/{len(endpoints)} 个端点成功")
    return success_count > 0

def main():
    """主函数"""
    logger.info("开始高级Binance API测试...")
    
    # 测试直接访问
    direct_url = test_direct_access()
    
    # 如果直接访问失败，测试其他交易所
    if not direct_url:
        logger.info("直接访问Binance API失败，测试其他交易所...")
        test_other_exchanges()
    
    # 测试WebSocket API
    try:
        websocket_result = test_binance_websocket()
    except:
        websocket_result = False
    
    # 测试V3 API的不同端点
    v3_result = test_binance_v3_api()
    
    # 总结结果
    logger.info("\n=== 测试结果总结 ===")
    if direct_url:
        logger.info(f"✅ 直接访问Binance API成功，可用URL: {direct_url}")
    else:
        logger.info("❌ 直接访问Binance API失败")
    
    if websocket_result:
        logger.info("✅ Binance WebSocket API测试成功")
    else:
        logger.info("❌ Binance WebSocket API测试失败")
    
    if v3_result:
        logger.info("✅ Binance V3 API测试成功")
    else:
        logger.info("❌ Binance V3 API测试失败")
    
    # 最终结论
    if direct_url or websocket_result or v3_result:
        logger.info("\n结论: 可以通过某些方式访问Binance API")
        return True
    else:
        logger.info("\n结论: 无法通过测试的方法访问Binance API，建议使用模拟数据模式")
        return False

if __name__ == "__main__":
    print("开始高级Binance API测试...")
    result = main()
    print(f"\n测试结果: {'成功' if result else '失败'}")
    if not result:
        print("建议使用模拟数据模式运行系统") 