#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
代理配置管理模块
提供代理服务器配置、测试和管理功能
"""

import os
import json
import time
import random
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# 配置日志
logger = logging.getLogger(__name__)

class ProxyManager:
    """代理管理器，用于管理和测试代理"""
    
    def __init__(self, proxy_file: str = "proxies.txt", test_url: str = "https://api.binance.com/api/v3/ping"):
        """
        初始化代理管理器
        
        Args:
            proxy_file: 代理列表文件路径
            test_url: 用于测试代理的URL
        """
        self.proxy_file = proxy_file
        self.test_url = test_url
        self.working_proxies = []
        self.timeout = 10  # 默认超时时间（秒）
        
        # 确保代理文件存在
        if not os.path.exists(proxy_file):
            with open(proxy_file, "w", encoding="utf-8") as f:
                f.write("# 在此文件中添加代理，每行一个，格式：http://host:port 或 socks5://host:port\n")
            logger.info(f"创建了空的代理文件: {proxy_file}")
    
    def load_proxies(self) -> List[str]:
        """
        从文件加载代理列表
        
        Returns:
            List[str]: 代理列表
        """
        try:
            with open(self.proxy_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 过滤掉注释和空行
            proxies = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
            
            logger.info(f"从 {self.proxy_file} 加载了 {len(proxies)} 个代理")
            return proxies
        except Exception as e:
            logger.error(f"加载代理列表失败: {e}")
            return []
    
    def save_proxies(self, proxies: List[str]) -> bool:
        """
        保存代理列表到文件
        
        Args:
            proxies: 代理列表
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.proxy_file, "w", encoding="utf-8") as f:
                f.write("# 代理列表，每行一个，格式：http://host:port 或 socks5://host:port\n")
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            logger.info(f"保存了 {len(proxies)} 个代理到 {self.proxy_file}")
            return True
        except Exception as e:
            logger.error(f"保存代理列表失败: {e}")
            return False
    
    def test_proxy(self, proxy: str, timeout: int = None) -> Tuple[bool, float]:
        """
        测试单个代理是否可用
        
        Args:
            proxy: 代理地址，格式：http://host:port 或 socks5://host:port
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[bool, float]: (是否可用, 响应时间)
        """
        if timeout is None:
            timeout = self.timeout
            
        proxies = {
            "http": proxy,
            "https": proxy
        }
        
        try:
            start_time = time.time()
            response = requests.get(self.test_url, proxies=proxies, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"代理 {proxy} 可用，响应时间: {elapsed:.2f}秒")
                return True, elapsed
            else:
                logger.warning(f"代理 {proxy} 返回状态码: {response.status_code}")
                return False, elapsed
        except Exception as e:
            logger.warning(f"代理 {proxy} 测试失败: {e}")
            return False, 0
    
    def test_all_proxies(self, timeout: int = None) -> List[Dict]:
        """
        测试所有代理是否可用
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            List[Dict]: 测试结果列表
        """
        if timeout is None:
            timeout = self.timeout
            
        proxies = self.load_proxies()
        if not proxies:
            logger.warning(f"没有找到代理，请在 {self.proxy_file} 中添加代理")
            return []
            
        results = []
        for proxy in proxies:
            logger.info(f"测试代理: {proxy}")
            success, elapsed = self.test_proxy(proxy, timeout)
            results.append({
                "proxy": proxy,
                "success": success,
                "elapsed": elapsed
            })
        
        # 更新工作代理列表
        self.working_proxies = [r["proxy"] for r in results if r["success"]]
        
        # 按响应时间排序
        results.sort(key=lambda x: x["elapsed"] if x["success"] else float("inf"))
        
        logger.info(f"测试完成: {len(self.working_proxies)}/{len(proxies)} 个代理可用")
        return results
    
    def get_proxy(self) -> Optional[str]:
        """
        获取一个可用的代理
        
        Returns:
            Optional[str]: 代理地址，如果没有可用代理则返回None
        """
        if not self.working_proxies:
            # 如果没有已知的工作代理，尝试测试所有代理
            self.test_all_proxies()
            
        if self.working_proxies:
            # 随机选择一个工作代理
            proxy = random.choice(self.working_proxies)
            logger.info(f"使用代理: {proxy}")
            return proxy
        else:
            logger.warning("没有可用的代理")
            return None
    
    def get_proxy_dict(self) -> Dict[str, str]:
        """
        获取一个可用的代理字典，用于requests库
        
        Returns:
            Dict[str, str]: 代理字典，如果没有可用代理则返回空字典
        """
        proxy = self.get_proxy()
        if proxy:
            return {
                "http": proxy,
                "https": proxy
            }
        return {}
    
    def add_proxy(self, proxy: str) -> bool:
        """
        添加一个新代理
        
        Args:
            proxy: 代理地址
            
        Returns:
            bool: 是否添加成功
        """
        proxies = self.load_proxies()
        if proxy not in proxies:
            proxies.append(proxy)
            return self.save_proxies(proxies)
        return True
    
    def remove_proxy(self, proxy: str) -> bool:
        """
        删除一个代理
        
        Args:
            proxy: 代理地址
            
        Returns:
            bool: 是否删除成功
        """
        proxies = self.load_proxies()
        if proxy in proxies:
            proxies.remove(proxy)
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
            return self.save_proxies(proxies)
        return True

# 全局实例
proxy_manager = ProxyManager()

def get_proxy() -> str:
    """
    获取一个可用的代理
    
    Returns:
        str: 代理地址，如果没有可用代理则返回空字符串
    """
    return proxy_manager.get_proxy() or ""

def get_proxy_dict() -> Dict[str, str]:
    """
    获取一个可用的代理字典，用于requests库
    
    Returns:
        Dict[str, str]: 代理字典
    """
    return proxy_manager.get_proxy_dict()

def test_proxies() -> List[Dict]:
    """
    测试所有代理是否可用
    
    Returns:
        List[Dict]: 测试结果列表
    """
    return proxy_manager.test_all_proxies()

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="代理配置管理工具")
    parser.add_argument("--test", action="store_true", help="测试所有代理")
    parser.add_argument("--add", type=str, help="添加新代理")
    parser.add_argument("--remove", type=str, help="删除代理")
    parser.add_argument("--timeout", type=int, default=10, help="代理测试超时时间（秒）")
    args = parser.parse_args()
    
    # 创建代理管理器
    manager = ProxyManager()
    manager.timeout = args.timeout
    
    if args.test:
        # 测试所有代理
        print("测试所有代理...")
        results = manager.test_all_proxies()
        
        # 打印结果
        print("\n代理测试结果:")
        print("-" * 60)
        print(f"{'代理地址':<40} {'状态':<10} {'响应时间'}")
        print("-" * 60)
        
        for result in results:
            status = "可用" if result["success"] else "不可用"
            elapsed = f"{result['elapsed']:.2f}秒" if result["success"] else "N/A"
            print(f"{result['proxy']:<40} {status:<10} {elapsed}")
        
        print("-" * 60)
        print(f"总计: {len(results)} 个代理, {len(manager.working_proxies)} 个可用")
    
    elif args.add:
        # 添加新代理
        proxy = args.add
        print(f"添加代理: {proxy}")
        
        # 测试新代理
        success, elapsed = manager.test_proxy(proxy)
        if success:
            print(f"代理可用，响应时间: {elapsed:.2f}秒")
            if manager.add_proxy(proxy):
                print(f"代理已添加到 {manager.proxy_file}")
            else:
                print("添加代理失败")
        else:
            print("代理不可用，是否仍要添加? (y/n)")
            if input().lower() == 'y':
                if manager.add_proxy(proxy):
                    print(f"代理已添加到 {manager.proxy_file}")
                else:
                    print("添加代理失败")
    
    elif args.remove:
        # 删除代理
        proxy = args.remove
        print(f"删除代理: {proxy}")
        if manager.remove_proxy(proxy):
            print(f"代理已从 {manager.proxy_file} 中删除")
        else:
            print("删除代理失败")
    
    else:
        # 默认操作：获取一个可用代理
        proxy = manager.get_proxy()
        if proxy:
            print(f"可用代理: {proxy}")
        else:
            print("没有可用的代理")
            print(f"请在 {manager.proxy_file} 中添加代理，格式：http://host:port 或 socks5://host:port") 