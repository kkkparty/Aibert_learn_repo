#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单SOCKS5代理测试脚本
设计用于快速测试单个代理是否可用
"""

import sys
import socks
import socket
import urllib.request
import urllib.parse
import requests
import time
from datetime import datetime

def log(msg):
    """带时间戳的日志输出"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_socks_direct(proxy_str, test_url="https://api.ipify.org?format=json", timeout=15):
    """直接使用PySocks测试"""
    log(f"使用PySocks直接测试: {proxy_str}")
    
    # 解析代理字符串
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
    
    # 提取代理参数
    host = parts[0]
    try:
        port = int(parts[1])
    except ValueError:
        log(f"无效的端口号: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    password = parts[-1]
    username = ':'.join(parts[2:-1])
    
    log(f"代理参数: {host}:{port}, 用户名: {username}, 密码: {password}")
    
    # 保存原始socket
    orig_socket = socket.socket
    
    try:
        # 设置SOCKS5代理
        socks.set_default_proxy(
            proxy_type=socks.SOCKS5,
            addr=host,
            port=port,
            username=username,
            password=password
        )
        # 替换socket实现
        socket.socket = socks.socksocket
        
        # 创建请求
        log(f"尝试连接到: {test_url}")
        response = urllib.request.urlopen(test_url, timeout=timeout)
        
        # 读取响应
        data = response.read().decode('utf-8')
        log(f"成功! 响应: {data}")
        return True
    except Exception as e:
        log(f"测试失败: {e}")
        return False
    finally:
        # 恢复原始socket
        socket.socket = orig_socket

def test_requests(proxy_str, test_url="https://api.ipify.org?format=json", timeout=15):
    """使用requests库测试"""
    log(f"使用requests库测试: {proxy_str}")
    
    # 解析代理字符串
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
    
    # 提取代理参数
    host = parts[0]
    try:
        port = int(parts[1])
    except ValueError:
        log(f"无效的端口号: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    password = parts[-1]
    username = ':'.join(parts[2:-1])
    
    # URL编码用户名和密码
    encoded_username = urllib.parse.quote(username)
    encoded_password = urllib.parse.quote(password)
    
    # 构建代理URL
    proxy_url = f"socks5://{encoded_username}:{encoded_password}@{host}:{port}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    # 添加请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        log(f"代理URL: {proxy_url}")
        log(f"尝试连接到: {test_url}")
        
        # 创建会话
        session = requests.Session()
        session.proxies = proxies
        session.headers.update(headers)
        
        # 发送请求
        response = session.get(test_url, timeout=timeout)
        
        # 检查响应
        log(f"响应状态码: {response.status_code}")
        log(f"响应内容: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        log(f"测试失败: {e}")
        return False

def test_all_methods(proxy_str):
    """测试所有方法"""
    # 测试URLs
    urls = [
        "https://api.ipify.org?format=json", 
        "http://httpbin.org/ip",
        "http://ip-api.com/json"
    ]
    
    log(f"开始全面测试代理: {proxy_str}")
    success = False
    
    # 测试所有URL组合
    for url in urls:
        log(f"\n------- 测试URL: {url} -------")
        
        # 使用PySocks
        log("\n>> 方法1: PySocks")
        if test_socks_direct(proxy_str, url):
            log("方法1成功!")
            success = True
        else:
            log("方法1失败")
        
        time.sleep(1)  # 短暂暂停
        
        # 使用requests
        log("\n>> 方法2: Requests")
        if test_requests(proxy_str, url):
            log("方法2成功!")
            success = True
        else:
            log("方法2失败")
            
        # 尝试socks5h协议
        log("\n>> 方法3: Requests + socks5h协议")
        parts = proxy_str.split(':')
        if len(parts) >= 4:
            host = parts[0]
            port = parts[1]
            password = parts[-1]
            username = ':'.join(parts[2:-1])
            
            # URL编码
            encoded_username = urllib.parse.quote(username)
            encoded_password = urllib.parse.quote(password)
            
            # 使用socks5h
            proxy_url = f"socks5h://{encoded_username}:{encoded_password}@{host}:{port}"
            proxies = {'http': proxy_url, 'https': proxy_url}
            
            try:
                log(f"使用socks5h代理: {proxy_url}")
                response = requests.get(url, proxies=proxies, timeout=15)
                log(f"响应状态码: {response.status_code}")
                log(f"响应内容: {response.text}")
                if response.status_code == 200:
                    log("方法3成功!")
                    success = True
                else:
                    log("方法3失败 - 状态码不是200")
            except Exception as e:
                log(f"方法3失败: {e}")
                
        time.sleep(2)  # 稍长的暂停，避免频率限制
    
    return success

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <代理字符串>")
        print(f"例如: {sys.argv[0]} 123.123.123.123:1080:username:password")
        return
    
    proxy_str = sys.argv[1]
    log(f"测试代理: {proxy_str}")
    
    # 如果有额外参数，只测试特定方法
    if len(sys.argv) > 2 and sys.argv[2] == "direct":
        test_socks_direct(proxy_str)
    elif len(sys.argv) > 2 and sys.argv[2] == "requests":
        test_requests(proxy_str)
    else:
        # 否则测试所有方法
        test_all_methods(proxy_str)

if __name__ == "__main__":
    main() 