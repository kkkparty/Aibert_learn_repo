#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接测试360s5 SOCKS5代理连接
"""

import socks
import socket
import urllib.request
import ssl
from urllib.error import URLError
import sys
import argparse
import requests
import json

def test_direct_socks(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    直接使用SOCKS库测试代理
    
    格式: hostname:port:username:password
    """
    parts = proxy_str.split(':')
    if len(parts) < 4:
        print(f"无效的代理格式: {proxy_str}")
        print("正确格式: hostname:port:username:password")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        print(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    print(f"测试代理: {proxy_host}:{proxy_port}")
    print(f"用户名: {proxy_username}")
    print(f"密码: {proxy_password}")
    
    # 保存原始socket
    default_socket = socket.socket
    
    try:
        # 设置SOCKS5代理
        socks.set_default_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_host,
            port=proxy_port,
            username=proxy_username,
            password=proxy_password
        )
        socket.socket = socks.socksocket
        
        # 尝试连接
        print(f"尝试连接到: {test_url}")
        response = urllib.request.urlopen(test_url, timeout=20)
        data = response.read().decode('utf-8')
        print(f"响应: {data}")
        
        # 尝试解析JSON
        try:
            json_data = json.loads(data)
            print(f"测试成功! 您的IP: {json_data.get('ip', 'unknown')}")
            return True
        except:
            print(f"收到响应，但不是JSON格式: {data[:100]}")
            return True
    except Exception as e:
        print(f"代理测试失败: {e}")
        if "socks" in str(e).lower():
            print("SOCKS代理错误，可能是认证问题或代理不可用")
        elif "timeout" in str(e).lower():
            print("连接超时，代理响应太慢")
        else:
            print(f"详细错误信息: {e}")
            print(f"错误类型: {type(e)}")
        return False
    finally:
        # 恢复原始socket
        socket.socket = default_socket

def test_requests_socks(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    使用requests库和SOCKS5代理
    """
    parts = proxy_str.split(':')
    if len(parts) < 4:
        print(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        print(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    # 构建代理URL - 尝试不同的格式
    # 格式1: socks5://username:password@hostname:port
    proxy_url_1 = f"socks5://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
    
    # 格式2: socks5h://username:password@hostname:port (h表示主机名由代理解析)
    proxy_url_2 = f"socks5h://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
    
    print("测试格式1:", proxy_url_1)
    try:
        proxies = {
            'http': proxy_url_1,
            'https': proxy_url_1
        }
        response = requests.get(test_url, proxies=proxies, timeout=20)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        print("测试成功! (格式1)")
        return True
    except Exception as e:
        print(f"测试失败 (格式1): {e}")
    
    print("\n测试格式2:", proxy_url_2)
    try:
        proxies = {
            'http': proxy_url_2,
            'https': proxy_url_2
        }
        response = requests.get(test_url, proxies=proxies, timeout=20)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        print("测试成功! (格式2)")
        return True
    except Exception as e:
        print(f"测试失败 (格式2): {e}")
    
    return False

def main():
    parser = argparse.ArgumentParser(description='测试360s5 SOCKS5代理')
    parser.add_argument('proxy', help='代理字符串 (格式: hostname:port:username:password)')
    parser.add_argument('--url', default='https://api.ipify.org?format=json', help='测试URL')
    
    args = parser.parse_args()
    
    print("====== 使用PySocks直接测试 ======")
    direct_result = test_direct_socks(args.proxy, args.url)
    
    print("\n====== 使用Requests库测试 ======")
    requests_result = test_requests_socks(args.proxy, args.url)
    
    print("\n====== 测试结果 ======")
    print(f"PySocks直接测试: {'成功' if direct_result else '失败'}")
    print(f"Requests库测试: {'成功' if requests_result else '失败'}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python direct_socks5_test.py hostname:port:username:password [--url TEST_URL]")
    else:
        main() 