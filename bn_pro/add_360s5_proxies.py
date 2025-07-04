#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
添加360s5格式的代理到代理池
格式: hostname:port:username:password
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import argparse
from proxy_manager import ProxyManager

def convert_proxy_format(proxy_str):
    """
    将hostname:port:username:password格式转换为
    socks5://username:password@hostname:port格式
    """
    parts = proxy_str.split(':')
    if len(parts) >= 4:
        hostname = parts[0]
        port = parts[1]
        # 用户名可能包含冒号，所以我们需要从后向前解析
        password = parts[-1]
        username = ':'.join(parts[2:-1])
        return f"socks5://{username}:{password}@{hostname}:{port}"
    else:
        print(f"无效的代理格式: {proxy_str}")
        return None

def add_proxies_from_file(file_path, skip_testing=True):
    """从文件添加360s5格式的代理"""
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
    
    # 转换代理格式
    converted_proxies = []
    for proxy in proxy_list:
        converted = convert_proxy_format(proxy)
        if converted:
            converted_proxies.append(converted)
    
    print(f"成功转换 {len(converted_proxies)}/{len(proxy_list)} 个代理格式")
    
    if skip_testing:
        # 直接保存到代理文件
        save_proxies_directly(converted_proxies)
        return True
    else:
        # 测试后添加
        proxy_manager = ProxyManager()
        
        added_count = 0
        for proxy in converted_proxies:
            print(f"测试添加代理: {proxy}")
            if proxy_manager.add_proxy(proxy):
                added_count += 1
        
        print(f"成功添加 {added_count}/{len(converted_proxies)} 个代理")
        print(f"当前代理池中共有 {len(proxy_manager.proxies)} 个代理")
        
        return True

def save_proxies_directly(converted_proxies):
    """直接将代理保存到文件"""
    # 初始化代理管理器只为了获取文件路径
    proxy_manager = ProxyManager()
    proxy_file = proxy_manager.proxy_file
    
    # 解析代理字符串为字典
    parsed_proxies = []
    for proxy in converted_proxies:
        if proxy.startswith('socks5://'):
            # 解析SOCKS5代理
            config = proxy_manager.parse_socks5_proxy(proxy)
            if config:
                parsed_proxies.append(config)
                print(f"已解析SOCKS5代理: {proxy}")
            else:
                print(f"无法解析代理: {proxy}")
    
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

def parse_clipboard_text():
    """
    从剪贴板解析代理列表
    格式: 
    aus.360s5.com:3680:95588794-zone-custom-sessid-GY1sc8wq-sessTime-15:X9O1AUFL
    aus.360s5.com:3680:95588794-zone-custom-sessid-S1RP6RE6-sessTime-15:X9O1AUFL
    ...
    """
    try:
        import pyperclip
        text = pyperclip.paste()
        
        # 按行分割
        lines = text.strip().split('\n')
        
        # 过滤空行
        proxy_list = [line.strip() for line in lines if line.strip()]
        
        if proxy_list:
            print(f"从剪贴板读取了 {len(proxy_list)} 个代理")
            
            # 创建临时文件
            tmp_file = "temp_proxies.txt"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(proxy_list))
            
            print(f"已将代理保存到临时文件: {tmp_file}")
            return tmp_file
        else:
            print("剪贴板中没有有效的代理")
            return None
    except ImportError:
        print("无法导入pyperclip模块，请安装: pip install pyperclip")
        return None
    except Exception as e:
        print(f"从剪贴板读取代理时出错: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='添加360s5格式的代理到代理池')
    parser.add_argument('--file', '-f', help='代理文件路径')
    parser.add_argument('--clipboard', '-c', action='store_true', help='从剪贴板读取代理')
    parser.add_argument('--test', '-t', action='store_true', help='测试代理有效性')
    
    args = parser.parse_args()
    
    file_path = args.file
    
    # 如果指定了从剪贴板读取
    if args.clipboard:
        file_path = parse_clipboard_text()
    
    if file_path:
        add_proxies_from_file(file_path, skip_testing=not args.test) 