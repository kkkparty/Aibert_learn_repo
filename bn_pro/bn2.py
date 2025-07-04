#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import random
import csv
import argparse
import logging
import smtplib
import email.utils
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import math
import concurrent.futures
import gc
import psutil
from binance_filter import filter_binance_coins, BinanceFilter

# 尝试导入代理管理器
try:
    from proxy_manager import ProxyManager
    PROXY_SUPPORT = True
except ImportError:
    PROXY_SUPPORT = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CryptoRecommender:
    def __init__(self, use_cache_only=False, use_proxies=False, max_workers=4, cache_expiry_hours=24):
        """初始化菜价分析系统"""
        # 确保缓存目录存在
        self.cache_dir = os.path.join('crypto_data', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.use_cache_only = use_cache_only
        self.portfolio = None
        self.use_proxies = use_proxies and PROXY_SUPPORT
        self.proxy_manager = None
        
        # 新增：并行处理配置
        self.max_workers = max_workers
        # 新增：缓存过期时间(小时)
        self.cache_expiry_hours = cache_expiry_hours
        # 新增：内存使用监控
        self.peak_memory_usage = 0
        self.initial_memory_usage = self._get_memory_usage()
        
        # 初始化代理管理器
        if self.use_proxies:
            try:
                self.proxy_manager = ProxyManager()
                logger.info(f"代理管理器初始化成功，当前有 {len(self.proxy_manager.proxies)} 个代理")
            except Exception as e:
                logger.error(f"代理管理器初始化失败: {e}")
                self.proxy_manager = None
                self.use_proxies = False
        
        # 加载配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                logger.debug("已加载配置文件")
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
            logger.debug("未找到配置文件或格式错误，使用默认配置")
            
        # 创建API请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        })
        
        # 初始化成功后的消息
        if use_cache_only:
            logging.info("使用缓存模式")
            print("已激活缓存模式 - 仅使用缓存数据，不发送新请求")
        else:
            logging.info("使用API请求模式")
            print("使用API请求模式 - 会发送网络请求获取最新数据")
        
        if self.use_proxies:
            print(f"已启用代理模式 - 使用代理IP池发送请求")
            
        print(f"并行处理 - 使用 {self.max_workers} 个工作线程")
        
        self.holdings = {}
        self.recommendations = {}
        self.total_investment = 0
        self.max_position_size = 0.2  # 单个持仓最大占比
        self.data_dir = Path("crypto_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 确保结果文件夹存在
        self.csv_file = self.data_dir / 'recommendations.csv'
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['symbol', 'name', 'price', 'market_cap', 'volume_24h', 
                                'price_change_7d', 'price_change_24h', 'price_change_30d', 
                                'rsi', 'action', 'reason', 'buy_time', 'sell_time'])
        
        # API配置
        self.api_key = os.environ.get('COINGECKO_API_KEY', '')  # 如果有API密钥
        self.base_url = "https://api.coingecko.com/api/v3"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/100.0.1185.29',
        ]
        
        # API限制设置
        self.min_request_interval = 15.0  # 两次请求之间的最小间隔时间（秒）
        self.last_request_time = 0
        
        if self.use_cache_only:
            logger.info("仅使用缓存模式已启用，将不会发送任何API请求")
    
        # 新增：缓存统计
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_requests = 0
        self.api_errors = 0
    
    # 新增：内存使用监控方法
    def _get_memory_usage(self):
        """获取当前进程的内存使用情况(MB)"""
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return mem_info.rss / 1024 / 1024  # 转换为MB
        except:
            return 0
            
    def _update_memory_stats(self):
        """更新内存使用统计"""
        current_usage = self._get_memory_usage()
        if current_usage > self.peak_memory_usage:
            self.peak_memory_usage = current_usage
        
        # 如果内存使用过高，手动触发垃圾回收
        if current_usage > 1000:  # 超过1GB
            logger.warning(f"内存使用过高 ({current_usage:.2f} MB)，执行垃圾回收...")
            gc.collect()
            
        return current_usage
    
    def _get_cache_path(self, endpoint, params):
        """生成缓存文件路径"""
        # 将参数排序后转为字符串，确保相同参数但不同顺序的请求得到相同的缓存文件
        sorted_params = sorted(params.items())
        param_str = '_'.join(f"{k}={v}" for k, v in sorted_params)
        cache_filename = f"{endpoint.replace('/', '_')}_{param_str}.json"
        return os.path.join(self.cache_dir, cache_filename)
    
    def _is_cache_valid(self, cache_path, max_age_hours=None):
        """检查缓存是否有效"""
        if max_age_hours is None:
            max_age_hours = self.cache_expiry_hours
            
        if not os.path.exists(cache_path):
            return False
        
        # 检查文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_time > timedelta(hours=max_age_hours):
            return False
        
        # 检查文件内容是否有效
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except:
            return False
    
    def _make_api_request(self, endpoint, params=None, max_retries=7, base_delay=5):
        """发送API请求，带有缓存和重试机制"""
        if params is None:
            params = {}
            
        # 确保endpoint以/开头
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        # 构建URL
        url = f"{self.base_url}{endpoint}"
        
        # 检查缓存
        cache_path = self._get_cache_path(endpoint, params)
        
        # 检查缓存是否有效
        cache_valid = self._is_cache_valid(cache_path)
        
        # 仅当use_cache_only为True时才只使用缓存
        if cache_valid:
            self.cache_hits += 1
            logger.info(f"使用缓存数据: {cache_path}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取缓存文件错误 {cache_path}: {e}")
                if self.use_cache_only:
                    return None
                # 如果不是仅缓存模式，继续尝试API请求
                self.cache_misses += 1
        else:
            self.cache_misses += 1
            if self.use_cache_only:
            logger.error(f"仅缓存模式错误: 找不到有效缓存 {cache_path}")
            return None
        
        # 强制控制请求频率
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"API频率控制: 等待 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)
        
        # 如果有API密钥，添加到参数中
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        if self.api_key:
            headers['x-cg-pro-api-key'] = self.api_key
        
        logger.info(f"请求API: {url}，参数: {params}")
        self.api_requests += 1
        
        # 获取代理（如果启用代理模式）
        proxy = None
        if self.use_proxies and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy(rotate=True)
            if proxy:
                logger.info(f"使用代理: {proxy}")
        
        # 重试机制
        retry_count = 0
        proxy_error_count = 0
        while retry_count <= max_retries:
            try:
                # 添加一个随机延迟，避免请求过于规律
                if retry_count > 0:
                    # 使用更温和的退避策略，最大延迟60秒
                    retry_delay = min(base_delay * (2 ** retry_count) + random.uniform(1, 3), 60)
                    logger.warning(f"重试 {retry_count}/{max_retries}，等待 {retry_delay:.2f} 秒...")
                    time.sleep(retry_delay)
                
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    proxies=proxy,
                    timeout=60  # 更长的超时时间
                )
                
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
                    
                if response.status_code == 429:
                    # 使用更温和的退避策略，最大延迟60秒
                    retry_delay = min(base_delay * (2 ** retry_count) + random.uniform(1, 3), 60)
                    logger.warning(f"API请求限制 (429)，等待 {retry_delay:.2f} 秒后重试 ({retry_count + 1}/{max_retries})")
                    
                    # 如果启用了代理，尝试更换代理
                    if self.use_proxies and self.proxy_manager and proxy_error_count < 3:
                        proxy = self.proxy_manager.get_random_proxy()
                        if proxy:
                            logger.info(f"429错误后更换代理: {proxy}")
                            proxy_error_count += 1
                            # 使用新代理立即重试
                            continue
                    
                    time.sleep(retry_delay)
                    retry_count += 1
                    continue
                    
                logger.error(f"API请求失败: {response.status_code}, 响应: {response.text[:100]}")
                
                # 如果是代理错误，尝试更换代理
                if self.use_proxies and self.proxy_manager and response.status_code in [403, 407, 502, 503, 504]:
                    if proxy_error_count < 3:
                        proxy = self.proxy_manager.get_random_proxy()
                        if proxy:
                            logger.info(f"HTTP错误后更换代理: {proxy}")
                            proxy_error_count += 1
                            continue
                
                self.api_errors += 1
                return None
                
            except requests.exceptions.RequestException as e:
                # 对网络错误使用线性退避策略，避免过长等待
                retry_delay = min(base_delay * (retry_count + 1) + random.uniform(2, 5), 30)
                logger.warning(f"请求出错: {e}, 等待 {retry_delay:.2f} 秒后重试 ({retry_count + 1}/{max_retries})")
                
                # 如果是代理错误，尝试更换代理
                if self.use_proxies and self.proxy_manager:
                    # 判断是否是代理错误（连接超时、拒绝连接等）
                    if "Proxy" in str(e) or "timeout" in str(e) or "Connection" in str(e):
                        if proxy_error_count < 3:
                            proxy = self.proxy_manager.get_random_proxy()
                            if proxy:
                                logger.info(f"代理错误后更换代理: {proxy}")
                                proxy_error_count += 1
                                # 减少重试延迟，因为已经更换了代理
                                time.sleep(min(retry_delay / 2, 5))
                                continue
                
                time.sleep(retry_delay)
                retry_count += 1
                
        logger.error(f"已达到最大重试次数 ({max_retries})，请求失败")
        self.api_errors += 1
        return None
    
    # 新增：并行处理币种数据
    def _process_coin_data_parallel(self, coins, short_term_analysis=True):
        """并行处理多个币种数据"""
        results = []
        processed_count = 0
        skipped_count = 0
        
        def process_single_coin(coin):
            """处理单个币种数据的子函数"""
            try:
                # 记录开始处理时间
                start_time = time.time()
                
                coin_id = coin.get('id', '')
                symbol = coin.get('symbol', '').upper()
                
                # 如果没有ID或符号，跳过
                if not coin_id or not symbol:
                    return {'status': 'skipped', 'reason': 'missing_id_or_symbol'}
                
                # 获取价格历史数据
                price_df = self.fetch_price_history(coin_id, days=30)
                if price_df is None or price_df.empty:
                    return {'status': 'skipped', 'reason': 'no_price_data', 'coin': coin}
                
                # 分析市场趋势
                market_trend = self.analyze_market_trend(price_df)
                
                # 计算技术指标
                indicators = self.calculate_technical_indicators(price_df)
                if indicators is None:
                    return {'status': 'skipped', 'reason': 'no_indicators', 'coin': coin}
                
                # 确保indicators是字典类型
                if not isinstance(indicators, dict):
                    indicators = {}
                    logger.warning(f"技术指标类型错误: {type(indicators)}, 使用空字典代替")
                
                # 获取多时间维度价格变化
                price_changes = self.fetch_price_changes(coin_id)
                if price_changes:
                    # 将价格变化数据合并到币种数据中
                    for key, value in price_changes.items():
                        if key not in coin:
                            coin[key] = value
                
                # 计算与BTC的相关性
                correlation_data = self.calculate_correlation_with_btc(coin_id)
                if correlation_data:
                    correlation = correlation_data.get('returns_correlation')
                    beta = correlation_data.get('beta')
                    if correlation is not None:
                        coin['btc_correlation'] = correlation
                    if beta is not None:
                        coin['btc_beta'] = beta
                
                # 确定买入行动
                recommendation = self.determine_buy_action(coin, indicators, market_trend)
                
                # 处理返回的元组(buy_decision, recommendation)
                if isinstance(recommendation, tuple) and len(recommendation) == 2:
                    buy_decision, recommendation_dict = recommendation
                    recommendation = recommendation_dict  # 使用推荐字典部分
                
                # 添加短线交易分析
                if short_term_analysis:
                    # 获取短期价格数据（7天，小时级别）
                    short_df = self.fetch_price_history(coin_id, days=7, interval='1h')
                    if short_df is not None and not short_df.empty:
                        # 计算短期技术指标
                        short_indicators = self.calculate_technical_indicators(short_df, is_short_term=True)
                        if short_indicators:
                            # 确保short_indicators是字典类型
                            if not isinstance(short_indicators, dict):
                                short_indicators = {}
                                logger.warning(f"短期技术指标类型错误: {type(short_indicators)}, 使用空字典代替")
                            
                            # 短期市场趋势
                            short_trend = self.analyze_market_trend(short_df)
                            # 短期买入分析
                            short_recommendation = self.determine_short_term_buy_action(
                                coin, short_indicators, short_trend
                            )
                            
                            # 处理返回的元组(buy_decision, recommendation)
                            if isinstance(short_recommendation, tuple) and len(short_recommendation) == 2:
                                short_buy_decision, short_recommendation_dict = short_recommendation
                                short_recommendation = short_recommendation_dict  # 使用推荐字典部分
                                
                            # 合并短期推荐到长期推荐中
                            recommendation['short_term'] = short_recommendation
                
                # 添加技术指标到推荐中
                recommendation['indicators'] = indicators
                recommendation['market_trend'] = market_trend
                
                # 计算处理时间
                processing_time = time.time() - start_time
                recommendation['processing_time'] = processing_time
                
                return {'status': 'success', 'recommendation': recommendation, 'coin': coin}
                
            except Exception as e:
                logger.error(f"处理币种 {coin.get('symbol', 'unknown')} 时出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {'status': 'error', 'error': str(e), 'coin': coin}
        
        # 使用线程池并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_coin = {executor.submit(process_single_coin, coin): coin for coin in coins}
            
            # 处理结果
            for future in tqdm(concurrent.futures.as_completed(future_to_coin), total=len(coins), desc="处理币种数据"):
                coin = future_to_coin[future]
                try:
                    result = future.result()
                    status = result.get('status')
                    
                    if status == 'success':
                        results.append(result)
                        processed_count += 1
                    elif status == 'skipped':
                        skipped_count += 1
                    elif status == 'error':
                        logger.error(f"处理币种 {coin.get('symbol', 'unknown')} 时出错: {result.get('error')}")
                        skipped_count += 1
                        
                    # 监控并更新内存使用情况
                    if processed_count % 10 == 0:
                        self._update_memory_stats()
                        
                except Exception as e:
                    logger.error(f"处理币种 {coin.get('symbol', 'unknown')} 的结果时出错: {e}")
                    skipped_count += 1
                    
        return {
            'results': results,
            'processed_count': processed_count,
            'skipped_count': skipped_count
        }
        
    # 新增：缓存清理方法
    def clean_cache(self, max_age_days=7):
        """清理旧的缓存文件"""
        logger.info(f"清理超过 {max_age_days} 天的缓存文件...")
        cache_files = os.listdir(self.cache_dir)
        cleaned_count = 0
        
        for file_name in cache_files:
            file_path = os.path.join(self.cache_dir, file_name)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_time > timedelta(days=max_age_days):
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        logger.error(f"删除缓存文件失败 {file_path}: {e}")
                        
        logger.info(f"缓存清理完成，删除了 {cleaned_count} 个旧文件")
        return cleaned_count
        
    # 新增：获取缓存统计
    def get_cache_stats(self):
        """获取缓存使用统计"""
        # 计算缓存命中率
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        # 获取缓存大小
        cache_size = 0
        file_count = 0
        for file_name in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file_name)
            if os.path.isfile(file_path):
                cache_size += os.path.getsize(file_path)
                file_count += 1
                
        # 转换为MB
        cache_size_mb = cache_size / (1024 * 1024)
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': cache_hit_rate,
            'api_requests': self.api_requests,
            'api_errors': self.api_errors,
            'file_count': file_count,
            'cache_size_mb': cache_size_mb,
            'peak_memory_mb': self.peak_memory_usage,
            'current_memory_mb': self._get_memory_usage()
        }
    
    def fetch_coin_data(self, limit=1000):
        """获取蔬菜市场数据"""
        logger.info(f"正在获取前 {limit} 种蔬菜数据...")
        
        endpoint = 'coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': min(250, limit),  # API单页最大250个
            'page': 1,
            'sparkline': 'false',
            'locale': 'en',
            'price_change_percentage': '24h,7d,30d'  # 增加30天价格变化
        }
        
        all_coins = []
        pages_needed = math.ceil(limit / params['per_page'])
        
        try:
            for page in range(1, pages_needed + 1):
                params['page'] = page
                
                # 尝试从缓存获取数据
                cache_path = self._get_cache_path(endpoint, params)
                if os.path.exists(cache_path) and self._is_cache_valid(cache_path):
                    logger.debug(f"从缓存加载蔬菜数据 (第{page}页): {cache_path}")
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    if self.use_cache_only:
                        logger.warning(f"缓存数据不存在或已过期，但处于仅缓存模式: {cache_path}")
                        continue
                        
                    # 从API获取数据
                    logger.info(f"获取蔬菜数据 (第{page}/{pages_needed}页)...")
                    data = self._make_api_request(endpoint, params)
                    
                    # 保存到缓存
                    if data:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                
                if data:
                    all_coins.extend(data)
                    logger.info(f"已获取 {len(all_coins)}/{limit} 种蔬菜数据")
                    
                    # 达到要求的数量后结束
                    if len(all_coins) >= limit:
                        break
                        
                # API请求之间暂停，避免触发速率限制
                if not self.use_cache_only and page < pages_needed:
                    time.sleep(5)
            
            # 确保BTC在列表首位（因为它是基准币）
            btc_index = -1
            for i, coin in enumerate(all_coins):
                if coin.get('symbol', '').lower() == 'btc':
                    btc_index = i
                    break
                    
            if btc_index > 0:  # 如果BTC不在首位，将其移到首位
                btc_coin = all_coins.pop(btc_index)
                all_coins.insert(0, btc_coin)
                logger.info("已将BTC移到列表首位")
            
            # 限制数量并返回
            return all_coins[:limit]
            
        except Exception as e:
            logger.error(f"获取蔬菜数据时出错: {e}")
            return all_coins if all_coins else None
    
    def fetch_price_history(self, coin_id, days=30, interval='daily'):
        """获取蔬菜价格历史数据
        
        参数:
        coin_id -- 蔬菜ID
        days -- 获取的天数，可选值: 1, 7, 14, 30, 90, 180, 365, max
        interval -- 时间间隔，可选值: 1h(小时), daily, weekly, monthly
                    当days=1时, 可选择1h获取小时级别数据
                    当days>1时, 一般使用daily
        """
        logger.debug(f"获取蔬菜 {coin_id} 的价格历史 (过去 {days} 天, 间隔: {interval})")
        
        # 验证参数有效性
        valid_intervals = ['1h', 'daily', 'weekly', 'monthly']
        # 将hourly转换为1h以匹配API要求
        if interval == 'hourly':
            interval = '1h'
            logger.debug(f"将interval参数从'hourly'转换为'1h'")
            
        if interval not in valid_intervals:
            logger.warning(f"无效的时间间隔: {interval}, 使用默认值: daily")
            interval = 'daily'
            
        # 当获取小时数据时，限制天数为1-7天
        if interval == '1h' and days > 7:
            logger.warning(f"小时级别数据最多获取7天, 已将天数从 {days} 调整为 7")
            days = 7
        
        endpoint = f'coins/{coin_id}/market_chart'
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': interval
        }
        
        try:
            # 尝试从缓存获取数据
            cache_path = self._get_cache_path(endpoint, params)
            
            # 仅在use_cache_only为True时才使用缓存
            if self.use_cache_only and self._is_cache_valid(cache_path):
                logger.debug(f"从缓存加载价格历史: {cache_path}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                if self.use_cache_only:
                    logger.warning(f"缓存数据不存在或已过期，但处于仅缓存模式: {cache_path}")
                    return None
                    
                # 从API获取数据
                data = self._make_api_request(endpoint, params)
                
                # 保存到缓存
                if data:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
            # 检查数据有效性
            if not data or 'prices' not in data or not data['prices']:
                logger.error(f"获取到的价格历史数据无效: {data}")
                return None
                
            # 将数据转换为DataFrame
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            # 创建价格DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            
            # 确保price列为float类型
            df['price'] = df['price'].astype(float)
            
            # 如果有成交量数据，添加到DataFrame
            if volumes and len(volumes) == len(prices):
                volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                # 确保volume列为float类型
                volume_df['volume'] = volume_df['volume'].astype(float)
                # 确保timestamp相同
                if np.array_equal(df['timestamp'].values, volume_df['timestamp'].values):
                    df['volume'] = volume_df['volume']
                else:
                    # 如果timestamp不同，需要进行合并
                    volume_df.set_index('timestamp', inplace=True)
                    df.set_index('timestamp', inplace=True)
                    df = pd.merge(df, volume_df, left_index=True, right_index=True, how='left')
                    df.reset_index(inplace=True)
            
            # 将时间戳转换为日期
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 确保列名兼容其他方法
            if 'price' in df.columns and 'close' not in df.columns:
                df['close'] = df['price'].astype(float)
                
            # 添加OHLC列（如果只有收盘价）
            if 'open' not in df.columns:
                df['open'] = df['close'].astype(float)
            if 'high' not in df.columns:
                df['high'] = df['close'].astype(float)
            if 'low' not in df.columns:
                df['low'] = df['close'].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"获取价格历史时出错: {e}")
            return None
    
    def fetch_price_changes(self, coin_id):
        """获取多个时间维度的价格变化数据"""
        logger.debug(f"获取蔬菜 {coin_id} 的多时间维度价格变化数据")
        
        endpoint = f'coins/{coin_id}'
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        
        try:
            data = self._make_api_request(endpoint, params)
            
            if not data or 'market_data' not in data:
                logger.error(f"获取价格变化数据失败: {data}")
                return None
                
            market_data = data['market_data']
            price_changes = {}
            
            # 提取不同时间维度的价格变化
            if 'price_change_percentage_1h_in_currency' in market_data:
                price_changes['1h'] = market_data['price_change_percentage_1h_in_currency'].get('usd', 0)
            
            if 'price_change_percentage_24h' in market_data:
                price_changes['24h'] = market_data['price_change_percentage_24h']
                
            if 'price_change_percentage_7d' in market_data:
                price_changes['7d'] = market_data['price_change_percentage_7d']
                
            if 'price_change_percentage_14d' in market_data:
                price_changes['14d'] = market_data['price_change_percentage_14d']
                
            if 'price_change_percentage_30d' in market_data:
                price_changes['30d'] = market_data['price_change_percentage_30d']
                
            if 'price_change_percentage_200d' in market_data:
                price_changes['200d'] = market_data['price_change_percentage_200d']
                
            if 'price_change_percentage_1y' in market_data:
                price_changes['1y'] = market_data['price_change_percentage_1y']
                
            # 添加当前价格
            if 'current_price' in market_data:
                price_changes['current_price'] = market_data['current_price'].get('usd', 0)
                
            # 添加24小时交易量
            if 'total_volume' in market_data:
                price_changes['total_volume'] = market_data['total_volume'].get('usd', 0)
                
            # 添加市值
            if 'market_cap' in market_data:
                price_changes['market_cap'] = market_data['market_cap'].get('usd', 0)
                
            return price_changes
                
        except Exception as e:
            logger.error(f"获取价格变化数据时出错: {e}")
            return None
    
    def calculate_technical_indicators(self, df, is_short_term=False):
        """计算蔬菜价格的技术指标
        
        参数:
        df -- 包含价格和成交量数据的DataFrame
        is_short_term -- 是否计算短线交易指标 (True: 更多短线指标, False: 基本指标)
        """
        try:
            # 确保有必要的列
            if 'close' not in df.columns and 'price' in df.columns:
                df['close'] = df['price'].astype(float)  # 兼容不同数据格式
                
            # 确保数据足够用于计算指标
            min_data_points = 30
            if is_short_term:
                min_data_points = 60  # 短线分析需要更多数据点
                
            if len(df) < min_data_points:
                logger.warning(f"数据点不足，无法计算完整的技术指标: 仅有 {len(df)} 个数据点，需要至少 {min_data_points} 个")
                if len(df) < 14:  # 至少需要14个点才能计算RSI
                return None
                
            # 转换数据类型为float，避免计算错误
            df['close'] = df['close'].astype(float)
            if 'volume' in df.columns:
                df['volume'] = df['volume'].astype(float)
            
            # ---------- 基本指标计算 ----------
            
            # 1. 移动平均线 (MA)
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma50'] = df['close'].rolling(window=50).mean()
            if len(df) >= 200:
                df['ma200'] = df['close'].rolling(window=200).mean()
            
            # 2. 指数移动平均线 (EMA)
            df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
            df['ema10'] = df['close'].ewm(span=10, adjust=False).mean()
            df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
            if len(df) >= 200:
                df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
            
            # 3. RSI (相对强弱指标) - 14周期
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            # 避免除零错误
            loss = loss.replace(0, np.inf)  # 使用无穷大替代0，确保结果为0
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # RSI超买超卖判断
            df['rsi_overbought'] = df['rsi'] > 70
            df['rsi_oversold'] = df['rsi'] < 30
            
            # 4. MACD (移动平均聚散指标)
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['signal']
            
            # MACD柱状图变化率
            df['macd_hist_change'] = df['macd_hist'].pct_change()
            
            # 5. 布林带 (Bollinger Bands)
            middle = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['bb_middle'] = middle
            df['bb_upper'] = middle + (std * 2)
            df['bb_lower'] = middle - (std * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']  # 波动率指标
            
            # 布林带位置指标 (B%)
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # 6. 随机指标 (Stochastic Oscillator)
            high_14 = df['close'].rolling(window=14).max()
            low_14 = df['close'].rolling(window=14).min()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # 7. 平均方向指数 (ADX) - 趋势强度指标
            if len(df) >= 28:
                # 1. 计算TR (True Range)
                if 'high' in df.columns and 'low' in df.columns:
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    high = df['high']
                    low = df['low']
                else:
                    # 如果没有high/low数据，使用收盘价估算
                    high = df['close'] * 1.01
                    low = df['close'] * 0.99
                    
                df['tr'] = np.maximum(
                    high - low,
                    np.maximum(
                        abs(high - df['close'].shift(1)),
                        abs(low - df['close'].shift(1))
                    )
                )
                
                # 2. 计算+DM和-DM (Directional Movement)
                df['dm_plus'] = np.where(
                    (high - high.shift(1)) > (low.shift(1) - low),
                    np.maximum(high - high.shift(1), 0),
                    0
                )
                df['dm_minus'] = np.where(
                    (low.shift(1) - low) > (high - high.shift(1)),
                    np.maximum(low.shift(1) - low, 0),
                    0
                )
                
                # 3. 计算14周期平滑TR, +DM, -DM
                df['tr_14'] = df['tr'].rolling(window=14).sum()
                df['dm_plus_14'] = df['dm_plus'].rolling(window=14).sum()
                df['dm_minus_14'] = df['dm_minus'].rolling(window=14).sum()
                
                # 4. 计算+DI和-DI (Directional Indicator)
                df['di_plus'] = 100 * (df['dm_plus_14'] / df['tr_14'])
                df['di_minus'] = 100 * (df['dm_minus_14'] / df['tr_14'])
                
                # 5. 计算DX (Directional Index)
                df['dx'] = 100 * (abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus']))
                
                # 6. 计算ADX (Average Directional Index)
                df['adx'] = df['dx'].rolling(window=14).mean()
                
                # 7. 趋势强度判断
                df['strong_trend'] = df['adx'] > 25
                df['very_strong_trend'] = df['adx'] > 50
                df['weak_trend'] = df['adx'] < 20
            
            # 8. 震荡指标: CCI (Commodity Channel Index)
            if 'high' in df.columns and 'low' in df.columns:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
        else:
                typical_price = df['close']
                
            ma_tp = typical_price.rolling(window=20).mean()
            mean_deviation = abs(typical_price - ma_tp).rolling(window=20).mean()
            df['cci'] = (typical_price - ma_tp) / (0.015 * mean_deviation)
            
            # 9. 动量指标 (Momentum)
            df['momentum_5'] = df['close'] - df['close'].shift(5)
            df['momentum_10'] = df['close'] - df['close'].shift(10)
            df['roc_5'] = df['close'].pct_change(periods=5) * 100  # 5日变动率
            df['roc_10'] = df['close'].pct_change(periods=10) * 100  # 10日变动率
            
            # ---------- 短线指标计算 (如果需要) ----------
            if is_short_term:
                if 'volume' in df.columns:
                    # 10. 成交量变化
                    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
                    df['volume_ma10'] = df['volume'].rolling(window=10).mean()
                    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
                    
                    # 成交量相对变化率
                    df['volume_change'] = df['volume'].pct_change()
                    df['volume_roc_5'] = df['volume'].pct_change(periods=5) * 100
                    
                    # 11. OBV (On-Balance Volume)
                    df['obv'] = np.where(df['close'] > df['close'].shift(1), 
                                      df['volume'], 
                                      np.where(df['close'] < df['close'].shift(1), 
                                             -df['volume'], 0)).cumsum()
                                             
                    # 12. 资金流量指标 (MFI - Money Flow Index)
                    if 'high' in df.columns and 'low' in df.columns:
                        typical_price = (df['high'] + df['low'] + df['close']) / 3
                        raw_money_flow = typical_price * df['volume']
                        positive_flow = np.where(typical_price > typical_price.shift(1), raw_money_flow, 0)
                        negative_flow = np.where(typical_price < typical_price.shift(1), raw_money_flow, 0)
                        
                        positive_flow_14 = pd.Series(positive_flow).rolling(window=14).sum()
                        negative_flow_14 = pd.Series(negative_flow).rolling(window=14).sum()
                        
                        money_ratio = positive_flow_14 / negative_flow_14
                        df['mfi'] = 100 - (100 / (1 + money_ratio))
                
                # 13. 乖离率 (BIAS)
                df['bias5'] = (df['close'] - df['ma5']) / df['ma5'] * 100
                df['bias10'] = (df['close'] - df['ma10']) / df['ma10'] * 100
                df['bias20'] = (df['close'] - df['ma20']) / df['ma20'] * 100
                
                # 14. 威廉指标 (Williams %R)
                high_14 = df['close'].rolling(window=14).max()
                low_14 = df['close'].rolling(window=14).min()
                df['williams_r'] = ((high_14 - df['close']) / (high_14 - low_14)) * -100
                
                # 15. 抛物线指标 (Parabolic SAR)
                # 简化版SAR计算 
                df['sar'] = df['close'].shift(1)
                df['rising'] = df['close'] > df['close'].shift(1)
                df['falling'] = df['close'] < df['close'].shift(1)
                
                # 16. 动量震荡指标 (Rate of Change)
                df['roc_1'] = df['close'].pct_change(periods=1) * 100  # 1日变动率
                df['roc_3'] = df['close'].pct_change(periods=3) * 100  # 3日变动率
            
            # ---------- 模式识别 ----------
            
            # 17. 价格突破识别
            df['ma5_crossover_ma10'] = (df['ma5'] > df['ma10']) & (df['ma5'].shift(1) <= df['ma10'].shift(1))
            df['ma5_crossunder_ma10'] = (df['ma5'] < df['ma10']) & (df['ma5'].shift(1) >= df['ma10'].shift(1))
            df['ma10_crossover_ma20'] = (df['ma10'] > df['ma20']) & (df['ma10'].shift(1) <= df['ma20'].shift(1))
            df['ma10_crossunder_ma20'] = (df['ma10'] < df['ma20']) & (df['ma10'].shift(1) >= df['ma20'].shift(1))
            
            # 18. 三重MA指标
            if len(df) >= 60:
                df['ma5_ma10_ma20_aligned_up'] = (df['ma5'] > df['ma10']) & (df['ma10'] > df['ma20'])
                df['ma5_ma10_ma20_aligned_down'] = (df['ma5'] < df['ma10']) & (df['ma10'] < df['ma20'])
            
            # 19. 支撑阻力识别
            df['close_above_upper_bb'] = df['close'] > df['bb_upper']
            df['close_below_lower_bb'] = df['close'] < df['bb_lower']
            df['inside_bb'] = (df['close'] >= df['bb_lower']) & (df['close'] <= df['bb_upper'])
            
            # 20. 趋势确认
            df['macd_above_signal'] = df['macd'] > df['signal']
            df['macd_crossover'] = (df['macd'] > df['signal']) & (df['macd'].shift(1) <= df['signal'].shift(1))
            df['macd_crossunder'] = (df['macd'] < df['signal']) & (df['macd'].shift(1) >= df['signal'].shift(1))
            
            # 21. 均线和价格关系
            df['price_above_ma5'] = df['close'] > df['ma5']
            df['price_above_ma10'] = df['close'] > df['ma10']
            df['price_above_ma20'] = df['close'] > df['ma20']
            df['price_above_ma50'] = df['close'] > df['ma50']
            if len(df) >= 200:
                df['price_above_ma200'] = df['close'] > df['ma200']
            
            # 22. 振荡器超买超卖确认
            df['stoch_k_crossover_stoch_d'] = (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1))
            df['stoch_k_crossunder_stoch_d'] = (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1))
            
            # 23. 反转形态识别
            # 双顶/双底识别 (简化版)
            peaks = df['close'].rolling(window=5, center=True).apply(
                lambda x: 1 if x.iloc[2] == max(x) else 0, raw=False
            )
            troughs = df['close'].rolling(window=5, center=True).apply(
                lambda x: 1 if x.iloc[2] == min(x) else 0, raw=False
            )
            df['is_peak'] = peaks
            df['is_trough'] = troughs
            
            # 返回计算后的指标
            indicators = {}
            
            # 提取最近的指标值
            for col in ['rsi', 'macd', 'signal', 'macd_hist', 'bb_middle', 'bb_upper', 
                     'bb_lower', 'bb_width', 'stoch_k', 'stoch_d', 'ma5', 'ma10', 
                     'ma20', 'ma50', 'ema5', 'ema10', 'ema20', 'momentum_5', 'roc_5',
                     'bias5', 'bias10', 'bias20', 'cci', 'bb_pct', 'strong_trend',
                     'very_strong_trend']:
                if col in df.columns:
                    indicators[col] = df[col].iloc[-1]
            
            # 如果有200日均线数据
            if 'ma200' in df.columns:
                indicators['ma200'] = df['ma200'].iloc[-1]
            if 'ema200' in df.columns:
                indicators['ema200'] = df['ema200'].iloc[-1]
            
            # 提取短线指标值
            if is_short_term and 'volume' in df.columns:
                for col in ['volume_ma5', 'volume_ma10', 'volume_change', 
                         'volume_roc_5', 'obv', 'mfi', 'williams_r', 'roc_1', 'roc_3']:
                    if col in df.columns:
                        indicators[col] = df[col].iloc[-1]
            
            # 添加ADX指标(如果计算了)
            if 'adx' in df.columns:
                indicators['adx'] = df['adx'].iloc[-1]
                indicators['di_plus'] = df['di_plus'].iloc[-1]
                indicators['di_minus'] = df['di_minus'].iloc[-1]
            
            # 计算其他派生指标
            indicators['rsi_oversold'] = indicators.get('rsi', 50) < 30
            indicators['rsi_overbought'] = indicators.get('rsi', 50) > 70
            
            # MACD指标
            indicators['macd_positive'] = indicators.get('macd', 0) > 0
            indicators['macd_crossover'] = df['macd'].iloc[-1] > df['signal'].iloc[-1] and df['macd'].iloc[-2] <= df['signal'].iloc[-2]
            indicators['macd_crossunder'] = df['macd'].iloc[-1] < df['signal'].iloc[-1] and df['macd'].iloc[-2] >= df['signal'].iloc[-2]
            
            # 多均线关系
            indicators['price_above_ma20'] = df['close'].iloc[-1] > indicators.get('ma20', 0)
            
            # 随机指标
            indicators['stoch_oversold'] = indicators.get('stoch_k', 50) < 20
            indicators['stoch_overbought'] = indicators.get('stoch_k', 50) > 80
            
            # 技术形态分析
            indicators['golden_cross'] = False
            indicators['death_cross'] = False
            
            # 确保数据足够长才计算金叉/死叉
            if len(df) > 50 and 'ma50' in df.columns and 'ma20' in df.columns:
                # 金叉：20日均线上穿50日均线
                if df['ma20'].iloc[-1] > df['ma50'].iloc[-1] and df['ma20'].iloc[-2] <= df['ma50'].iloc[-2]:
                    indicators['golden_cross'] = True
                
                # 死叉：20日均线下穿50日均线
                if df['ma20'].iloc[-1] < df['ma50'].iloc[-1] and df['ma20'].iloc[-2] >= df['ma50'].iloc[-2]:
                    indicators['death_cross'] = True
            
            # 计算趋势强度(基于多个指标综合)
            trend_score = 0
            
            # 根据均线排列判断趋势
            if 'ma5' in df.columns and 'ma10' in df.columns and 'ma20' in df.columns:
                if df['ma5'].iloc[-1] > df['ma10'].iloc[-1] > df['ma20'].iloc[-1]:
                    trend_score += 2  # 多头排列
                elif df['ma5'].iloc[-1] < df['ma10'].iloc[-1] < df['ma20'].iloc[-1]:
                    trend_score -= 2  # 空头排列
            
            # MACD判断趋势
            if 'macd' in df.columns and 'signal' in df.columns:
                if df['macd'].iloc[-1] > 0 and df['macd'].iloc[-1] > df['signal'].iloc[-1]:
                    trend_score += 1  # MACD位于零轴上方且高于信号线
                elif df['macd'].iloc[-1] < 0 and df['macd'].iloc[-1] < df['signal'].iloc[-1]:
                    trend_score -= 1  # MACD位于零轴下方且低于信号线
            
            # RSI判断趋势
            if 'rsi' in df.columns:
                rsi_value = df['rsi'].iloc[-1]
                if rsi_value > 60:
                    trend_score += 1  # RSI处于强势区域
                elif rsi_value < 40:
                    trend_score -= 1  # RSI处于弱势区域
            
            # ADX判断趋势强度
            if 'adx' in df.columns and 'di_plus' in df.columns and 'di_minus' in df.columns:
                adx_value = df['adx'].iloc[-1]
                di_plus = df['di_plus'].iloc[-1]
                di_minus = df['di_minus'].iloc[-1]
                
                if adx_value > 25:  # 强趋势
                    if di_plus > di_minus:
                        trend_score += 2  # 强上升趋势
                    else:
                        trend_score -= 2  # 强下降趋势
            
            # 价格与布林带关系
            if 'bb_middle' in df.columns and 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                price = df['close'].iloc[-1]
                if price > df['bb_middle'].iloc[-1]:
                    trend_score += 0.5
                    if price > df['bb_upper'].iloc[-1]:
                        trend_score += 0.5  # 价格高于上轨
                elif price < df['bb_middle'].iloc[-1]:
                    trend_score -= 0.5
                    if price < df['bb_lower'].iloc[-1]:
                        trend_score -= 0.5  # 价格低于下轨
            
            # 最终趋势评级
            if trend_score >= 3:
                indicators['trend'] = "强势上升"
            elif trend_score >= 1:
                indicators['trend'] = "上升趋势"
            elif trend_score <= -3:
                indicators['trend'] = "强势下降"
            elif trend_score <= -1:
                indicators['trend'] = "下降趋势"
            else:
                indicators['trend'] = "横盘整理"
            
            indicators['trend_score'] = trend_score
            
            # 计算价格波动性
            if len(df) >= 20:
                volatility = df['close'].pct_change().std() * 100  # 日收益率标准差
                indicators['volatility'] = volatility
                indicators['high_volatility'] = volatility > 5  # 5%以上为高波动
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_recommendations(self, current_date, limit=None, sort_by='score', save_timestamp=True, save_all_data=False, short_term_analysis=True):
        """生成蔬菜推荐结果
        
        参数:
        current_date -- 当前日期 (用于标记数据)
        limit -- 限制分析的蔬菜数量
        sort_by -- 排序字段: score(综合评分), market_cap(受欢迎度), price_change_24h(24h价格变化), 
                   price_change_7d(7d价格变化), rsi, volume_24h(交易量)
        save_timestamp -- 是否保存带时间戳的结果文件
        save_all_data -- 是否保存所有获取的原始蔬菜数据
        short_term_analysis -- 是否进行短线分析
        """
        # 重置性能统计
        start_time = time.time()
        self.peak_memory_usage = self._get_memory_usage()
        self.initial_memory_usage = self.peak_memory_usage
        
        # 清理旧缓存文件，减少磁盘占用
        self.clean_cache(max_age_days=30)  # 清理超过30天的缓存
        
        # 分析BTC风险等级，用作参考
        btc_risk = self.analyze_btc_risk()
        btc_risk_level = "未知"
        btc_risk_score = 50
        
        if btc_risk:
            btc_risk_level = btc_risk.get('level', '未知')
            btc_risk_score = btc_risk.get('score', 50)
            logger.info(f"BTC风险级别: {btc_risk_level} (得分: {btc_risk_score})")
            for factor in btc_risk.get('factors', []):
                logger.info(f"- {factor}")
        
        # 获取蔬菜数据
        coins = self.fetch_coin_data(limit=limit or 1000)
        if not coins:
            logger.error("无法获取蔬菜数据")
            return None
            
        # 如果需要，保存原始数据
            if save_all_data:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            raw_data_path = os.path.join('crypto_data', f'all_coins_{timestamp}.json')
            try:
                with open(raw_data_path, 'w', encoding='utf-8') as f:
                    json.dump(coins, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存原始数据到 {raw_data_path}")
        except Exception as e:
                logger.error(f"保存原始数据时出错: {e}")
        
        # 准备要分析的币种
        if limit and len(coins) > limit:
            coins = coins[:limit]
            
        total_count = len(coins)
        logger.info(f"开始分析 {total_count} 种蔬菜...")
        
        # 使用并行处理方法
        processing_results = self._process_coin_data_parallel(coins, short_term_analysis=short_term_analysis)
        
        # 处理并行处理结果
        results = processing_results.get('results', [])
        processed_count = processing_results.get('processed_count', 0)
        skipped_count = processing_results.get('skipped_count', 0)
        
        # 构建推荐列表
        recommendations = []
        long_term_count = 0
        short_term_count = 0
        
        for result in results:
            if result.get('status') == 'success':
                recommendation = result.get('recommendation')
                coin = result.get('coin')
                
                if recommendation.get('action') == 'buy':
                    # 增加BTC风险信息
                    recommendation['btc_risk_level'] = btc_risk_level
                    recommendation['btc_risk_score'] = btc_risk_score
                    
                    # 将币种添加到推荐列表
                    recommendations.append(recommendation)
                    long_term_count += 1
                    
                    # 添加到CSV
                    self.append_recommendation_to_csv(coin.get('symbol', ''), recommendation)
                
                # 检查短期推荐
                if short_term_analysis and 'short_term' in recommendation:
                    short_rec = recommendation['short_term']
                    if short_rec.get('action') == 'buy':
                        # 创建一个短期推荐的副本
                        short_copy = recommendation.copy()
                        short_copy.update(short_rec)
                        short_copy['is_short_term'] = True
                        
                        # 增加BTC风险信息
                        short_copy['btc_risk_level'] = btc_risk_level
                        short_copy['btc_risk_score'] = btc_risk_score
                        
                        # 添加到推荐列表
                        recommendations.append(short_copy)
                        short_term_count += 1
                        
                        # 添加到CSV（标记为短期）
                        short_copy['reason'].append("短线交易推荐")
                        self.append_recommendation_to_csv(coin.get('symbol', ''), short_copy)
        
        # 根据指定字段排序
        if sort_by in ['score', 'market_cap', 'volume_24h']:
            recommendations.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        elif sort_by in ['price_change_24h', 'price_change_7d', 'rsi']:
            # 按照上涨百分比排序
                recommendations.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
                
        # 创建结果对象
        result_object = {
            'recommendations': recommendations,
            'recommendations_count': len(recommendations),
            'long_term_count': long_term_count,
            'short_term_count': short_term_count,
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S') if save_timestamp else None,
            'total_count': total_count,
            'analyzed_count': processed_count,
            'skipped_count': skipped_count,
            'btc_risk_level': btc_risk_level,
            'btc_risk_score': btc_risk_score,
            'processing_time': time.time() - start_time,
            'peak_memory_mb': self.peak_memory_usage,
            'cache_stats': self.get_cache_stats()
        }
        
        # 默认应用币安过滤
        logger.info("应用币安过滤器，只保留币安支持的币种...")
        result_object = filter_binance_coins(result_object, include_binance_only=True)
                
        # 保存结果
        if save_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_file = self.save_results_with_timestamp(result_object['recommendations'], timestamp)
            logger.info(f"已保存结果到 {result_file}")
        
        # 显示结果摘要
        logger.info(f"推荐摘要: 总共 {len(result_object['recommendations'])} 个推荐")
        logger.info(f"- 长线推荐: {result_object['long_term_count']} 个")
        if short_term_analysis:
            logger.info(f"- 短线推荐: {result_object['short_term_count']} 个")
        
        # 统计处理时间和内存使用
        end_time = time.time()
        processing_time = end_time - start_time
        current_memory = self._get_memory_usage()
        
        logger.info(f"分析完成，处理时间: {processing_time:.2f} 秒")
        logger.info(f"内存使用: 当前 {current_memory:.2f} MB, 峰值 {self.peak_memory_usage:.2f} MB")
        
        # 获取缓存统计
        cache_stats = self.get_cache_stats()
        logger.info(f"缓存统计: 命中率 {cache_stats['hit_rate']*100:.2f}%, 缓存大小 {cache_stats['cache_size_mb']:.2f} MB")
        logger.info(f"API请求: 总数 {cache_stats['api_requests']}, 错误 {cache_stats['api_errors']}")
        
        # 执行垃圾回收
        gc.collect()
        
        return result_object

    def simulate_daily_reminders(self, days=7, limit=None, sort_by='score', save_timestamp=True, save_all_data=False, short_term_analysis=True):
        """模拟每日推荐提醒
        
        参数:
        days -- 模拟的天数(1=今天)
        limit -- 限制分析的蔬菜数量
        sort_by -- 排序字段
        save_timestamp -- 是否保存带时间戳的结果文件
        save_all_data -- 是否保存所有获取的原始蔬菜数据
        short_term_analysis -- 是否进行短线分析
        """
        logger.info(f"执行蔬菜分析 (分析 {days} 天内的数据)")
        
        # 设置当前日期
        current_date = datetime.now()
        
        # 生成今天的推荐
        results = self.generate_recommendations(
            current_date=current_date,
            limit=limit,
            sort_by=sort_by,
            save_timestamp=save_timestamp,
            save_all_data=save_all_data,
            short_term_analysis=short_term_analysis
        )
        
        if not results:
            logger.error("生成推荐失败")
            return None
            
        # 获取BTC风险分析结果
        btc_risk_analysis = self.analyze_btc_risk()
        if btc_risk_analysis:
            # 添加市场评述到结果中
            results['market_comment'] = btc_risk_analysis.get('market_comment', '')
            
            # 添加积极和消极因素
            results['positive_factors'] = btc_risk_analysis.get('positive_factors', [])
            results['negative_factors'] = btc_risk_analysis.get('negative_factors', [])
            
            # 添加中文风险级别
            results['btc_risk_level_zh'] = btc_risk_analysis.get('level_zh', '中等')
            
        # 输出性能统计
        if 'processing_time' in results:
            print(f"\n处理完成, 用时: {results['processing_time']:.2f} 秒")
            print(f"内存峰值: {results.get('peak_memory_mb', 0):.2f} MB")
            
            cache_stats = results.get('cache_stats', {})
            if cache_stats:
                print(f"缓存命中率: {cache_stats.get('hit_rate', 0)*100:.2f}%")
                print(f"API请求: {cache_stats.get('api_requests', 0)} 个, 错误: {cache_stats.get('api_errors', 0)} 个")
        
        # 显示结果摘要
        print(f"\n分析了 {results['analyzed_count']}/{results['total_count']} 种蔬菜")
        print(f"BTC风险级别: {results.get('btc_risk_level_zh', '未知')} (得分: {results.get('btc_risk_score', 0)})")
        
        # 显示市场评述
        if 'market_comment' in results and results['market_comment']:
            print(f"\n市场评述: {results['market_comment']}")
            
            # 显示主要积极和消极因素
            if 'positive_factors' in results and results['positive_factors']:
                pos_factors = results['positive_factors'][:3] if len(results['positive_factors']) > 3 else results['positive_factors']
                print(f"积极因素: {', '.join(pos_factors)}")
                
            if 'negative_factors' in results and results['negative_factors']:
                neg_factors = results['negative_factors'][:3] if len(results['negative_factors']) > 3 else results['negative_factors']
                print(f"消极因素: {', '.join(neg_factors)}")
        
        print(f"发现 {results['recommendations_count']} 个推荐")
        print(f"  - 长线推荐: {results.get('long_term_count', 0)} 种")
        if short_term_analysis:
            print(f"  - 短线推荐: {results.get('short_term_count', 0)} 种")
        
        # 显示推荐详情
        recommendations = results.get('recommendations', [])
        if recommendations:
            print("\n推荐蔬菜列表:")
            print("排名   类型    蔬菜      名称                   价格        受欢迎度/亿     24h价格变化    7d价格变化    新鲜度     评分")
            print("-"*120)
            
            # 只显示前10个
            for i, rec in enumerate(recommendations[:10]):
                # 确定分析类型
                analysis_type = "短线" if rec.get('is_short_term', False) else "长线"
                symbol = rec.get('symbol', '')
                name = rec.get('name', '')[:20]  # 限制名称长度
                price = rec.get('price', 0)
                market_cap = rec.get('market_cap', 0) / 1e8  # 转换为亿
                change_24h = rec.get('price_change_24h', 0)
                change_7d = rec.get('price_change_7d', 0)
                rsi = rec.get('rsi', 0)
                score = rec.get('score', 0)
                
                print(f"{i+1:<5} {analysis_type:<6} {symbol:<8} {name:<20} {price:<10.6f} {market_cap:<12.2f} "
                      f"{change_24h:<12.2f}% {change_7d:<10.2f}% {rsi:<8.2f} {score:<6.1f}")
                
            # 显示详细原因(前3个)
            for i, rec in enumerate(recommendations[:3]):
                symbol = rec.get('symbol', '')
                reasons = rec.get('reason', [])
                analysis_type = "短线" if rec.get('is_short_term', False) else "长线"
                
                print(f"\n{symbol} ({analysis_type}) 推荐原因:")
                for reason in reasons:
                    print(f"- {reason}")
                    
                # 显示风险信息
                if 'btc_correlation' in rec:
                    corr = rec.get('btc_correlation', 0)
                    corr_level = "高" if abs(corr) > 0.7 else "中" if abs(corr) > 0.4 else "低"
                    corr_direction = "正" if corr > 0 else "负" if corr < 0 else "无"
                    print(f"- 与BTC相关性: {corr_level}{corr_direction}相关 ({corr:.2f})")
                    
                if 'btc_beta' in rec:
                    beta = rec.get('btc_beta', 0)
                    beta_desc = "高波动" if beta > 1.2 else "低波动" if beta < 0.8 else "中等波动"
                    print(f"- 相对BTC波动性: {beta_desc} (Beta: {beta:.2f})")
                
                # 显示趋势信息(如果有)
                if 'indicators' in rec and 'trend' in rec['indicators']:
                    trend = rec['indicators']['trend']
                    print(f"- 价格趋势: {trend}")
                    
                # 显示波动性(如果有)
                if 'indicators' in rec and 'volatility' in rec['indicators']:
                    volatility = rec['indicators']['volatility']
                    print(f"- 价格波动率: {volatility:.2f}%")
        
        return results

    def calculate_recommendation_score(self, coin_data):
        """计算推荐币种的综合评分，用于排序"""
        score = 0
        
        # 1. 根据技术指标评分
        rsi = coin_data.get('rsi', 50)
        # RSI: 接近30(超卖)得高分，接近70(超买)得低分
        if rsi <= 30:
            score += 20 * (1 - rsi/30)  # RSI越低分越高，最高20分
        elif rsi <= 50:
            score += 10 * (50 - rsi) / 20  # 30-50之间，分数递减，最高10分
            
        # 2. 根据市场趋势评分
        reason = coin_data.get('reason', '')
        if '强势上升' in reason:
            score += 15
        elif '上升趋势' in reason:
            score += 10
        elif '短期波动' in reason:
            score += 5
            
        # 3. 根据MACD信号评分
        if 'MACD金叉' in reason:
            score += 20
            
        # 4. 根据布林带情况评分
        if '价格低于布林带下轨' in reason:
            score += 15
            
        # 5. 价格动量评分
        price_change_24h = coin_data.get('price_change_24h', 0)
        price_change_7d = coin_data.get('price_change_7d', 0)
        
        # 短期动能转正给予加分
        if price_change_24h > 0 and price_change_7d < 0:
            score += 10  # 7天下跌但24小时转正，可能是触底反弹
        elif price_change_24h > 0 and price_change_7d > 0:
            score += 5   # 持续上涨
            
        # 6. 成交量/市值比率 (流动性指标)
        market_cap = coin_data.get('market_cap', 0)
        volume_24h = coin_data.get('volume_24h', 0)
        if market_cap > 0:
            liquidity_ratio = volume_24h / market_cap
            # 流动性比率通常在0-0.5之间，高流动性给予加分
            score += min(liquidity_ratio * 100, 15)  # 最高15分
            
        # 7. 市值评分 (大市值币种风险更低)
        # 根据市值范围分级
        if market_cap >= 50_000_000_000:  # 超大市值 (> 500亿)
            score += 5
        elif market_cap >= 10_000_000_000:  # 大市值 (> 100亿)
            score += 3
        elif market_cap >= 1_000_000_000:  # 中市值 (> 10亿)
            score += 1
            
        return score

    def analyze_btc_risk(self):
        """分析BTC的风险水平，用作基准风险参考"""
        logger.info("分析BTC风险水平...")
        
        try:
            # 1. 获取BTC的长期价格数据 (200天)
            btc_long_df = self.fetch_price_history('bitcoin', days=200)
            if btc_long_df is None or btc_long_df.empty:
                logger.error("无法获取BTC长期价格数据")
                return None
                
            # 2. 获取BTC的中期价格数据 (30天)
            btc_mid_df = self.fetch_price_history('bitcoin', days=30)
            
            # 3. 获取BTC的短期价格数据 (7天，小时级别)
            btc_short_df = self.fetch_price_history('bitcoin', days=7, interval='1h')
            if btc_short_df is None or btc_short_df.empty:
                logger.warning("无法获取BTC短期价格数据，仅使用长期数据分析")
                
            # 4. 获取BTC的多时间维度价格变化
            btc_changes = self.fetch_price_changes('bitcoin')
            
            # 5. 计算长期技术指标
            long_indicators = self.calculate_technical_indicators(btc_long_df)
            
            # 6. 计算中期技术指标
            mid_indicators = None
            if btc_mid_df is not None and not btc_mid_df.empty:
                mid_indicators = self.calculate_technical_indicators(btc_mid_df)
            
            # 7. 计算短期技术指标（如果有数据）
            short_indicators = None
            if btc_short_df is not None and not btc_short_df.empty:
                short_indicators = self.calculate_technical_indicators(btc_short_df, is_short_term=True)
            
            # 8. 计算BTC风险评分 (0-100，越高风险越大)
            risk_score = 50  # 默认中等风险
            risk_factors = []
            positive_factors = []
            negative_factors = []
            
            # 9. 分析市场趋势
            long_trend = self.analyze_market_trend(btc_long_df)
            mid_trend = None
            if btc_mid_df is not None and not btc_mid_df.empty:
                mid_trend = self.analyze_market_trend(btc_mid_df)
            short_trend = None
            if btc_short_df is not None and not btc_short_df.empty:
                short_trend = self.analyze_market_trend(btc_short_df)
            
            # 添加趋势分析
            trend_risk = 0
            if long_trend:
                if "下降" in long_trend:
                    trend_risk += 10
                    risk_factors.append(f"BTC长期趋势: {long_trend}")
                    negative_factors.append(f"长期{long_trend}")
                elif "上升" in long_trend:
                    trend_risk -= 10
                    positive_factors.append(f"长期{long_trend}")
            
            if mid_trend:
                if "下降" in mid_trend:
                    trend_risk += 5
                    risk_factors.append(f"BTC中期趋势: {mid_trend}")
                    negative_factors.append(f"中期{mid_trend}")
                elif "上升" in mid_trend:
                    trend_risk -= 5
                    positive_factors.append(f"中期{mid_trend}")
            
            if short_trend:
                if "下降" in short_trend:
                    trend_risk += 3
                    risk_factors.append(f"BTC短期趋势: {short_trend}")
                    negative_factors.append(f"短期{short_trend}")
                elif "上升" in short_trend:
                    trend_risk -= 3
                    positive_factors.append(f"短期{short_trend}")
            
            risk_score += trend_risk
            
            # 长期指标评估
            if long_indicators:
                # RSI评估
                rsi = long_indicators.get('rsi', 50)
                if rsi > 70:
                    risk_score += 15
                    risk_factors.append(f"BTC RSI超买 ({rsi:.1f})")
                    negative_factors.append(f"RSI超买 ({rsi:.1f})")
                elif rsi < 30:
                    risk_score -= 10
                    risk_factors.append(f"BTC RSI超卖 ({rsi:.1f})")
                    positive_factors.append(f"RSI超卖 ({rsi:.1f})")
                    
                # MACD评估
                macd = long_indicators.get('macd', 0)
                signal = long_indicators.get('signal', 0)
                if macd < signal and long_indicators.get('macd_crossunder', False):
                    risk_score += 10
                    risk_factors.append("BTC MACD死叉")
                    negative_factors.append("MACD死叉")
                elif macd > signal and long_indicators.get('macd_crossover', False):
                    risk_score -= 10
                    risk_factors.append("BTC MACD金叉")
                    positive_factors.append("MACD金叉")
                    
                # 布林带评估
                if long_indicators.get('price_above_ma20', False):
                    if long_indicators.get('bb_width', 0) > 0.05:  # 布林带扩张
                        risk_score += 5
                        risk_factors.append("BTC价格高波动")
                        negative_factors.append("价格高波动")
                
                # 均线评估
                if long_indicators.get('death_cross', False):
                    risk_score += 15
                    risk_factors.append("BTC 20/50均线死叉")
                    negative_factors.append("20/50均线死叉")
                elif long_indicators.get('golden_cross', False):
                    risk_score -= 15
                    risk_factors.append("BTC 20/50均线金叉")
                    positive_factors.append("20/50均线金叉")
                    
                # 价格与MA200关系
                if 'ma200' in long_indicators:
                    current_price = btc_long_df['close'].iloc[-1]
                    ma200 = long_indicators.get('ma200')
                    
                    if current_price > ma200 * 1.1:
                        risk_score += 10
                        risk_factors.append(f"BTC价格远高于200日均线 (+{((current_price/ma200)-1)*100:.1f}%)")
                        negative_factors.append(f"价格远高于200日均线 (+{((current_price/ma200)-1)*100:.1f}%)")
                    elif current_price > ma200:
                        risk_score -= 5
                        risk_factors.append("BTC价格处于200日均线上方")
                        positive_factors.append("价格处于200日均线上方")
                    elif current_price < ma200 * 0.9:
                        risk_score += 5
                        risk_factors.append(f"BTC价格远低于200日均线 (-{(1-(current_price/ma200))*100:.1f}%)")
                        negative_factors.append(f"价格远低于200日均线 (-{(1-(current_price/ma200))*100:.1f}%)")
                    else:
                        risk_factors.append("BTC价格处于200日均线下方")
                        negative_factors.append("价格处于200日均线下方")
            
            # 中期指标评估
            if mid_indicators:
                # 中期RSI
                mid_rsi = mid_indicators.get('rsi', 50)
                if mid_rsi > 70:
                    risk_score += 10
                    risk_factors.append(f"BTC中期RSI超买 ({mid_rsi:.1f})")
                    negative_factors.append(f"中期RSI超买 ({mid_rsi:.1f})")
                elif mid_rsi < 30:
                    risk_score -= 7
                    risk_factors.append(f"BTC中期RSI超卖 ({mid_rsi:.1f})")
                    positive_factors.append(f"中期RSI超卖 ({mid_rsi:.1f})")
                    
                # 随机指标
                stoch_k = mid_indicators.get('stoch_k', 50)
                stoch_d = mid_indicators.get('stoch_d', 50)
                
                if stoch_k > 80 and stoch_d > 80:
                    risk_score += 8
                    risk_factors.append(f"BTC中期随机指标超买 (K:{stoch_k:.1f}/D:{stoch_d:.1f})")
                    negative_factors.append(f"中期随机指标超买")
                elif stoch_k < 20 and stoch_d < 20:
                    risk_score -= 5
                    risk_factors.append(f"BTC中期随机指标超卖 (K:{stoch_k:.1f}/D:{stoch_d:.1f})")
                    positive_factors.append(f"中期随机指标超卖")
            
            # 短期指标评估
            if short_indicators:
                # 短期RSI评估
                short_rsi = short_indicators.get('rsi', 50)
                if short_rsi > 80:
                    risk_score += 10
                    risk_factors.append(f"BTC短期RSI极度超买 ({short_rsi:.1f})")
                    negative_factors.append(f"短期RSI极度超买 ({short_rsi:.1f})")
                elif short_rsi < 20:
                    risk_score -= 5
                    risk_factors.append(f"BTC短期RSI极度超卖 ({short_rsi:.1f})")
                    positive_factors.append(f"短期RSI极度超卖 ({short_rsi:.1f})")
                    
                # 短期成交量评估
                if 'volume_change' in short_indicators:
                    volume_change = short_indicators.get('volume_change', 0)
                    if volume_change > 2.0:  # 成交量暴增
                        risk_score += 10
                        risk_factors.append(f"BTC短期成交量暴增 ({volume_change:.1f}x)")
                        negative_factors.append(f"短期成交量暴增 ({volume_change:.1f}x)")
                        
                # 短期波动性
                if 'bb_width' in short_indicators:
                    bb_width = short_indicators.get('bb_width', 0)
                    if bb_width > 0.1:  # 高波动
                        risk_score += 8
                        risk_factors.append(f"BTC短期高波动 (布林带宽度: {bb_width:.3f})")
                        negative_factors.append(f"短期高波动")
            
            # 价格变化评估
            if btc_changes:
                # 短期价格变化
                price_change_24h = btc_changes.get('24h', 0)
                if price_change_24h > 10:
                    risk_score += 10
                    risk_factors.append(f"BTC 24h价格大幅上涨 (+{price_change_24h:.1f}%)")
                    negative_factors.append(f"24h价格大幅上涨 (+{price_change_24h:.1f}%)")
                elif price_change_24h < -10:
                    risk_score += 15
                    risk_factors.append(f"BTC 24h价格大幅下跌 ({price_change_24h:.1f}%)")
                    negative_factors.append(f"24h价格大幅下跌 ({price_change_24h:.1f}%)")
                    
                # 中期价格变化
                price_change_7d = btc_changes.get('7d', 0)
                if price_change_7d > 20:
                    risk_score += 12
                    risk_factors.append(f"BTC 7天过快上涨 (+{price_change_7d:.1f}%)")
                    negative_factors.append(f"7天过快上涨 (+{price_change_7d:.1f}%)")
                elif price_change_7d < -20:
                    risk_score += 15
                    risk_factors.append(f"BTC 7天大幅下跌 ({price_change_7d:.1f}%)")
                    negative_factors.append(f"7天大幅下跌 ({price_change_7d:.1f}%)")
                    
                # 长期价格趋势
                price_change_30d = btc_changes.get('30d', 0)
                if price_change_30d < -20:
                    risk_score += 15
                    risk_factors.append(f"BTC 30天大幅下跌 ({price_change_30d:.1f}%)")
                    negative_factors.append(f"30天大幅下跌 ({price_change_30d:.1f}%)")
                elif price_change_30d > 50:
                    risk_score += 10
                    risk_factors.append(f"BTC 30天过快上涨 (+{price_change_30d:.1f}%)")
                    negative_factors.append(f"30天过快上涨 (+{price_change_30d:.1f}%)")
                    
                # 超长期变化
                price_change_200d = btc_changes.get('200d', 0)
                if price_change_200d:
                    if price_change_200d > 100:
                        risk_score += 10
                        risk_factors.append(f"BTC 200天涨幅过高 (+{price_change_200d:.1f}%)")
                        negative_factors.append(f"200天涨幅过高 (+{price_change_200d:.1f}%)")
                    elif price_change_200d < -50:
                        risk_score -= 5
                        risk_factors.append(f"BTC 200天大幅下跌 ({price_change_200d:.1f}%)")
                        positive_factors.append(f"200天大幅下跌 ({price_change_200d:.1f}%)")
            
            # 检测反转模式
            try:
                # 短期价格反转检测
                if btc_short_df is not None and len(btc_short_df) > 24:
                    last_12h = btc_short_df.iloc[-12:]['close'].values
                    prev_12h = btc_short_df.iloc[-24:-12]['close'].values
                    
                    last_change = (last_12h[-1] - last_12h[0]) / last_12h[0] * 100
                    prev_change = (prev_12h[-1] - prev_12h[0]) / prev_12h[0] * 100
                    
                    # 前12小时上涨，后12小时下跌
                    if prev_change > 5 and last_change < -3:
                        risk_score += 10
                        risk_factors.append(f"BTC短期反转信号: 涨势转跌 (前:{prev_change:.1f}% → 后:{last_change:.1f}%)")
                        negative_factors.append(f"短期涨势转跌")
                    # 前12小时下跌，后12小时上涨
                    elif prev_change < -5 and last_change > 3:
                        risk_score -= 10
                        risk_factors.append(f"BTC短期反转信号: 跌势转涨 (前:{prev_change:.1f}% → 后:{last_change:.1f}%)")
                        positive_factors.append(f"短期跌势转涨")
                except Exception as e:
                logger.error(f"检测价格反转模式时出错: {e}")
            
            # 限制风险分数范围在0-100之间
            risk_score = max(0, min(100, risk_score))
            
            # 风险级别划分（使用英文值）
            risk_level = "medium"
            risk_level_zh = "中等"
            if risk_score >= 75:
                risk_level = "very_high"
                risk_level_zh = "极高"
            elif risk_score >= 60:
                risk_level = "high"
                risk_level_zh = "高"
            elif risk_score <= 25:
                risk_level = "very_low"
                risk_level_zh = "极低"
            elif risk_score <= 40:
                risk_level = "low"
                risk_level_zh = "低"
                
            # 生成市场评述
            market_comment = self._generate_market_comment(risk_level_zh, positive_factors, negative_factors)
                
            # 返回风险分析结果
            risk_analysis = {
                'score': risk_score,
                'level': risk_level,
                'level_zh': risk_level_zh,
                'factors': risk_factors,
                'positive_factors': positive_factors,
                'negative_factors': negative_factors,
                'market_comment': market_comment,
                'long_indicators': long_indicators,
                'mid_indicators': mid_indicators,
                'short_indicators': short_indicators,
                'price_changes': btc_changes,
                'trends': {
                    'long': long_trend,
                    'mid': mid_trend,
                    'short': short_trend
                }
            }
            
            logger.info(f"BTC风险分析完成: 风险等级 {risk_level_zh} (得分: {risk_score}/100)")
            for factor in risk_factors:
                logger.info(f"- {factor}")
                
            return risk_analysis
            
    except Exception as e:
            logger.error(f"BTC风险分析出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def analyze_market_trend(self, price_df):
        """分析市场趋势
        
        参数:
        price_df -- 价格数据DataFrame
        
        返回:
        趋势描述字符串
        """
        try:
            if price_df is None or len(price_df) == 0:
                return "数据不足"
                
            # 确保数据类型正确
            if 'close' in price_df.columns:
                price_df['close'] = price_df['close'].astype(float)
            else:
                return "数据缺失"
                
            # 计算简单移动平均线
            if len(price_df) >= 20:
                price_df['ma20'] = price_df['close'].rolling(window=20).mean()
            if len(price_df) >= 50:
                price_df['ma50'] = price_df['close'].rolling(window=50).mean()
                
            # 计算最近的价格变化
            if len(price_df) >= 10:
                recent_change = (float(price_df['close'].iloc[-1]) / float(price_df['close'].iloc[-10]) - 1) * 100
            else:
                recent_change = 0
                
            # 计算波动性 - 修复Series转float的问题
            if len(price_df) >= 20:
                # 先计算标准差Series，然后取最后一个值并转换为float
                volatility = price_df['close'].pct_change().rolling(window=20).std().iloc[-1] * 100
            else:
                # 同样，先计算标准差Series，然后取最后一个值并转换为float
                volatility = price_df['close'].pct_change().std().iloc[-1] * 100
                
            # 分析趋势
            trend = "横盘整理"  # 默认趋势
            
            # 基于最近价格变化判断短期趋势
            if recent_change > 10:
                trend = "强势上升"
            elif recent_change > 5:
                trend = "上升趋势"
            elif recent_change < -10:
                trend = "强势下降"
            elif recent_change < -5:
                trend = "下降趋势"
                
            # 基于均线关系调整趋势判断
            if 'ma20' in price_df.columns and 'ma50' in price_df.columns and len(price_df) >= 2:
                # 安全地提取数值，避免Series比较
                last_ma20 = float(price_df['ma20'].iloc[-1])
                prev_ma20 = float(price_df['ma20'].iloc[-2])
                last_ma50 = float(price_df['ma50'].iloc[-1])
                prev_ma50 = float(price_df['ma50'].iloc[-2])
                
                # 当前价格
                current_price = float(price_df['close'].iloc[-1])
                
                # 黄金交叉(短期均线上穿长期均线)
                if (last_ma20 > last_ma50) and (prev_ma20 <= prev_ma50):
                    trend = "上升趋势"
                    
                # 死亡交叉(短期均线下穿长期均线)
                if (last_ma20 < last_ma50) and (prev_ma20 >= prev_ma50):
                    trend = "下降趋势"
                    
                # 强势多头排列
                if (current_price > last_ma20) and (last_ma20 > last_ma50) and (recent_change > 0):
                    trend = "上升趋势"
                    if (recent_change > 5) and (volatility < 5):  # 稳健上升，低波动
                        trend = "强势上升"
                        
                # 强势空头排列
                if (current_price < last_ma20) and (last_ma20 < last_ma50) and (recent_change < 0):
                    trend = "下降趋势"
                    if (recent_change < -5) and (volatility < 5):  # 稳健下降，低波动
                        trend = "强势下降"
                        
            # 高波动性可能表示趋势不稳定
            if volatility > 10:
                if "强势" in trend:
                    trend = trend.replace("强势", "")  # 高波动不宜判断为强势
                trend += "(高波动)"
                
            return trend
            
        except Exception as e:
            logger.error(f"分析市场趋势时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "分析失败"
            
    def calculate_correlation_with_btc(self, coin_id):
        """计算与BTC的相关性和Beta值
        
        参数:
        coin_id -- 币种ID
        
        返回:
        包含相关性和Beta的字典
        """
        try:
            # 获取BTC的30天价格数据
            btc_df = self.fetch_price_history('bitcoin', days=30)
            if btc_df is None or btc_df.empty:
                logger.warning(f"无法获取BTC价格数据，无法计算相关性")
                return None
                
            # 获取目标币种的30天价格数据
            coin_df = self.fetch_price_history(coin_id, days=30)
            if coin_df is None or coin_df.empty:
                logger.warning(f"无法获取 {coin_id} 价格数据，无法计算相关性")
                return None
                
            # 确保数据长度一致并且有足够的数据点
            if len(btc_df) < 10 or len(coin_df) < 10:
                logger.warning(f"数据点不足，无法计算相关性")
                return None
                
            # 计算日收益率
            btc_returns = btc_df['close'].pct_change().dropna()
            coin_returns = coin_df['close'].pct_change().dropna()
            
            # 确保索引一致，以便正确对齐
            common_idx = btc_returns.index.intersection(coin_returns.index)
            if len(common_idx) < 10:
                logger.warning(f"共同的数据点不足，无法计算相关性")
                return None
                
            # 使用共同索引重新对齐数据
            btc_returns = btc_returns[common_idx]
            coin_returns = coin_returns[common_idx]
            
            # 计算皮尔逊相关系数
            correlation = btc_returns.corr(coin_returns)
            
            # 计算Beta系数 (衡量相对于BTC的波动性)
            # Beta = Cov(coin, BTC) / Var(BTC)
            covariance = btc_returns.cov(coin_returns)
            variance = btc_returns.var()
            
            if variance != 0:
                beta = covariance / variance
            else:
                beta = 0
            
            return {
                'returns_correlation': correlation,
                'beta': beta,
                'common_data_points': len(common_idx)
            }
            
        except Exception as e:
            logger.error(f"计算与BTC相关性时出错: {e}")
            return None

    def _generate_market_comment(self, risk_level_zh, positive_factors, negative_factors):
        """生成市场评述
        
        参数:
        risk_level_zh -- 风险级别中文描述
        positive_factors -- 积极因素列表
        negative_factors -- 消极因素列表
        
        返回:
        市场评述文本
        """
        try:
            # 根据风险级别生成基础评述
            if risk_level_zh == "极低":
                base_comment = "当前BTC风险极低，市场处于非常有利的买入时机。"
            elif risk_level_zh == "低":
                base_comment = "当前BTC风险较低，市场总体趋势向好，适合选择性买入。"
            elif risk_level_zh == "中等":
                base_comment = "当前BTC风险中等，市场处于盘整阶段，建议谨慎操作。"
            elif risk_level_zh == "高":
                base_comment = "当前BTC风险较高，市场可能面临调整，建议减少仓位或持币观望。"
            elif risk_level_zh == "极高":
                base_comment = "当前BTC风险极高，市场可能大幅下跌，建议暂停买入并考虑减仓。"
            else:
                base_comment = "当前BTC风险评估不明确，建议谨慎操作。"
                
            # 添加积极因素
            positive_text = ""
            if positive_factors:
                if len(positive_factors) > 3:
                    selected_factors = positive_factors[:3]
                else:
                    selected_factors = positive_factors
                    
                positive_text = f"积极信号包括: {', '.join(selected_factors)}"
                
            # 添加消极因素
            negative_text = ""
            if negative_factors:
                if len(negative_factors) > 3:
                    selected_factors = negative_factors[:3]
                else:
                    selected_factors = negative_factors
                    
                negative_text = f"需注意的风险信号: {', '.join(selected_factors)}"
                
            # 组合完整评述
            full_comment = base_comment
            
            if positive_text:
                full_comment += " " + positive_text
                
            if negative_text:
                full_comment += " " + negative_text
                
            # 添加建议
            if risk_level_zh in ["极低", "低"]:
                full_comment += " 推荐采取适度买入策略，关注强势上涨品种。"
            elif risk_level_zh == "中等":
                full_comment += " 建议均衡配置，同时保留部分现金等待更好的买入机会。"
            else:
                full_comment += " 建议以防御策略为主，降低投资仓位，增加稳定性资产配置。"
                
            return full_comment
            
        except Exception as e:
            logger.error(f"生成市场评述时出错: {e}")
            return f"当前BTC风险级别: {risk_level_zh}，建议根据自身风险承受能力进行投资决策。"

    def determine_buy_action(self, coin, indicators, market_trend):
        """确定是否推荐购买
        
        参数:
        coin -- 币种数据
        indicators -- 技术指标
        market_trend -- 市场趋势描述
        
        返回:
        (买入决定, 推荐对象)
        """
        try:
            symbol = coin.get('symbol', '').upper()
            name = coin.get('name', '')
            price = coin.get('current_price', coin.get('price', 0))
            market_cap = coin.get('market_cap', 0)
            volume_24h = coin.get('total_volume', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            price_change_7d = coin.get('price_change_percentage_7d', 0)
            price_change_30d = coin.get('price_change_percentage_30d', 0)
            
            # 创建推荐对象
            recommendation = {
                'symbol': symbol,
                'name': name,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'price_change_24h': price_change_24h,
                'price_change_7d': price_change_7d,
                'price_change_30d': price_change_30d,
                'action': 'hold',  # 默认建议
                'reason': [],  # 推荐原因
                'score': 0,  # 推荐评分
                'rsi': indicators.get('rsi', 50) if indicators else 50
            }
            
            # 如果指标不存在，无法给出建议
            if not indicators:
                recommendation['reason'].append("技术指标数据不足")
                return False, recommendation
                
            # 计算推荐分数
            score = 0
            reason = []
            
            # 1. RSI指标分析
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                score += 20
                reason.append(f"RSI超卖 ({rsi:.1f})")
            elif rsi < 40:
                score += 10
                reason.append(f"RSI偏低 ({rsi:.1f})")
            elif rsi > 70:
                score -= 20
                reason.append(f"RSI超买 ({rsi:.1f})")
                
            # 2. MACD分析
            macd = indicators.get('macd', 0)
            signal = indicators.get('signal', 0)
            
            if indicators.get('macd_crossover', False) or (macd is not None and signal is not None and macd > signal and macd > 0):
                score += 15
                reason.append("MACD金叉")
            elif indicators.get('macd_crossunder', False) or (macd is not None and signal is not None and macd < signal and macd < 0):
                score -= 10
                reason.append("MACD死叉")
                
            # 3. 布林带分析
            if indicators.get('close_below_lower_bb', False) or (
                    'bb_lower' in indicators and price < indicators['bb_lower']):
                score += 15
                reason.append("价格低于布林带下轨")
            elif indicators.get('close_above_upper_bb', False) or (
                    'bb_upper' in indicators and price > indicators['bb_upper']):
                score -= 15
                reason.append("价格高于布林带上轨")
            
            # 4. 市场趋势分析
            if market_trend:
                if "强势上升" in market_trend:
                    score += 20
                    reason.append(f"市场走势: {market_trend}")
                elif "上升" in market_trend:
                    score += 10
                    reason.append(f"市场走势: {market_trend}")
                elif "强势下降" in market_trend:
                    score -= 20
                    reason.append(f"市场走势: {market_trend}")
                elif "下降" in market_trend:
                    score -= 10
                    reason.append(f"市场走势: {market_trend}")
                    
            # 5. 移动平均线分析
            if indicators.get('price_above_ma50', False) and indicators.get('ma5_ma10_ma20_aligned_up', False):
                score += 15
                reason.append("均线多头排列")
            elif indicators.get('price_below_ma50', False) and indicators.get('ma5_ma10_ma20_aligned_down', False):
                score -= 15
                reason.append("均线空头排列")
                
            # 6. 价格动量分析
            if price_change_24h > 5 and price_change_7d < 0:
                score += 10
                reason.append(f"可能反转信号: 24h ({price_change_24h:.1f}%) / 7d ({price_change_7d:.1f}%)")
            elif price_change_24h < -5 and price_change_7d > 5:
                score -= 10
                reason.append(f"可能回调信号: 24h ({price_change_24h:.1f}%) / 7d ({price_change_7d:.1f}%)")
                
            # 7. 趋势突破信号
            if indicators.get('ma5_crossover_ma10', False):
                score += 5
                reason.append("短期突破: MA5穿越MA10")
            elif indicators.get('ma10_crossover_ma20', False):
                score += 10
                reason.append("中期突破: MA10穿越MA20")
                
            # 8. 超买超卖指标综合评估
            stoch_k = indicators.get('stoch_k', 50)
            stoch_d = indicators.get('stoch_d', 50)
            if stoch_k < 20 and stoch_d < 20 and rsi < 40:
                score += 15
                reason.append(f"多重超卖信号: K线 ({stoch_k:.1f}) D线 ({stoch_d:.1f}) RSI ({rsi:.1f})")
            elif stoch_k > 80 and stoch_d > 80 and rsi > 60:
                score -= 15
                reason.append(f"多重超买信号: K线 ({stoch_k:.1f}) D线 ({stoch_d:.1f}) RSI ({rsi:.1f})")
                
            # 9. 波动性评估
            volatility = indicators.get('volatility', 5)
            if volatility > 10:
                score -= 5
                reason.append(f"高波动性 ({volatility:.1f}%)")
            elif volatility < 3 and price_change_7d > 0:
                score += 5
                reason.append(f"低波动稳定上涨 ({volatility:.1f}%)")
                
            # 10. 成交量分析
            volume_change = indicators.get('volume_change', 0)
            if volume_change and volume_change > 2.0 and price_change_24h > 3:
                score += 10
                reason.append(f"成交量大增 ({volume_change:.1f}倍) 伴随价格上涨")
                
            # 计算最终评分(0-100)
            final_score = max(0, min(100, 50 + score))
            
            # 更新推荐对象
            recommendation['score'] = final_score
            recommendation['reason'] = reason
            
            # 根据评分决定推荐类型
            if final_score >= 70:
                recommendation['action'] = 'buy'
                return True, recommendation
            else:
                recommendation['action'] = 'hold'
                return False, recommendation
                
    except Exception as e:
            logger.error(f"决定买入行动时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, {'action': 'hold', 'reason': ["分析出错"], 'score': 0}
            
    def determine_short_term_buy_action(self, coin, indicators, market_trend):
        """确定短线交易推荐
        
        参数:
        coin -- 币种数据
        indicators -- 短期技术指标
        market_trend -- 短期市场趋势描述
        
        返回:
        (买入决定, 推荐对象)
        """
        try:
            symbol = coin.get('symbol', '').upper()
            name = coin.get('name', '')
            price = coin.get('current_price', coin.get('price', 0))
            market_cap = coin.get('market_cap', 0)
            volume_24h = coin.get('total_volume', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            price_change_7d = coin.get('price_change_percentage_7d', 0)
            
            # 创建推荐对象
            recommendation = {
                'symbol': symbol,
                'name': name,
                'price': price,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'price_change_24h': price_change_24h,
                'price_change_7d': price_change_7d,
                'action': 'hold',  # 默认建议
                'reason': [],  # 推荐原因
                'score': 0,  # 推荐评分
                'rsi': indicators.get('rsi', 50) if indicators else 50
            }
            
            # 如果指标不存在，无法给出建议
            if not indicators:
                recommendation['reason'].append("短期技术指标数据不足")
                return False, recommendation
                
            # 计算推荐分数 (短线交易更注重快速波动和超买超卖)
            score = 0
            reason = []
            
            # 1. RSI指标分析 (短线更敏感的阈值)
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                score += 25
                reason.append(f"短期RSI超卖 ({rsi:.1f})")
            elif rsi < 40:
                score += 15
                reason.append(f"短期RSI偏低 ({rsi:.1f})")
            elif rsi > 75:
                score -= 25
                reason.append(f"短期RSI超买 ({rsi:.1f})")
            elif rsi > 65:
                score -= 15
                reason.append(f"短期RSI偏高 ({rsi:.1f})")
                
            # 2. MACD分析
            if indicators.get('macd_crossover', False):
                score += 20
                reason.append("短期MACD金叉")
            elif indicators.get('macd_crossunder', False):
                score -= 15
                reason.append("短期MACD死叉")
                
            # 3. 布林带分析
            if indicators.get('close_below_lower_bb', False) or (
                    'bb_lower' in indicators and 'bb_pct' in indicators and indicators['bb_pct'] < 0.05):
                score += 20
                reason.append("价格接近布林带下轨")
            elif indicators.get('close_above_upper_bb', False) or (
                    'bb_upper' in indicators and 'bb_pct' in indicators and indicators['bb_pct'] > 0.95):
                score -= 20
                reason.append("价格接近布林带上轨")
                
            # 4. 短期市场趋势分析
            if market_trend:
                if "强势上升" in market_trend:
                    score += 15
                    reason.append(f"短期走势: {market_trend}")
                elif "上升" in market_trend:
                    score += 10
                    reason.append(f"短期走势: {market_trend}")
                    
            # 5. 随机指标分析 (短线交易常用)
            stoch_k = indicators.get('stoch_k', 50)
            stoch_d = indicators.get('stoch_d', 50)
            if stoch_k < 20 and stoch_d < 20:
                score += 20
                reason.append(f"随机指标超卖: K线 ({stoch_k:.1f}) D线 ({stoch_d:.1f})")
            elif stoch_k > 80 and stoch_d > 80:
                score -= 20
                reason.append(f"随机指标超买: K线 ({stoch_k:.1f}) D线 ({stoch_d:.1f})")
                
            # 6. K线与D线交叉
            if indicators.get('stoch_k_crossover_stoch_d', False) or (
                    stoch_k > stoch_d and indicators.get('stoch_k', 0) < 30):
                score += 15
                reason.append("K线自下而上穿越D线")
                
            # 7. 短期动量分析
            roc_1 = indicators.get('roc_1', 0)
            if roc_1 > 3:
                score += 15
                reason.append(f"强势短期动量 (+{roc_1:.1f}%)")
            elif roc_1 < -3:
                score -= 10
                reason.append(f"弱势短期动量 ({roc_1:.1f}%)")
                
            # 8. 成交量分析 (短线更注重)
            volume_change = indicators.get('volume_change', 0)
            if volume_change and volume_change > 1.5:
                score += 15
                reason.append(f"短期成交量放大 ({volume_change:.1f}倍)")
                
            # 9. 乖离率分析
            bias5 = indicators.get('bias5', 0)
            if bias5 < -5:
                score += 10
                reason.append(f"价格远低于5日均线 ({bias5:.1f}%)")
            elif bias5 > 7:
                score -= 10
                reason.append(f"价格远高于5日均线 ({bias5:.1f}%)")
                
            # 10. 威廉指标分析
            williams_r = indicators.get('williams_r', -50)
            if williams_r < -80:
                score += 15
                reason.append(f"威廉指标超卖 ({williams_r:.1f})")
            elif williams_r > -20:
                score -= 15
                reason.append(f"威廉指标超买 ({williams_r:.1f})")
                
            # 计算最终评分(0-100)
            final_score = max(0, min(100, 50 + score))
            
            # 更新推荐对象
            recommendation['score'] = final_score
            recommendation['reason'] = reason
            
            # 短线交易需要更高的确信度
            if final_score >= 75:
                recommendation['action'] = 'buy'
                return True, recommendation
            else:
                recommendation['action'] = 'hold'
                return False, recommendation
                
        except Exception as e:
            logger.error(f"决定短线买入行动时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, {'action': 'hold', 'reason': ["短线分析出错"], 'score': 0}

    def save_results_with_timestamp(self, recommendations, timestamp=None):
        """保存推荐结果并添加时间戳
        
        参数:
        recommendations -- 推荐结果列表
        timestamp -- 时间戳，如果为None则使用当前时间
        
        返回:
        保存的文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # 确保目录存在
        os.makedirs("crypto_data", exist_ok=True)
        
        # 保存为JSON
        json_file = f"crypto_data/recommendations_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        logger.info(f"推荐结果已保存至 {json_file}")
        
        # 保存为CSV
        csv_file = f"crypto_data/recommendations_{timestamp}.csv"
        try:
            # 提取需要的字段
            csv_data = []
            for rec in recommendations:
                row = {
                    'symbol': rec.get('symbol', ''),
                    'name': rec.get('name', ''),
                    'price': rec.get('price', 0),
                    'market_cap': rec.get('market_cap', 0),
                    'volume_24h': rec.get('volume_24h', 0),
                    'price_change_24h': rec.get('price_change_24h', 0),
                    'price_change_7d': rec.get('price_change_7d', 0),
                    'price_change_30d': rec.get('price_change_30d', 0),
                    'action': rec.get('action', 'hold'),
                    'score': rec.get('score', 0),
                    'reason': ' | '.join(rec.get('reason', [])),
                    'rsi': rec.get('rsi', 0)
                }
                csv_data.append(row)
                
            # 写入CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(csv_file, index=False, encoding='utf-8')
                logger.info(f"推荐结果已保存至 {csv_file}")
            else:
                logger.warning("没有推荐结果可保存")
                
    except Exception as e:
            logger.error(f"保存CSV文件时出错: {e}")
            
        # 同时更新最新的推荐结果
        latest_csv = "crypto_data/recommendations.csv"
        try:
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(latest_csv, index=False, encoding='utf-8')
                logger.info(f"最新推荐结果已更新至 {latest_csv}")
        except Exception as e:
            logger.error(f"更新最新推荐结果时出错: {e}")
            
        return json_file

def main():
    try:
        # 设置命令行参数解析
        parser = argparse.ArgumentParser(description='菜价分析工具')
        parser.add_argument('--cache-only', action='store_true', help='仅使用缓存数据，不发送API请求')
        parser.add_argument('--limit', '--coins', type=int, default=None, help='限制分析的蔬菜数量，使用最受欢迎的前N种蔬菜')
        parser.add_argument('--sort-by', type=str, default='score', 
                            choices=['score', 'market_cap', 'price_change_24h', 'price_change_7d', 'rsi', 'volume_24h'], 
                            help='推荐结果排序方式: score(综合评分), market_cap(受欢迎度), price_change_24h(24h价格变化), price_change_7d(7d价格变化), rsi, volume_24h(交易量)')
        parser.add_argument('--no-save', action='store_true', help='不保存时间戳结果文件')
        parser.add_argument('--save-raw', '--save-all', action='store_true', help='保存所有获取的原始蔬菜数据')
        parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，减少输出信息')
        parser.add_argument('--email', type=str, help='发送结果到指定邮箱地址')
        parser.add_argument('--qq-email', type=str, help='发送结果到指定QQ邮箱地址(简化流程)')
        parser.add_argument('--no-obfuscation', action='store_true', help='不使用术语混淆，直接使用加密货币术语')
        parser.add_argument('--use-proxies', action='store_true', help='启用代理IP池，避免API请求限制')
        parser.add_argument('--add-proxy', type=str, help='添加代理到代理池，格式为http://ip:port或socks5://username:password@host:port')
        parser.add_argument('--add-proxies-from-url', type=str, help='从URL添加代理到代理池')
        parser.add_argument('--add-socks5-proxy', type=str, metavar='HOST:PORT', help='添加SOCKS5代理，格式为host:port')
        parser.add_argument('--socks5-username', type=str, help='SOCKS5代理用户名')
        parser.add_argument('--socks5-password', type=str, help='SOCKS5代理密码')
        parser.add_argument('--list-proxies', action='store_true', help='列出当前代理池中的所有代理')
        parser.add_argument('--no-short-term', action='store_true', help='不进行短线分析，仅分析长线数据')
        
        # 性能优化相关 - 提供覆盖默认值的选项
        parser.add_argument('--workers', type=int, default=6, help='并行处理的工作线程数量 (默认: 6)')
        parser.add_argument('--cache-expiry', type=int, default=24, help='缓存有效期(小时) (默认: 24)')
        parser.add_argument('--no-clean-cache', action='store_true', help='不清理过期缓存文件')
        
        # 风险控制相关 - 提供覆盖默认值的选项
        parser.add_argument('--max-risk-level', type=str, default='medium', 
                        choices=['low', 'medium', 'high', 'very_high'], 
                        help='设置最大风险级别，高于此级别的币种不推荐 (默认: medium)')
        parser.add_argument('--risk-adjustment', type=float, default=0.8, 
                        help='风险调整系数 (0.5-2.0)，较低值会降低整体风险 (默认: 0.8)')
        
        # 分析能力相关
        parser.add_argument('--trend-filter', type=str, 
                        choices=['uptrend', 'downtrend', 'sideways', 'strong_uptrend', 'strong_downtrend'], 
                        help='按趋势类型筛选推荐')
        parser.add_argument('--volatility-filter', type=float, default=None, 
                        help='波动率阈值 (%%，仅显示低于此波动率的币种)')
        parser.add_argument('--enhanced-analysis', action='store_true', 
                        help='启用增强分析，提供更详细的技术指标')
                        
        # 测试模式 - 直接加载现有的结果文件
        parser.add_argument('--test', action='store_true', help='测试模式：加载现有推荐文件而不是生成新数据')
        parser.add_argument('--test-file', type=str, default='crypto_data/recommendations_20250617_211357.json', 
                        help='测试模式下加载的推荐文件路径')
        
        args = parser.parse_args()
        
        # 处理代理管理相关命令
        if PROXY_SUPPORT:
            proxy_manager = ProxyManager()
            
            # 列出现有代理
            if args.list_proxies:
                proxies = proxy_manager.proxies
                print(f"当前代理池中共有 {len(proxies)} 个代理:")
                for i, proxy in enumerate(proxies):
                    print(f"[{i+1}] {proxy}")
                return
                
            # 添加SOCKS5代理（用于ip.proxys5.net格式）
            if args.add_socks5_proxy:
                host_port = args.add_socks5_proxy.split(':')
                
                if len(host_port) != 2:
                    print(f"无效的SOCKS5代理格式，正确格式: host:port")
                    return
                    
                host = host_port[0]
                try:
                    port = int(host_port[1])
                except ValueError:
                    print(f"无效的端口号: {host_port[1]}")
                    return
                    
                username = args.socks5_username or ""
                password = args.socks5_password or ""
                
                # 构建SOCKS5代理URL
                proxy_url = f"socks5://{username}:{password}@{host}:{port}"
                
                if proxy_manager.add_proxy(proxy_url):
                    print(f"成功添加SOCKS5代理: {host}:{port}")
                else:
                    print(f"无法添加SOCKS5代理: {host}:{port}")
            
            # 添加单个代理
            if args.add_proxy:
                if proxy_manager.add_proxy(args.add_proxy):
                    print(f"成功添加代理: {args.add_proxy}")
                else:
                    print(f"无法添加代理: {args.add_proxy}")
                    
            # 从URL添加代理
            if args.add_proxies_from_url:
                added = proxy_manager.add_proxies_from_url(args.add_proxies_from_url)
                print(f"从URL添加代理完成，成功添加 {added} 个代理")
                
            if args.add_proxy or args.add_proxies_from_url or args.add_socks5_proxy:
                print(f"当前代理池中共有 {len(proxy_manager.proxies)} 个代理")
            return
            
        # 设置日志级别
        if args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        
        # 测试模式：直接加载现有推荐文件
        if args.test:
            print(f"测试模式：加载现有推荐文件 {args.test_file}")
            try:
                import json
                with open(args.test_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # 处理文件可能是列表或字典的情况
                if isinstance(file_data, list):
                    recommendations = file_data
                    results = {
                        'recommendations': recommendations,
                        'recommendations_count': len(recommendations),
                        'analyzed_count': len(recommendations),
                        'total_count': len(recommendations),
                        'btc_risk_level': 'medium',
                        'btc_risk_level_zh': '中等',
                        'btc_risk_score': 50,
                        'long_term_count': len([r for r in recommendations if not r.get('is_short_term', False)]),
                        'short_term_count': len([r for r in recommendations if r.get('is_short_term', False)])
                    }
                    print(f"成功加载推荐文件，包含 {len(recommendations)} 个推荐项")
                else:
                    results = file_data
                    print(f"成功加载推荐文件，包含 {len(results.get('recommendations', []))} 个推荐项")
                
                # 修正风险级别中英文显示
                if 'btc_risk_level' in results:
                    level_map = {
                        '低': 'low',
                        '中等': 'medium',
                        '高': 'high',
                        '极高': 'very_high'
                    }
                    reverse_map = {v: k for k, v in level_map.items()}
                    
                    btc_risk_level = results.get('btc_risk_level')
                    # 如果是中文风险级别，增加level英文属性
                    if btc_risk_level in level_map:
                        results['btc_risk_level_zh'] = btc_risk_level
                        results['btc_risk_level'] = level_map[btc_risk_level]
                    # 如果是英文风险级别，增加level_zh中文属性
                    elif btc_risk_level in reverse_map:
                        results['btc_risk_level_zh'] = reverse_map[btc_risk_level]
                
                # 根据新参数进行额外过滤
                if 'recommendations' in results and results['recommendations']:
                    # 根据参数过滤推荐结果
                    apply_filtering(results, args)
                    
                # 显示结果
                print_results(results, include_short_term=not args.no_short_term)
                
            except Exception as e:
                print(f"加载推荐文件失败: {e}")
                import traceback
                print(traceback.format_exc())
            return
        
        print("开始运行菜价分析系统...\n")
        print("初始化...\n")
        
        # 输出默认优化配置
        print(f"系统默认配置:")
        print(f"- 并行处理: {args.workers} 个工作线程")
        print(f"- 缓存过期时间: {args.cache_expiry} 小时")
        print(f"- 自动清理缓存: {'已启用' if not args.no_clean_cache else '已禁用'}")
        print(f"- 最大风险级别: {args.max_risk_level} (风险调整系数: {args.risk_adjustment})")
        print()
        
        # 使用新的优化参数初始化
        recommender = CryptoRecommender(
            use_cache_only=args.cache_only, 
            use_proxies=args.use_proxies,
            max_workers=args.workers,
            cache_expiry_hours=args.cache_expiry
        )
        
        # 如果需要清理缓存 (默认开启，除非明确禁用)
        if not args.no_clean_cache:
            cleaned = recommender.clean_cache(max_age_days=7)
            print(f"缓存清理完成，删除了 {cleaned} 个旧文件")
        
        print("初始化完成，开始获取和分析数据...\n")
        
        # 执行分析
        results = recommender.simulate_daily_reminders(
            days=1, 
            limit=args.limit, 
            sort_by=args.sort_by,
            save_timestamp=not args.no_save,
            save_all_data=args.save_raw,
            short_term_analysis=not args.no_short_term
        )
        
        # 根据新参数进行额外过滤
        if results and 'recommendations' in results and results['recommendations']:
            apply_filtering(results, args)
        
        print("\n程序执行完成！")
        if results:
            print_results(results, include_short_term=not args.no_short_term)
            
    except Exception as e:
        logger.error(f"主程序执行错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
def apply_filtering(results, args):
    """根据参数过滤推荐结果"""
    # 获取推荐列表
    recommendations = results['recommendations']
    filtered_recommendations = recommendations.copy()
            
    # 根据最大风险级别过滤
    if args.max_risk_level:
        risk_levels = {'low': 0, 'medium': 1, 'high': 2, 'very_high': 3}
        max_risk_value = risk_levels.get(args.max_risk_level, 3)
        
        # 当BTC风险等级高于设定值时，显示风险警告
        btc_risk_level = results.get('btc_risk_level', 'medium')
        btc_risk_value = risk_levels.get(btc_risk_level, 1)
        
        if btc_risk_value > max_risk_value:
            print(f"\n⚠️ 风险警告: 当前BTC风险等级为 {results.get('btc_risk_level_zh', btc_risk_level)}，高于您设置的最大风险级别 {args.max_risk_level}")
            print(f"推荐减少投资额度或等待风险降低")
        
        # 过滤掉高风险币种
        filtered_recommendations = [rec for rec in filtered_recommendations if risk_levels.get(rec.get('btc_risk_level', 'medium'), 1) <= max_risk_value]
    
    # 根据趋势类型过滤
    if args.trend_filter:
        # 映射英文趋势代码到中文显示
        trend_map = {
            'strong_uptrend': '强势上升',
            'uptrend': '上升趋势',
            'sideways': '横盘整理',
            'downtrend': '下降趋势',
            'strong_downtrend': '强势下降'
        }
        requested_trend = args.trend_filter
        requested_trend_zh = trend_map.get(requested_trend, requested_trend)
        
        # 对于旧格式的数据，可能需要从reason中提取趋势信息
        trend_filtered = []
        for rec in filtered_recommendations:
            # 尝试从indicators中获取趋势
            has_trend = False
            if 'indicators' in rec:
                indicators_trend = rec['indicators'].get('trend', '')
                indicators_trend_en = rec['indicators'].get('trend_en', '')
                if indicators_trend == requested_trend_zh or indicators_trend_en == requested_trend:
                    trend_filtered.append(rec)
                    has_trend = True
            
            # 如果indicators中没有趋势信息，尝试从reason中获取
            if not has_trend and 'reason' in rec:
                for reason in rec['reason']:
                    if '市场走势' in reason and requested_trend_zh in reason:
                        trend_filtered.append(rec)
                        break
        
        filtered_recommendations = trend_filtered
    
    # 根据波动率过滤
    if args.volatility_filter is not None:
        filtered_recommendations = [rec for rec in filtered_recommendations 
                                 if 'indicators' in rec and rec['indicators'].get('volatility', 100) <= args.volatility_filter]
    
    # 显示过滤结果
    if len(filtered_recommendations) < len(recommendations):
        print(f"\n应用筛选条件后: 从 {len(recommendations)} 个推荐中筛选出 {len(filtered_recommendations)} 个符合条件的币种")
            
        # 更新结果中的推荐列表
        results['recommendations'] = filtered_recommendations
        results['recommendations_count'] = len(filtered_recommendations)

def print_results(results, include_short_term=True):
    """打印结果摘要"""
    print(f"\n===== 分析结果摘要 =====")
    print(f"分析币种: {results['analyzed_count']}/{results['total_count']} 种")
    print(f"BTC风险: {results.get('btc_risk_level_zh', '未知')} ({results.get('btc_risk_score', 0)}分)")
    
    # 显示推荐数量
    recommendations = results.get('recommendations', [])
    print(f"推荐数量: {len(recommendations)} 个")
    if 'long_term_count' in results:
        print(f"- 长线: {results['long_term_count']} 个")
    if include_short_term and 'short_term_count' in results:
        print(f"- 短线: {results['short_term_count']} 个")
        
    # 显示缓存统计
    if 'cache_stats' in results:
        cache_stats = results['cache_stats']
        print(f"\n缓存命中率: {cache_stats.get('hit_rate', 0)*100:.1f}%")
        print(f"API请求: {cache_stats.get('api_requests', 0)}次, 错误: {cache_stats.get('api_errors', 0)}次")
        
    # 显示推荐详情
    if recommendations:
        print("\n===== 推荐币种 =====")
        # 只显示前5个
        for i, rec in enumerate(recommendations[:5]):
            symbol = rec.get('symbol', '').upper()
            price = rec.get('price', 0)
            price_change_24h = rec.get('price_change_24h', 0)
            price_change_7d = rec.get('price_change_7d', 0)
            score = rec.get('score', 0)
            
            # 确定分析类型
            analysis_type = "短线" if rec.get('is_short_term', False) else "长线"
            
            print(f"{i+1}. {symbol} ({analysis_type}) | 价格: ${price:.6f} | 24h: {price_change_24h:.1f}% | 7d: {price_change_7d:.1f}% | 评分: {score:.1f}")
            
    print("\n爬取状态: " + ("成功" if len(recommendations) > 0 else "失败"))
    if 'processing_time' in results:
        print(f"处理时间: {results['processing_time']:.1f}秒")

if __name__ == "__main__":
    main() 