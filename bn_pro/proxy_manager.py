#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import random
import time
import logging
import requests
import socks
import socket
from datetime import datetime, timedelta
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# 创建一个全局的代理管理器实例
_proxy_manager = None

def get_proxy():
    """获取一个有效的代理地址"""
    global _proxy_manager
    
    # 如果代理管理器未初始化，则创建一个
    if _proxy_manager is None:
        # 检查是否有代理文件
        proxy_files = ['proxies.txt', '360s5_proxies.txt']
        proxy_list = []
        
        for file_name in proxy_files:
            if os.path.exists(file_name):
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        lines = [line.strip() for line in lines if line.strip()]
                        logger.info(f"从文件 {file_name} 读取了 {len(lines)} 个代理")
                        proxy_list.extend(lines)
                except Exception as e:
                    logger.error(f"读取代理文件 {file_name} 失败: {e}")
        
        if proxy_list:
            _proxy_manager = ProxyManager()
            _proxy_manager.add_proxies_from_list(proxy_list)
            logger.info(f"已加载 {len(proxy_list)} 个代理")
        else:
            logger.warning("未找到可用的代理文件或代理文件为空")
            return None
    
    # 获取一个代理
    if _proxy_manager and _proxy_manager.proxies:
        logger.info(f"代理管理器中有 {len(_proxy_manager.proxies)} 个代理")
        
        # 直接从原始代理列表中随机选择一个
        if proxy_list:
            proxy_str = random.choice(proxy_list)
            logger.info(f"选择的代理: {proxy_str}")
            return proxy_str
        
        return None
    else:
        logger.warning("代理管理器中没有可用的代理")
        return None

class ProxyManager:
    """代理IP池管理类"""
    
    def __init__(self, proxy_file='proxy_list.json', test_url='https://api.coingecko.com/api/v3/ping'):
        """
        初始化代理管理器
        
        参数:
        proxy_file -- 存储代理列表的文件
        test_url -- 用于测试代理有效性的URL
        """
        self.proxy_file = proxy_file
        self.test_url = test_url
        self.proxies = []
        self.current_index = 0
        self.last_proxy_update = None
        self.update_interval = timedelta(hours=2)  # 每2小时重新验证代理
        
        # 加载代理列表
        self.load_proxies()
    
    def load_proxies(self):
        """从文件加载代理列表"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'proxies' in data and 'last_updated' in data:
                        self.proxies = data['proxies']
                        self.last_proxy_update = datetime.fromisoformat(data['last_updated'])
                        logger.info(f"已加载 {len(self.proxies)} 个代理")
                    else:
                        logger.warning("代理文件格式不正确")
                        self.proxies = []
            else:
                logger.info("代理文件不存在，将使用空代理列表")
                self.proxies = []
        except Exception as e:
            logger.error(f"加载代理文件出错: {e}")
            self.proxies = []
    
    def save_proxies(self):
        """保存代理列表到文件"""
        try:
            data = {
                'proxies': self.proxies,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(self.proxies)} 个代理到文件")
        except Exception as e:
            logger.error(f"保存代理文件出错: {e}")
    
    def parse_socks5_proxy(self, proxy_str):
        """
        解析SOCKS5代理字符串，返回代理参数
        
        参数:
        proxy_str - 格式为 socks5://username:password@host:port 的代理字符串
        
        返回:
        dict - 包含代理配置的字典
        """
        try:
            parsed = urlparse(proxy_str)
            proxy_type = parsed.scheme  # socks5
            auth_info = parsed.netloc.split('@')
            
            if len(auth_info) > 1:
                # 有用户名和密码
                username_password = auth_info[0].split(':')
                host_port = auth_info[1].split(':')
                
                username = username_password[0] if len(username_password) > 0 else ""
                password = username_password[1] if len(username_password) > 1 else ""
                
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 1080
            else:
                # 无用户名和密码
                host_port = auth_info[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 1080
                username = password = None
            
            if proxy_type == 'socks5':
                return {
                    'type': 'socks5',
                    'host': host,
                    'port': port,
                    'username': username,
                    'password': password,
                    'raw': proxy_str  # 保存原始字符串
                }
            else:
                return None
        except Exception as e:
            logger.error(f"解析SOCKS5代理出错: {e}, proxy_str: {proxy_str}")
            return None
    
    def setup_socks5_proxy(self, proxy_config):
        """
        设置全局SOCKS5代理
        
        参数:
        proxy_config - 包含代理配置的字典
        """
        try:
            socks.set_default_proxy(
                socks.SOCKS5, 
                proxy_config['host'], 
                proxy_config['port'], 
                username=proxy_config['username'], 
                password=proxy_config['password']
            )
            socket.socket = socks.socksocket
            logger.info(f"已设置全局SOCKS5代理: {proxy_config['host']}:{proxy_config['port']}")
            return True
        except Exception as e:
            logger.error(f"设置SOCKS5代理失败: {e}")
            return False
    
    def reset_socks_proxy(self):
        """重置SOCKS代理，恢复默认socket"""
        socket.socket = socket._orig_socket
        logger.info("已重置全局SOCKS代理")
    
    def format_proxy_for_requests(self, proxy):
        """
        将代理信息格式化为requests库可用的格式
        
        参数:
        proxy - 代理配置（字符串或字典）
        
        返回:
        dict - requests库可用的代理配置
        """
        if isinstance(proxy, str):
            # 检查是否是SOCKS5代理
            if proxy.startswith('socks5://'):
                config = self.parse_socks5_proxy(proxy)
                if config:
                    proxy_url = f"socks5://{config['username']}:{config['password']}@{config['host']}:{config['port']}"
                    return {"http": proxy_url, "https": proxy_url}
                else:
                    return None
            else:
                # HTTP/HTTPS代理
                return {"http": proxy, "https": proxy}
        elif isinstance(proxy, dict):
            # 如果已经是字典格式，检查是否有type字段指示是SOCKS5
            if proxy.get('type') == 'socks5':
                proxy_url = f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
                return {"http": proxy_url, "https": proxy_url}
            elif 'http' in proxy or 'https' in proxy:
                # 如果已经是requests格式，直接返回
                return proxy
            elif 'raw' in proxy:
                # 如果有raw字段，使用raw字段的值
                return {"http": proxy['raw'], "https": proxy['raw']}
        
        logger.warning(f"无法识别的代理格式: {proxy}")
        return None
    
    def add_proxy(self, proxy, skip_test=False):
        """
        添加新代理到列表
        
        参数:
        proxy -- 代理地址，格式为 "http://ip:port" 或 "socks5://username:password@ip:port"
                或 {"http": "http://ip:port", "https": "http://ip:port"}
                或 {"type": "socks5", "host": "ip", "port": port, "username": "user", "password": "pass"}
        skip_test -- 是否跳过代理测试
        """
        # 处理SOCKS5代理特殊情况
        if isinstance(proxy, str) and proxy.startswith('socks5://'):
            config = self.parse_socks5_proxy(proxy)
            if not config:
                logger.warning(f"无效的SOCKS5代理格式: {proxy}")
                return False
            
            # 检查是否已存在
            for existing_proxy in self.proxies:
                if isinstance(existing_proxy, dict) and existing_proxy.get('type') == 'socks5':
                    if (existing_proxy.get('host') == config['host'] and 
                        existing_proxy.get('port') == config['port']):
                        logger.info(f"代理已存在: {proxy}")
                        return False
            
            # 测试SOCKS5代理
            if not skip_test:
            formatted_proxy = self.format_proxy_for_requests(config)
            if formatted_proxy and self.test_proxy(formatted_proxy):
                self.proxies.append(config)
                logger.info(f"添加SOCKS5代理成功: {proxy}")
                self.save_proxies()
                return True
            return False
            else:
                # 跳过测试，直接添加
                self.proxies.append(config)
                logger.info(f"添加SOCKS5代理成功(跳过测试): {proxy}")
                self.save_proxies()
                return True
        
        # 处理HTTP/HTTPS代理
        formatted_proxy = self.format_proxy_for_requests(proxy) if isinstance(proxy, str) else proxy
        
        if skip_test:
            self.proxies.append(formatted_proxy)
            logger.info(f"添加代理成功(跳过测试): {formatted_proxy}")
            self.save_proxies()
            return True
        elif formatted_proxy not in self.proxies and self.test_proxy(formatted_proxy):
            self.proxies.append(formatted_proxy)
            logger.info(f"添加代理成功: {formatted_proxy}")
            self.save_proxies()
            return True
        return False
    
    def remove_proxy(self, proxy):
        """从列表中移除代理"""
        # 处理不同格式的代理
        formatted_proxy = self.format_proxy_for_requests(proxy) if isinstance(proxy, str) else proxy
        
        for i, p in enumerate(self.proxies):
            # 对比代理对象的各个属性
            if isinstance(p, dict) and isinstance(formatted_proxy, dict):
                if p.get('type') == 'socks5' and formatted_proxy.get('type') == 'socks5':
                    if (p.get('host') == formatted_proxy.get('host') and 
                        p.get('port') == formatted_proxy.get('port')):
                        self.proxies.pop(i)
                        logger.info(f"已移除SOCKS5代理: {p}")
                        self.save_proxies()
                        return True
                elif p == formatted_proxy:
                    self.proxies.pop(i)
                    logger.info(f"已移除代理: {p}")
                    self.save_proxies()
                    return True
            elif p == formatted_proxy:
                self.proxies.pop(i)
                logger.info(f"已移除代理: {p}")
                self.save_proxies()
                return True
        
        return False
    
    def get_proxy(self, rotate=True):
        """
        获取一个代理
        
        参数:
        rotate -- 是否轮换到下一个代理
        
        返回:
        代理字典或None（如果没有可用代理）
        """
        if not self.proxies:
            return None
            
        # 检查是否需要更新代理有效性
        self.check_proxy_update()
            
        # 获取当前代理
        if rotate:
            self.current_index = (self.current_index + 1) % len(self.proxies)
        
        proxy = self.proxies[self.current_index] if self.proxies else None
        
        # 将代理转换为requests可用格式
        if proxy:
            return self.format_proxy_for_requests(proxy)
        return None
    
    def get_random_proxy(self):
        """随机获取一个代理"""
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        return self.format_proxy_for_requests(proxy)
    
    def test_proxy(self, proxy, timeout=10):
        """
        测试代理是否有效
        
        参数:
        proxy -- 要测试的代理
        timeout -- 请求超时时间（秒）
        
        返回:
        布尔值，表示代理是否有效
        """
        if not proxy:
            return False
            
        try:
            # 将代理格式转换为requests可用的格式
            formatted_proxy = self.format_proxy_for_requests(proxy)
            if not formatted_proxy:
                return False
                
            response = requests.get(
                self.test_url,
                proxies=formatted_proxy,
                timeout=timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"代理测试失败: {proxy} - {e}")
            return False
    
    def validate_all_proxies(self):
        """验证所有代理的有效性，移除无效代理"""
        if not self.proxies:
            logger.info("没有代理需要验证")
            return
            
        logger.info(f"开始验证 {len(self.proxies)} 个代理的有效性")
        valid_proxies = []
        
        for proxy in self.proxies:
            formatted_proxy = self.format_proxy_for_requests(proxy)
            if formatted_proxy and self.test_proxy(formatted_proxy):
                valid_proxies.append(proxy)
            else:
                logger.info(f"移除无效代理: {proxy}")
            
            # 避免请求过快
            time.sleep(1)
        
        self.proxies = valid_proxies
        self.last_proxy_update = datetime.now()
        self.save_proxies()
        logger.info(f"代理验证完成，有效代理: {len(valid_proxies)}/{len(self.proxies)}")
    
    def check_proxy_update(self):
        """检查是否需要更新代理有效性"""
        if (not self.last_proxy_update or 
                datetime.now() - self.last_proxy_update > self.update_interval):
            logger.info("代理列表需要更新验证")
            self.validate_all_proxies()
    
    def add_proxies_from_list(self, proxy_list, skip_test=True):
        """从列表批量添加多个代理"""
        added_count = 0
        for proxy in proxy_list:
            if self.add_proxy(proxy, skip_test=skip_test):
                added_count += 1
        logger.info(f"批量添加代理完成，成功添加 {added_count}/{len(proxy_list)} 个")
        return added_count
    
    def add_proxies_from_url(self, url):
        """从URL获取并添加代理列表"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # 假设返回格式为每行一个代理
                proxy_list = response.text.strip().split('\n')
                return self.add_proxies_from_list(proxy_list)
            else:
                logger.error(f"获取代理列表失败，状态码: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"从URL获取代理列表出错: {e}")
            return 0
    
    def get_stats(self):
        """获取代理统计信息"""
        return {
            "total_proxies": len(self.proxies),
            "current_index": self.current_index,
            "last_updated": self.last_proxy_update.isoformat() if self.last_proxy_update else None
        }


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 初始化代理管理器
    proxy_manager = ProxyManager()
    
    # 测试添加不同类型代理
    test_proxies = [
        {"http": "http://example.com:8080", "https": "http://example.com:8080"},
        "http://example2.com:8080",
        "socks5://username:password@socks5-server:1080"
    ]
    
    # 测试添加代理
    for proxy in test_proxies:
        proxy_manager.add_proxy(proxy)
    
    # 测试获取代理
    print("获取代理:", proxy_manager.get_proxy())
    print("随机代理:", proxy_manager.get_random_proxy())
    
    # 测试代理统计
    print("代理统计:", proxy_manager.get_stats()) 