#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SOCKS5代理修复工具
解决SOCKS5代理连接问题，自动诊断并生成固定代码
"""

import os
import sys
import socket
import socks
import json
import time
import urllib.request
import urllib.parse
import requests
import ssl
import random
import re
import argparse
from datetime import datetime
from pathlib import Path

# 全局变量
DEBUG = True

def log(msg, level="INFO"):
    """打印带时间戳的日志"""
    level_prefixes = {
        "INFO": "",
        "SUCCESS": "[✓] ",
        "ERROR": "[✗] ",
        "WARNING": "[!] ",
        "DEBUG": "[D] "
    }
    prefix = level_prefixes.get(level, "")
    
    if level == "DEBUG" and not DEBUG:
        return
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {prefix}{msg}")

# SOCKS5代理连接错误及其解决方案
COMMON_ERRORS = {
    "SOCKS5 proxy server sent invalid data": {
        "description": "代理服务器返回了不符合SOCKS5协议的数据。这通常表明身份验证失败或代理服务器配置有问题。",
        "solutions": [
            "检查用户名和密码是否正确",
            "URL编码用户名和密码",
            "尝试不同的身份验证方法",
            "联系代理服务提供商确认正确的连接方法"
        ]
    },
    "timed out": {
        "description": "连接超时。代理服务器可能无响应或网络不稳定。",
        "solutions": [
            "确认代理服务器是否在线",
            "检查网络连接",
            "增加超时时间",
            "尝试不同的代理服务器"
        ]
    },
    "Connection refused": {
        "description": "代理服务器拒绝了连接请求。",
        "solutions": [
            "确认代理服务器地址和端口是否正确",
            "检查代理服务器是否在线",
            "确认您是否有权访问此代理服务器"
        ]
    },
    "Name or service not known": {
        "description": "无法解析代理服务器的主机名。",
        "solutions": [
            "检查代理服务器主机名是否正确",
            "确认DNS设置是否正确",
            "使用IP地址而不是主机名"
        ]
    }
}

def test_socks5_basic(proxy_config):
    """
    基本SOCKS5测试
    使用最基本的PySocks配置测试连接
    """
    log(f"测试基本SOCKS5连接: {proxy_config['host']}:{proxy_config['port']}")
    
    # 保存原始socket
    orig_socket = socket.socket
    
    try:
        # 设置代理
        socks.set_default_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_config['host'],
            port=proxy_config['port'],
            username=proxy_config.get('username'),
            password=proxy_config.get('password')
        )
        socket.socket = socks.socksocket
        
        # 测试连接
        test_url = "http://httpbin.org/ip"
        log(f"连接到: {test_url}", "DEBUG")
        
        req = urllib.request.Request(test_url)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
    except Exception as e:
        log(f"基本测试失败: {str(e)}", "ERROR")
        return False, str(e)
    finally:
        # 恢复原始socket
        socket.socket = orig_socket

def test_socks5_requests(proxy_config):
    """使用requests库测试SOCKS5代理"""
    log(f"使用requests库测试SOCKS5连接")
    
    # 构建代理URL
    if proxy_config.get('username'):
        # URL编码用户名和密码
        username = urllib.parse.quote(proxy_config['username'])
        password = urllib.parse.quote(proxy_config['password'])
        proxy_url = f"socks5://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
    else:
        proxy_url = f"socks5://{proxy_config['host']}:{proxy_config['port']}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        test_url = "http://httpbin.org/ip"
        log(f"代理URL: {proxy_url}", "DEBUG")
        log(f"连接到: {test_url}", "DEBUG")
        
        response = requests.get(test_url, proxies=proxies, timeout=15)
        if response.status_code == 200:
            data = response.json()
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
        else:
            log(f"请求失败，状态码: {response.status_code}", "ERROR")
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        log(f"Requests测试失败: {str(e)}", "ERROR")
        return False, str(e)

def test_socks5h_requests(proxy_config):
    """使用socks5h协议测试代理"""
    log(f"使用socks5h协议测试连接")
    
    # 构建代理URL
    if proxy_config.get('username'):
        # URL编码用户名和密码
        username = urllib.parse.quote(proxy_config['username'])
        password = urllib.parse.quote(proxy_config['password'])
        proxy_url = f"socks5h://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
    else:
        proxy_url = f"socks5h://{proxy_config['host']}:{proxy_config['port']}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        test_url = "http://httpbin.org/ip"
        log(f"代理URL: {proxy_url}", "DEBUG")
        log(f"连接到: {test_url}", "DEBUG")
        
        response = requests.get(test_url, proxies=proxies, timeout=15)
        if response.status_code == 200:
            data = response.json()
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
        else:
            log(f"请求失败，状态码: {response.status_code}", "ERROR")
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        log(f"socks5h测试失败: {str(e)}", "ERROR")
        return False, str(e)

def test_custom_handler(proxy_config):
    """使用自定义SOCKS5处理器测试"""
    log(f"使用自定义处理器测试连接")
    
    try:
        # 自定义SocksiPy处理器
        class SocksiPyConnection(urllib.request.HTTPConnection):
            def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True, username=None, password=None, *args, **kwargs):
                self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
                urllib.request.HTTPConnection.__init__(self, *args, **kwargs)

            def connect(self):
                self.sock = socks.socksocket()
                self.sock.setproxy(*self.proxyargs)
                if type(self.timeout) in (int, float):
                    self.sock.settimeout(self.timeout)
                self.sock.connect((self.host, self.port))

        class SocksiPyConnectionS(urllib.request.HTTPSConnection):
            def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True, username=None, password=None, *args, **kwargs):
                self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
                urllib.request.HTTPSConnection.__init__(self, *args, **kwargs)

            def connect(self):
                sock = socks.socksocket()
                sock.setproxy(*self.proxyargs)
                if type(self.timeout) in (int, float):
                    sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                
                try:
                    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)
                except AttributeError:
                    context = ssl.create_default_context()
                    self.sock = context.wrap_socket(sock, server_hostname=self.host)

        class SocksiPyHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kw = kwargs
                urllib.request.HTTPHandler.__init__(self)
                urllib.request.HTTPSHandler.__init__(self)

            def http_open(self, req):
                def build(host, port=None, timeout=0, **kwargs):
                    kw = merge_dict(self.kw, kwargs)
                    conn = SocksiPyConnection(*self.args, host=host, port=port, timeout=timeout, **kw)
                    return conn
                return self.do_open(build, req)

            def https_open(self, req):
                def build(host, port=None, timeout=0, **kwargs):
                    kw = merge_dict(self.kw, kwargs)
                    conn = SocksiPyConnectionS(*self.args, host=host, port=port, timeout=timeout, **kw)
                    return conn
                return self.do_open(build, req)

        def merge_dict(a, b):
            d = a.copy()
            d.update(b)
            return d
        
        # 创建opener
        opener = urllib.request.build_opener(
            SocksiPyHandler(
                socks.SOCKS5, 
                proxy_config['host'], 
                proxy_config['port'], 
                username=proxy_config.get('username'), 
                password=proxy_config.get('password')
            )
        )
        
        # 设置为默认opener
        urllib.request.install_opener(opener)
        
        # 测试连接
        test_url = "http://httpbin.org/ip"
        log(f"连接到: {test_url}", "DEBUG")
        
        req = urllib.request.Request(test_url)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
    except Exception as e:
        log(f"自定义处理器测试失败: {str(e)}", "ERROR")
        return False, str(e)

def test_session_connection(proxy_config):
    """使用Session测试连接"""
    log(f"使用Session测试连接")
    
    # 构建代理URL
    if proxy_config.get('username'):
        # URL编码用户名和密码
        username = urllib.parse.quote(proxy_config['username'])
        password = urllib.parse.quote(proxy_config['password'])
        proxy_url = f"socks5://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
    else:
        proxy_url = f"socks5://{proxy_config['host']}:{proxy_config['port']}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    # 创建会话
    session = requests.Session()
    session.proxies = proxies
    
    # 添加请求头
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        test_url = "http://httpbin.org/ip"
        log(f"Session连接到: {test_url}", "DEBUG")
        
        response = session.get(test_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
        else:
            log(f"Session请求失败，状态码: {response.status_code}", "ERROR")
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        log(f"Session测试失败: {str(e)}", "ERROR")
        return False, str(e)

def test_http_proxy_fallback(proxy_config):
    """尝试使用HTTP代理格式进行测试"""
    log(f"尝试使用HTTP代理格式")
    
    # 构建代理URL
    if proxy_config.get('username'):
        # URL编码用户名和密码
        username = urllib.parse.quote(proxy_config['username'])
        password = urllib.parse.quote(proxy_config['password'])
        http_proxy_url = f"http://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
    else:
        http_proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
    
    proxies = {
        'http': http_proxy_url,
        'https': http_proxy_url
    }
    
    try:
        test_url = "http://httpbin.org/ip"
        log(f"HTTP代理URL: {http_proxy_url}", "DEBUG")
        log(f"连接到: {test_url}", "DEBUG")
        
        response = requests.get(test_url, proxies=proxies, timeout=15)
        if response.status_code == 200:
            data = response.json()
            log(f"成功! 显示的IP: {data.get('origin')}", "SUCCESS")
            return True, data
        else:
            log(f"HTTP代理请求失败，状态码: {response.status_code}", "ERROR")
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        log(f"HTTP代理测试失败: {str(e)}", "ERROR")
        return False, str(e)

def get_proxy_config_from_string(proxy_str):
    """从代理字符串中提取配置"""
    parts = proxy_str.split(':')
    if len(parts) < 2:
        log(f"无效的代理格式: {proxy_str}", "ERROR")
        return None
    
    # 提取主机和端口
    host = parts[0]
    try:
        port = int(parts[1])
    except ValueError:
        log(f"无效的端口号: {parts[1]}", "ERROR")
        return None
    
    # 检查是否有用户名和密码
    if len(parts) >= 4:
        # 用户名可能包含冒号，密码是最后一部分
        password = parts[-1]
        username = ':'.join(parts[2:-1])
        return {
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }
    else:
        return {
            'host': host,
            'port': port
        }

def full_proxy_test(proxy_str):
    """执行全面的代理测试"""
    log(f"开始全面测试代理: {proxy_str}")
    
    # 解析代理配置
    proxy_config = get_proxy_config_from_string(proxy_str)
    if not proxy_config:
        return False, None, "无效的代理配置"
    
    # 记录配置
    log(f"代理主机: {proxy_config['host']}")
    log(f"代理端口: {proxy_config['port']}")
    if proxy_config.get('username'):
        log(f"用户名: {proxy_config['username']}")
        log(f"密码: {'*' * len(proxy_config['password'])}")
    
    # 定义测试方法
    test_methods = [
        ("基本SOCKS5", test_socks5_basic),
        ("Requests SOCKS5", test_socks5_requests),
        ("SOCKS5h协议", test_socks5h_requests),
        ("自定义处理器", test_custom_handler),
        ("Session连接", test_session_connection),
        ("HTTP代理回退", test_http_proxy_fallback)
    ]
    
    # 运行所有测试
    successful_methods = []
    error_messages = {}
    success = False
    result_data = None
    
    for method_name, test_func in test_methods:
        log(f"\n----- 测试方法: {method_name} -----")
        try:
            method_success, data = test_func(proxy_config)
            if method_success:
                log(f"{method_name}测试成功!", "SUCCESS")
                successful_methods.append(method_name)
                if not result_data:
                    result_data = data
                success = True
            else:
                if isinstance(data, str):
                    error_messages[method_name] = data
                    
            # 避免频率限制
            time.sleep(2) 
        except Exception as e:
            log(f"{method_name}测试出错: {str(e)}", "ERROR")
            error_messages[method_name] = str(e)
    
    # 分析错误
    common_error_types = {}
    for method, error in error_messages.items():
        for error_key in COMMON_ERRORS.keys():
            if error_key in error:
                if error_key not in common_error_types:
                    common_error_types[error_key] = []
                common_error_types[error_key].append(method)
    
    # 总结结果
    log("\n===== 测试结果总结 =====")
    if success:
        log(f"找到 {len(successful_methods)} 个成功的连接方法:", "SUCCESS")
        for method in successful_methods:
            log(f"- {method}", "SUCCESS")
    else:
        log("所有测试方法均失败", "ERROR")
    
    if common_error_types:
        log("\n发现常见错误类型:", "WARNING")
        for error_key, methods in common_error_types.items():
            error_info = COMMON_ERRORS[error_key]
            log(f"错误: {error_key}", "WARNING")
            log(f"  说明: {error_info['description']}", "WARNING")
            log(f"  影响的方法: {', '.join(methods)}", "WARNING")
            log("  可能的解决方案:", "WARNING")
            for solution in error_info['solutions']:
                log(f"  - {solution}", "WARNING")
    
    return success, successful_methods, result_data

def generate_fix_code(proxy_str, successful_methods):
    """生成修复代码"""
    if not successful_methods:
        return "// 未找到可用的连接方法，无法生成修复代码"
    
    # 解析代理配置
    proxy_config = get_proxy_config_from_string(proxy_str)
    if not proxy_config:
        return "// 无效的代理配置，无法生成修复代码"
    
    # 选择最佳方法
    best_method = None
    method_priority = ["自定义处理器", "基本SOCKS5", "Session连接", "SOCKS5h协议", "Requests SOCKS5", "HTTP代理回退"]
    for method in method_priority:
        if method in successful_methods:
            best_method = method
            break
    
    if not best_method:
        best_method = successful_methods[0]
    
    log(f"选择的最佳连接方法: {best_method}")
    
    # 生成相应的代码
    code = f"""
# {best_method} - 代理连接修复代码
# 由fix_socks5_proxy.py自动生成

"""
    
    if best_method == "基本SOCKS5":
        code += f"""
import socks
import socket
import urllib.request
import json

# 保存原始socket
orig_socket = socket.socket

def use_socks5_proxy():
    \"\"\"启用SOCKS5代理\"\"\"
    # 设置SOCKS5代理
    socks.set_default_proxy(
        proxy_type=socks.SOCKS5,
        addr="{proxy_config['host']}",
        port={proxy_config['port']}"""
        
        if proxy_config.get('username'):
            code += f""",
        username="{proxy_config['username']}",
        password="{proxy_config['password']}"
"""
        else:
            code += "\n"
            
        code += """)
    # 替换socket实现
    socket.socket = socks.socksocket
    
def reset_proxy():
    \"\"\"重置代理设置\"\"\"
    socket.socket = orig_socket
    
def make_request(url, params=None, headers=None):
    \"\"\"使用代理发送请求\"\"\"
    try:
        use_socks5_proxy()
        
        # 创建请求
        req = urllib.request.Request(url)
        
        # 添加请求头
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # 发送请求
        response = urllib.request.urlopen(req, timeout=30)
        data = response.read().decode('utf-8')
        
        # 解析JSON
        return json.loads(data)
    finally:
        reset_proxy()
"""
    
    elif best_method in ["Requests SOCKS5", "SOCKS5h协议", "Session连接"]:
        # 确定协议
        protocol = "socks5h" if best_method == "SOCKS5h协议" else "socks5"
        
        # 构建代理URL
        if proxy_config.get('username'):
            username = urllib.parse.quote(proxy_config['username'])
            password = urllib.parse.quote(proxy_config['password'])
            proxy_url = f"{protocol}://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
        else:
            proxy_url = f"{protocol}://{proxy_config['host']}:{proxy_config['port']}"
        
        code += f"""
import requests

def make_request(url, params=None, headers=None):
    \"\"\"使用SOCKS5代理发送请求\"\"\"
    # 设置代理
    proxies = {{
        'http': "{proxy_url}",
        'https': "{proxy_url}"
    }}
    
    # 设置请求头
    request_headers = {{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }}
    
    # 添加自定义请求头
    if headers:
        request_headers.update(headers)
    
    # 创建会话
    session = requests.Session()
    session.proxies = proxies
    session.headers.update(request_headers)
    
    # 发送请求
    response = session.get(url, params=params, timeout=30)
    
    # 检查状态码
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败，状态码: {{response.status_code}}")
"""
    
    elif best_method == "自定义处理器":
        code += f"""
import socks
import socket
import urllib.request
import ssl
import json

def create_socks5_handler():
    \"\"\"创建SOCKS5处理器\"\"\"
    # SocksiPy处理器定义
    class SocksiPyConnection(urllib.request.HTTPConnection):
        def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True, username=None, password=None, *args, **kwargs):
            self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
            urllib.request.HTTPConnection.__init__(self, *args, **kwargs)

        def connect(self):
            self.sock = socks.socksocket()
            self.sock.setproxy(*self.proxyargs)
            if type(self.timeout) in (int, float):
                self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))

    class SocksiPyConnectionS(urllib.request.HTTPSConnection):
        def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=True, username=None, password=None, *args, **kwargs):
            self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
            urllib.request.HTTPSConnection.__init__(self, *args, **kwargs)

        def connect(self):
            sock = socks.socksocket()
            sock.setproxy(*self.proxyargs)
            if type(self.timeout) in (int, float):
                sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            try:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)
            except AttributeError:
                context = ssl.create_default_context()
                self.sock = context.wrap_socket(sock, server_hostname=self.host)

    class SocksiPyHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kw = kwargs
            urllib.request.HTTPHandler.__init__(self)
            urllib.request.HTTPSHandler.__init__(self)

        def http_open(self, req):
            def build(host, port=None, timeout=0, **kwargs):
                kw = merge_dict(self.kw, kwargs)
                conn = SocksiPyConnection(*self.args, host=host, port=port, timeout=timeout, **kw)
                return conn
            return self.do_open(build, req)

        def https_open(self, req):
            def build(host, port=None, timeout=0, **kwargs):
                kw = merge_dict(self.kw, kwargs)
                conn = SocksiPyConnectionS(*self.args, host=host, port=port, timeout=timeout, **kw)
                return conn
            return self.do_open(build, req)

    def merge_dict(a, b):
        d = a.copy()
        d.update(b)
        return d
    
    # 创建处理器
    return SocksiPyHandler(
        socks.SOCKS5, 
        "{proxy_config['host']}", 
        {proxy_config['port']}, """
        
        if proxy_config.get('username'):
            code += f"""
        username="{proxy_config['username']}", 
        password="{proxy_config['password']}"
    )
"""
        else:
            code += """
    )
"""
            
        code += """
def make_request(url, params=None, headers=None):
    \"\"\"使用SOCKS5代理发送请求\"\"\"
    # 创建opener
    opener = urllib.request.build_opener(create_socks5_handler())
    urllib.request.install_opener(opener)
    
    # 构建URL
    if params:
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        if '?' in url:
            url += '&' + query_string
        else:
            url += '?' + query_string
    
    # 创建请求
    req = urllib.request.Request(url)
    
    # 添加请求头
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    else:
        # 添加默认请求头
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 发送请求并解析响应
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read().decode('utf-8')
        return json.loads(data)
"""
    
    elif best_method == "HTTP代理回退":
        # 构建代理URL
        if proxy_config.get('username'):
            username = urllib.parse.quote(proxy_config['username'])
            password = urllib.parse.quote(proxy_config['password'])
            proxy_url = f"http://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
        else:
            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
        
        code += f"""
import requests

def make_request(url, params=None, headers=None):
    \"\"\"使用HTTP代理发送请求\"\"\"
    # 设置代理
    proxies = {{
        'http': "{proxy_url}",
        'https': "{proxy_url}"
    }}
    
    # 设置请求头
    request_headers = {{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }}
    
    # 添加自定义请求头
    if headers:
        request_headers.update(headers)
    
    # 发送请求
    response = requests.get(url, params=params, headers=request_headers, proxies=proxies, timeout=30)
    
    # 检查状态码
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败，状态码: {{response.status_code}}")
"""
    
    # 添加使用示例
    code += """
# 使用示例
if __name__ == "__main__":
    try:
        # 测试连接
        result = make_request("http://httpbin.org/ip")
        print(f"连接成功! 您的IP: {result.get('origin')}")
    except Exception as e:
        print(f"连接失败: {e}")
"""
    
    return code

def save_fix_code(code, filename="socks5_proxy_fix.py"):
    """保存修复代码到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        log(f"修复代码已保存到: {filename}", "SUCCESS")
        return True
    except Exception as e:
        log(f"保存修复代码失败: {e}", "ERROR")
        return False

def test_proxy(args):
    """测试代理"""
    proxy_str = args.proxy
    log(f"开始测试代理: {proxy_str}")
    
    # 执行测试
    success, methods, result = full_proxy_test(proxy_str)
    
    # 如果成功，生成修复代码
    if success and args.fix:
        log("\n正在生成修复代码...")
        code = generate_fix_code(proxy_str, methods)
        save_fix_code(code, args.output)
    
    return success

def test_proxy_file(args):
    """测试文件中的代理"""
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        log(f"读取代理文件失败: {e}", "ERROR")
        return False
    
    if not proxies:
        log("代理文件为空", "ERROR")
        return False
    
    log(f"文件中包含 {len(proxies)} 个代理")
    
    # 测试每个代理
    success_count = 0
    successful_proxies = []
    
    for i, proxy in enumerate(proxies):
        log(f"\n===== 测试代理 {i+1}/{len(proxies)} =====")
        log(f"代理: {proxy}")
        
        # 执行测试
        success, methods, result = full_proxy_test(proxy)
        
        if success:
            success_count += 1
            successful_proxies.append((proxy, methods))
        
        # 避免测试过于频繁
        if i < len(proxies) - 1:
            time.sleep(3)
    
    # 总结结果
    log(f"\n===== 测试结果总结 =====")
    log(f"共测试了 {len(proxies)} 个代理，其中 {success_count} 个成功")
    
    if successful_proxies and args.fix:
        # 选择第一个成功的代理生成修复代码
        best_proxy, methods = successful_proxies[0]
        log(f"\n使用代理 {best_proxy} 生成修复代码")
        code = generate_fix_code(best_proxy, methods)
        save_fix_code(code, args.output)
    
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='SOCKS5代理修复工具')
    parser.add_argument('--proxy', help='代理字符串，格式为host:port:username:password')
    parser.add_argument('--file', help='代理文件，每行一个代理')
    parser.add_argument('--fix', action='store_true', help='生成修复代码')
    parser.add_argument('--output', default='socks5_proxy_fix.py', help='修复代码输出文件')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    # 设置调试模式
    global DEBUG
    DEBUG = args.debug
    
    # 检查参数
    if not args.proxy and not args.file:
        parser.print_help()
        return
    
    # 根据参数测试代理
    if args.proxy:
        test_proxy(args)
    elif args.file:
        test_proxy_file(args)

if __name__ == "__main__":
    main() 