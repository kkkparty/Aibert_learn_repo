#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试使用代理的Binance API连接
尝试通过代理服务器访问Binance API
"""

import requests
import json
import time
import logging
import random
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 免费代理列表 (仅用于测试，实际使用时应使用更可靠的代理)
FREE_PROXIES = [
    "http://47.243.242.70:8080",
    "http://47.243.175.55:8080",
    "http://47.243.124.21:8080",
    "http://8.219.43.134:8080",
    "http://47.243.50.83:8080",
    "http://8.219.5.240:8080",
    "http://47.242.202.128:8080",
    "http://47.242.78.205:8080",
    "http://47.243.242.70:3128",
    "http://47.242.78.205:3128",
    "http://8.219.43.134:3128",
    "http://47.243.124.21:3128",
    "http://47.243.175.55:3128",
    "http://47.243.50.83:3128"
]

def test_binance_api_with_proxy(proxy=None):
    """测试使用代理的Binance API连接"""
    
    # Binance API基础URL
    base_url = "https://api.binance.com"
    
    # 测试端点
    endpoints = [
        "/api/v3/ping",  # 简单连接测试
        "/api/v3/time",  # 服务器时间
        "/api/v3/ticker/24hr?symbol=BTCUSDT"  # BTC/USDT 24小时价格统计
    ]
    
    # 设置代理
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
        logger.info(f"使用代理: {proxy}")
    else:
        logger.info("不使用代理")
    
    # 设置请求头，模拟不同的用户代理
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    
    success_count = 0
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"测试API: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                headers=headers,
                proxies=proxies, 
                timeout=15
            )
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
                    
                    success_count += 1
                except json.JSONDecodeError:
                    logger.error("响应不是有效的JSON格式")
            else:
                logger.error(f"请求失败! 状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"错误信息: {error_data}")
                except:
                    logger.error(f"无法解析错误响应: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
    
    # 总结结果
    logger.info(f"测试完成: {success_count}/{len(endpoints)} 个端点请求成功")
    
    if success_count == len(endpoints):
        logger.info("所有API请求均成功，Binance API可以通过此代理正常访问!")
        return True
    else:
        logger.warning("部分API请求失败，此代理可能不可用")
        return False

def test_multiple_proxies():
    """测试多个代理"""
    logger.info("开始测试多个代理...")
    
    # 首先测试不使用代理
    logger.info("=== 测试不使用代理 ===")
    direct_result = test_binance_api_with_proxy(None)
    
    if direct_result:
        logger.info("不使用代理也能成功访问Binance API!")
        return True
    
    # 测试免费代理列表
    working_proxies = []
    for i, proxy in enumerate(FREE_PROXIES):
        logger.info(f"=== 测试代理 {i+1}/{len(FREE_PROXIES)}: {proxy} ===")
        result = test_binance_api_with_proxy(proxy)
        if result:
            working_proxies.append(proxy)
            logger.info(f"找到可用代理: {proxy}")
            # 找到一个可用代理就可以了
            break
    
    if working_proxies:
        logger.info(f"测试完成，找到 {len(working_proxies)} 个可用代理")
        logger.info(f"可用代理列表: {working_proxies}")
        return True
    else:
        logger.warning("测试完成，未找到可用代理")
        return False

def test_binance_alternative_domains():
    """测试Binance的替代域名"""
    logger.info("测试Binance替代域名...")
    
    # Binance的一些替代域名
    alternative_domains = [
        "https://api1.binance.com",
        "https://api2.binance.com",
        "https://api3.binance.com"
    ]
    
    success = False
    
    for domain in alternative_domains:
        logger.info(f"测试域名: {domain}")
        url = f"{domain}/api/v3/ping"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"域名 {domain} 可访问!")
                success = True
                break
            else:
                logger.warning(f"域名 {domain} 返回状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"域名 {domain} 访问失败: {e}")
    
    return success

if __name__ == "__main__":
    print("开始测试Binance API连接...")
    
    # 首先测试替代域名
    print("\n=== 测试Binance替代域名 ===")
    alt_domain_result = test_binance_alternative_domains()
    
    if not alt_domain_result:
        # 如果替代域名不可用，测试代理
        print("\n=== 测试代理访问 ===")
        proxy_result = test_multiple_proxies()
        
        if proxy_result:
            print("\n总结: 通过代理可以成功访问Binance API")
        else:
            print("\n总结: 无法通过测试的方法访问Binance API")
    else:
        print("\n总结: 通过替代域名可以成功访问Binance API") 