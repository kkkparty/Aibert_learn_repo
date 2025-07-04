#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
360s5代理修复和测试工具
尝试多种方法直到成功连接
"""

import os
import sys
import socks
import socket
import json
import time
import urllib.request
import urllib.parse
import requests
import ssl
from pathlib import Path
from datetime import datetime
import argparse
import random

def log(msg):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_method1(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法1: 直接使用SOCKS库测试代理 (原始格式)
    """
    log("方法1: 直接使用PySocks (原始格式)")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    log(f"测试代理: {proxy_host}:{proxy_port}")
    log(f"用户名: {proxy_username}")
    log(f"密码: {proxy_password}")
    
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
        log(f"尝试连接到: {test_url}")
        response = urllib.request.urlopen(test_url, timeout=15)
        data = response.read().decode('utf-8')
        log(f"响应: {data}")
        
        # 保存有效配置到文件
        save_working_config("method1", {
            "host": proxy_host,
            "port": proxy_port,
            "username": proxy_username,
            "password": proxy_password
        })
        return True
    except Exception as e:
        log(f"方法1失败: {e}")
        return False
    finally:
        # 恢复原始socket
        socket.socket = default_socket

def test_method2(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法2: 使用requests库测试代理 (socks5:// 格式)
    """
    log("方法2: 使用Requests库 (socks5:// 格式)")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    # 构建代理URL - 尝试不同的格式
    # 格式1: socks5://username:password@hostname:port
    proxy_url = f"socks5://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
    
    log(f"测试代理URL: {proxy_url}")
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        response = requests.get(test_url, proxies=proxies, timeout=15)
        log(f"响应状态码: {response.status_code}")
        log(f"响应内容: {response.text}")
        
        # 保存有效配置到文件
        save_working_config("method2", {
            "proxy_url": proxy_url
        })
        return True
    except Exception as e:
        log(f"方法2失败: {e}")
        return False

def test_method3(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法3: 使用URL编码后的用户名密码
    """
    log("方法3: 使用URL编码后的用户名密码")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    # URL编码用户名和密码
    encoded_username = urllib.parse.quote(proxy_username)
    encoded_password = urllib.parse.quote(proxy_password)
    
    proxy_url = f"socks5://{encoded_username}:{encoded_password}@{proxy_host}:{proxy_port}"
    log(f"URL编码后的代理: {proxy_url}")
    
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        response = requests.get(test_url, proxies=proxies, timeout=15)
        log(f"响应状态码: {response.status_code}")
        log(f"响应内容: {response.text}")
        
        # 保存有效配置到文件
        save_working_config("method3", {
            "proxy_url": proxy_url,
            "encoded_username": encoded_username,
            "encoded_password": encoded_password
        })
        return True
    except Exception as e:
        log(f"方法3失败: {e}")
        return False

def test_method4(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法4: 使用socks5h协议 (主机名由代理解析)
    """
    log("方法4: 使用socks5h协议")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    # URL编码用户名和密码
    encoded_username = urllib.parse.quote(proxy_username)
    encoded_password = urllib.parse.quote(proxy_password)
    
    # 使用socks5h而不是socks5
    proxy_url = f"socks5h://{encoded_username}:{encoded_password}@{proxy_host}:{proxy_port}"
    log(f"测试socks5h代理: {proxy_url}")
    
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        response = requests.get(test_url, proxies=proxies, timeout=15)
        log(f"响应状态码: {response.status_code}")
        log(f"响应内容: {response.text}")
        
        # 保存有效配置到文件
        save_working_config("method4", {
            "proxy_url": proxy_url
        })
        return True
    except Exception as e:
        log(f"方法4失败: {e}")
        return False

def test_method5(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法5: 使用用户提供的代码示例
    """
    log("方法5: 使用用户提供的代码示例")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    log(f"使用原始代码示例结构")
    
    try:
        # SocksiPy定义
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
                    # 在Python3.3及以上版本使用SSLContext
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
        
        # 设置请求和代理
        req = urllib.request.Request(
            url=test_url, 
            headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        
        opener = urllib.request.build_opener(
            SocksiPyHandler(
                socks.SOCKS5, 
                proxy_host, 
                proxy_port, 
                username=proxy_username, 
                password=proxy_password
            )
        )
        
        log(f"尝试连接到: {test_url}")
        response = opener.open(req, timeout=15)
        data = response.read().decode('utf-8')
        log(f"响应: {data}")
        
        # 保存有效配置到文件
        save_working_config("method5", {
            "host": proxy_host,
            "port": proxy_port,
            "username": proxy_username,
            "password": proxy_password
        })
        return True
    except Exception as e:
        log(f"方法5失败: {e}")
        return False

def test_method6(proxy_str, test_url='https://api.ipify.org?format=json'):
    """
    方法6: 尝试使用requests + SOCKS5代理 + session
    """
    log("方法6: 使用Requests session")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    # URL编码用户名和密码
    encoded_username = urllib.parse.quote(proxy_username)
    encoded_password = urllib.parse.quote(proxy_password)
    
    proxy_url = f"socks5://{encoded_username}:{encoded_password}@{proxy_host}:{proxy_port}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        # 创建session
        session = requests.Session()
        session.proxies = proxies
        
        # 添加多个请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        log(f"使用session连接到: {test_url}")
        response = session.get(test_url, headers=headers, timeout=15)
        log(f"响应状态码: {response.status_code}")
        log(f"响应内容: {response.text}")
        
        # 保存有效配置
        save_working_config("method6", {
            "proxy_url": proxy_url,
            "proxy_type": "socks5",
            "proxy_host": proxy_host,
            "proxy_port": proxy_port,
            "proxy_username": proxy_username,
            "proxy_password": proxy_password,
        })
        return True
    except Exception as e:
        log(f"方法6失败: {e}")
        return False

def test_method7(proxy_str, test_url='http://httpbin.org/ip'):
    """
    方法7: 尝试使用不同的测试URL (http而非https)
    """
    log("方法7: 使用不同的测试URL (http)")
    parts = proxy_str.split(':')
    if len(parts) < 4:
        log(f"无效的代理格式: {proxy_str}")
        return False
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        log(f"无效的端口: {parts[1]}")
        return False
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
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
        log(f"尝试连接到HTTP URL: {test_url}")
        response = urllib.request.urlopen(test_url, timeout=15)
        data = response.read().decode('utf-8')
        log(f"响应: {data}")
        
        # 保存有效配置到文件
        save_working_config("method7", {
            "host": proxy_host,
            "port": proxy_port,
            "username": proxy_username,
            "password": proxy_password,
            "test_url": test_url
        })
        return True
    except Exception as e:
        log(f"方法7失败: {e}")
        return False
    finally:
        # 恢复原始socket
        socket.socket = default_socket

def save_working_config(method, config):
    """保存有效的配置到文件"""
    try:
        config_file = "working_proxy_config.json"
        
        # 如果文件存在，先读取已有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)
        else:
            all_configs = {}
        
        # 添加新配置
        all_configs[method] = {
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(all_configs, f, indent=2)
            
        log(f"已保存成功的配置 (方法{method}) 到 {config_file}")
    except Exception as e:
        log(f"保存配置失败: {e}")

def fix_proxy_manager():
    """为bn_pro/proxy_manager.py创建补丁文件"""
    log("创建代理管理器补丁文件...")
    
    # 检查是否有有效的配置
    if not os.path.exists("working_proxy_config.json"):
        log("没有找到有效的配置，请先运行测试找到可用的方法")
        return False
    
    try:
        with open("working_proxy_config.json", 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        # 选择第一个可用的配置
        if not configs:
            log("配置文件为空")
            return False
        
        method, config_data = list(configs.items())[0]
        config = config_data["config"]
        
        log(f"使用方法{method}的配置创建补丁")
        
        patch_content = """
# 360s5代理补丁
# 此文件由fix_360s5_proxy.py创建

import socks
import socket
import urllib.request
import ssl
import urllib.parse

def parse_360s5_proxy(proxy_str):
    \"\"\"解析360s5格式的代理\"\"\"
    parts = proxy_str.split(':')
    if len(parts) < 4:
        return None
        
    proxy_host = parts[0]
    try:
        proxy_port = int(parts[1])
    except:
        return None
    
    # 用户名可能包含冒号，密码是最后一部分
    proxy_password = parts[-1]
    proxy_username = ':'.join(parts[2:-1])
    
    return {
        "host": proxy_host,
        "port": proxy_port,
        "username": proxy_username,
        "password": proxy_password
    }

def create_360s5_socks_handler(proxy_config):
    \"\"\"创建360s5 SOCKS5代理处理器\"\"\"
    # 定义SocksiPy处理器类
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
        proxy_config["host"], 
        proxy_config["port"], 
        username=proxy_config["username"], 
        password=proxy_config["password"]
    )

def use_global_socks5_proxy(proxy_config):
    \"\"\"设置全局SOCKS5代理\"\"\"
    socks.set_default_proxy(
        proxy_type=socks.SOCKS5,
        addr=proxy_config["host"],
        port=proxy_config["port"],
        username=proxy_config["username"],
        password=proxy_config["password"]
    )
    # 替换全局socket
    socket.socket = socks.socksocket
    
def reset_global_proxy():
    \"\"\"重置全局代理\"\"\"
    socket.socket = socket._orig_socket
"""
        
        # 写入补丁文件
        patch_file = "bn_pro/proxy_360s5_patch.py"
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write(patch_content)
            
        log(f"补丁文件已创建: {patch_file}")
        
        # 创建修改版的bn2.py中的请求代码
        create_fixed_request_code(method, config)
        
        return True
    except Exception as e:
        log(f"创建补丁文件失败: {e}")
        return False

def create_fixed_request_code(method, config):
    """根据成功的方法创建修复的请求代码"""
    log("创建修复的请求代码示例...")
    
    code_template = ""
    
    if method == "method1" or method == "method5" or method == "method7":
        # 使用全局代理设置
        code_template = """
# 在bn_pro/bn2.py的_make_api_request方法中替换请求代码
# 使用全局SOCKS5代理方法

from proxy_360s5_patch import use_global_socks5_proxy, reset_global_proxy

try:
    # 设置全局代理
    use_global_socks5_proxy({
        "host": "%(host)s", 
        "port": %(port)d,
        "username": "%(username)s",
        "password": "%(password)s"
    })
    
    # 使用普通请求 (不需要proxies参数)
    response = requests.get(
        url, 
        params=params, 
        headers=headers, 
        timeout=60  # 更长的超时时间
    )
    
    # 更新最后请求时间
    self.last_request_time = time.time()
    
    # 重置全局代理
    reset_global_proxy()
    
    if response.status_code == 200:
        # 成功，保存缓存并返回
        data = response.json()
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
        return data
        
except Exception as e:
    logger.error(f"请求出错: {e}")
    reset_global_proxy()  # 确保重置全局代理
    return None
""" % {
            "host": config["host"],
            "port": config["port"],
            "username": config["username"],
            "password": config["password"]
        }
    elif method in ["method2", "method3", "method4", "method6"]:
        # 使用代理URL
        code_template = """
# 在bn_pro/bn2.py的_make_api_request方法中替换请求代码
# 使用代理URL方法

try:
    # 使用固定的代理URL
    proxies = {
        'http': "%(proxy_url)s",
        'https': "%(proxy_url)s"
    }
    
    # 创建session
    session = requests.Session()
    session.proxies = proxies
    session.headers.update(headers)
    
    # 发送请求
    response = session.get(url, params=params, timeout=60)
    
    # 更新最后请求时间
    self.last_request_time = time.time()
    
    if response.status_code == 200:
        # 成功，保存缓存并返回
        data = response.json()
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
        return data
        
except Exception as e:
    logger.error(f"请求出错: {e}")
    return None
""" % {"proxy_url": config["proxy_url"]}
    
    # 写入修复代码文件
    fix_code_file = "bn_pro/fixed_request_code.py"
    with open(fix_code_file, 'w', encoding='utf-8') as f:
        f.write(code_template)
        
    log(f"修复的请求代码已保存到: {fix_code_file}")

def main():
    parser = argparse.ArgumentParser(description='修复和测试360s5 SOCKS5代理')
    parser.add_argument('--proxy', help='代理字符串 (格式: hostname:port:username:password)')
    parser.add_argument('--file', help='代理文件路径')
    parser.add_argument('--url', default='https://api.ipify.org?format=json', help='测试URL')
    parser.add_argument('--method', type=int, help='仅测试特定方法 (1-7)')
    parser.add_argument('--patch', action='store_true', help='根据成功的方法创建补丁文件')
    
    args = parser.parse_args()
    
    # 如果只是创建补丁
    if args.patch:
        fix_proxy_manager()
        return
    
    # 确定代理字符串
    proxy_str = ''
    if args.proxy:
        proxy_str = args.proxy
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
                if proxies:
                    # 随机选择一个代理
                    proxy_str = random.choice(proxies)
                    log(f"从文件随机选择代理: {proxy_str}")
                else:
                    log("代理文件为空")
                    sys.exit(1)
        except Exception as e:
            log(f"读取代理文件失败: {e}")
            sys.exit(1)
    else:
        log("必须提供--proxy或--file参数")
        sys.exit(1)
    
    # 测试URL
    test_url = args.url
    log(f"使用测试URL: {test_url}")
    
    # 如果指定了特定方法
    if args.method:
        method_funcs = {
            1: test_method1,
            2: test_method2,
            3: test_method3,
            4: test_method4,
            5: test_method5,
            6: test_method6,
            7: test_method7
        }
        
        if args.method not in method_funcs:
            log(f"无效的方法: {args.method}，必须是1-7")
            sys.exit(1)
            
        log(f"仅测试方法{args.method}")
        success = method_funcs[args.method](proxy_str, test_url)
        log(f"方法{args.method}测试结果: {'成功' if success else '失败'}")
        return
    
    # 测试所有方法
    log("开始测试360s5代理，将尝试多种方法直到成功...")
    log(f"测试代理: {proxy_str}")
    
    methods = [
        (1, test_method1),
        (2, test_method2),
        (3, test_method3),
        (4, test_method4),
        (5, test_method5),
        (6, test_method6),
        (7, test_method7)
    ]
    
    success = False
    successful_methods = []
    
    for method_num, method_func in methods:
        log(f"\n============ 尝试方法 {method_num} ============")
        try:
            if method_func(proxy_str, test_url):
                log(f"方法 {method_num} 成功！")
                success = True
                successful_methods.append(method_num)
                if method_num < 7:  # 仍继续测试其他方法
                    time.sleep(2)  # 暂停一下，避免速率限制
        except Exception as e:
            log(f"测试方法 {method_num} 时出错: {e}")
        
    # 总结
    log("\n====== 测试结果汇总 ======")
    if success:
        log(f"找到 {len(successful_methods)} 个成功的方法: {successful_methods}")
        log("您现在可以运行以下命令创建补丁文件:")
        log("  python bn_pro/fix_360s5_proxy.py --patch")
    else:
        log("所有方法都失败，请检查代理是否有效或更新代理")

if __name__ == "__main__":
    log("360s5代理修复工具启动")
    if len(sys.argv) > 1:
        main()
    else:
        log("用法: python fix_360s5_proxy.py --proxy hostname:port:username:password")
        log("或: python fix_360s5_proxy.py --file proxy_file.txt")
        log("或: python fix_360s5_proxy.py --method 1-7 --proxy hostname:port:username:password")
        log("或: python fix_360s5_proxy.py --patch (创建补丁文件)")