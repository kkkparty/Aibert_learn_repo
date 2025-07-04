#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将代理文件中的代理添加到代理池
"""

import os
import sys
import json
import argparse
from datetime import datetime
from proxy_manager import ProxyManager

def add_proxies_from_file(file_path, skip_testing=False):
    """
    从文件添加代理
    
    参数:
    file_path -- 代理文件路径
    skip_testing -- 是否跳过测试直接添加
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        proxy_list = f.read().strip().split('\n')
    
    # 过滤空行
    proxy_list = [p for p in proxy_list if p.strip()]
    
    print(f"从文件读取了 {len(proxy_list)} 个代理")
    
    if skip_testing:
        # 不测试，直接保存到代理文件
        save_proxies_directly(proxy_list)
        return True
    
    # 初始化代理管理器并测试后添加
    proxy_manager = ProxyManager()
    
    # 添加代理
    added_count = 0
    for proxy in proxy_list:
        print(f"测试添加代理: {proxy}")
        if proxy_manager.add_proxy(proxy):
            added_count += 1
    
    print(f"成功添加 {added_count}/{len(proxy_list)} 个代理")
    print(f"当前代理池中共有 {len(proxy_manager.proxies)} 个代理")
    
    return True

def save_proxies_directly(proxy_list):
    """直接将代理列表保存到文件，跳过测试"""
    from pathlib import Path
    
    # 初始化代理管理器只为了获取文件路径
    proxy_manager = ProxyManager()
    proxy_file = proxy_manager.proxy_file
    
    # 解析代理字符串为字典
    parsed_proxies = []
    for proxy in proxy_list:
        if proxy.startswith('socks5://'):
            # 解析SOCKS5代理
            config = proxy_manager.parse_socks5_proxy(proxy)
            if config:
                parsed_proxies.append(config)
                print(f"已解析SOCKS5代理: {proxy}")
            else:
                print(f"无法解析代理: {proxy}")
        else:
            # HTTP代理
            parsed_proxies.append({"http": proxy, "https": proxy})
            print(f"已解析HTTP代理: {proxy}")
    
    # 保存到代理文件
    data = {
        'proxies': parsed_proxies,
        'last_updated': datetime.now().isoformat()
    }
    
    # 确保目录存在
    Path(os.path.dirname(proxy_file)).mkdir(parents=True, exist_ok=True)
    
    with open(proxy_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已直接保存 {len(parsed_proxies)} 个代理到文件: {proxy_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从文件添加代理到代理池')
    parser.add_argument('file_path', help='代理文件路径')
    parser.add_argument('--skip-testing', '-s', action='store_true', help='跳过测试，直接添加代理')
    
    args = parser.parse_args()
    add_proxies_from_file(args.file_path, args.skip_testing) 