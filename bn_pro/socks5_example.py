#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SOCKS5代理使用示例
这个脚本展示了如何使用SOCKS5代理发送HTTP请求
"""

import requests
import socks
import socket
import urllib.request
from urllib.error import URLError
import sys

# 代理配置信息
proxy_config = {
    # 根据您的实际代理信息修改这些值
    'host': 'ip.proxys5.net',  # 或您的代理服务器地址
    'port': 6500,              # 或您的代理服务器端口
    'username': '',            # 如果需要身份验证，填写用户名
    'password': ''             # 如果需要身份验证，填写密码
}

def test_direct_connection():
    """测试直接连接（不使用代理）"""
    print("测试直接连接...")
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        print(f"请求成功: {response.text}")
        return True
    except Exception as e:
        print(f"直接连接失败: {e}")
        return False

def test_requests_with_socks5():
    """使用requests库配合SOCKS5代理"""
    print("\n方法1: 使用requests库 + SOCKS5代理...")
    
    # 构建代理URL
    proxy_url = f"socks5://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=10)
        print(f"请求成功: {response.text}")
        return True
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_socks_global_proxy():
    """使用全局SOCKS代理（适用于不支持代理参数的库）"""
    print("\n方法2: 使用全局SOCKS代理...")
    
    # 保存原始socket
    original_socket = socket.socket
    
    try:
        # 设置全局代理
        socks.set_default_proxy(
            socks.SOCKS5, 
            proxy_config['host'], 
            proxy_config['port'], 
            username=proxy_config['username'] if proxy_config['username'] else None, 
            password=proxy_config['password'] if proxy_config['password'] else None
        )
        socket.socket = socks.socksocket
        
        # 使用普通的urllib请求
        response = urllib.request.urlopen('https://api.ipify.org?format=json', timeout=10)
        content = response.read().decode('utf-8')
        print(f"请求成功: {content}")
        return True
    except Exception as e:
        print(f"请求失败: {e}")
        return False
    finally:
        # 恢复原始socket
        socket.socket = original_socket

def test_socksipy_handler():
    """使用SocksiPyHandler (与您提供的代码类似)"""
    print("\n方法3: 使用SocksiPyHandler...")
    
    # 导入您的SocksiPyHandler类
    try:
        from urllib.error import URLError
        import urllib.request
        import ssl
        
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
                    # 在较新版本的Python中，这部分代码可能需要修改
                    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)
                except AttributeError:
                    # 在Python3.3及以上版本可能需要使用SSLContext
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

        # 使用SocksiPyHandler
        opener = urllib.request.build_opener(
            SocksiPyHandler(
                socks.SOCKS5,
                proxy_config['host'],
                proxy_config['port'],
                username=proxy_config['username'] if proxy_config['username'] else None,
                password=proxy_config['password'] if proxy_config['password'] else None
            )
        )
        
        # 设置User-Agent
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        ]
        
        response = opener.open('https://api.ipify.org?format=json', timeout=10)
        content = response.read().decode('utf-8')
        print(f"请求成功: {content}")
        return True
    except Exception as e:
        print(f"请求失败: {e}")
        print(f"详细错误: {sys.exc_info()}")
        return False

def main():
    print("===== SOCKS5代理测试程序 =====")
    print(f"使用代理: {proxy_config['host']}:{proxy_config['port']}")
    
    # 测试直接连接
    test_direct_connection()
    
    # 测试三种不同的代理方法
    print("\n===== 测试不同的代理方法 =====")
    results = {
        "requests+SOCKS5": test_requests_with_socks5(),
        "全局代理":      test_socks_global_proxy(),
        "SocksiPyHandler": test_socksipy_handler()
    }
    
    print("\n===== 测试结果汇总 =====")
    for method, success in results.items():
        print(f"{method}: {'✓ 成功' if success else '✗ 失败'}")
    
    print("\n===== 如何在bn.py中使用代理 =====")
    print("1. 使用命令行添加代理: python bn_pro/bn2.py --add-socks5-proxy ip.proxys5.net:6500 --socks5-username YOUR_USERNAME --socks5-password YOUR_PASSWORD")
    print("2. 运行分析工具并使用代理: python bn_pro/bn2.py --use-proxies --coins 500")
    
if __name__ == "__main__":
    main() 