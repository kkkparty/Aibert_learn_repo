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
    def __init__(self, use_cache_only=False, use_proxies=False):
        """初始化菜价分析系统"""
        # 确保缓存目录存在
        self.cache_dir = os.path.join('crypto_data', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.use_cache_only = use_cache_only
        self.portfolio = None
        self.use_proxies = use_proxies and PROXY_SUPPORT
        self.proxy_manager = None
        
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
        self.min_request_interval = 8.0  # 两次请求之间的最小间隔时间（秒）
        self.last_request_time = 0
        
        if self.use_cache_only:
            logger.info("仅使用缓存模式已启用，将不会发送任何API请求")
    
    def _get_cache_path(self, endpoint, params):
        """生成缓存文件路径"""
        # 将参数排序后转为字符串，确保相同参数但不同顺序的请求得到相同的缓存文件
        sorted_params = sorted(params.items())
        param_str = '_'.join(f"{k}={v}" for k, v in sorted_params)
        cache_filename = f"{endpoint.replace('/', '_')}_{param_str}.json"
        return os.path.join(self.cache_dir, cache_filename)
    
    def _is_cache_valid(self, cache_path, max_age_hours=24):
        """检查缓存是否有效"""
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
        if self._is_cache_valid(cache_path):
            logger.info(f"使用缓存数据: {cache_path}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")
                if self.use_cache_only:
                    logger.error(f"仅缓存模式错误: 无法读取缓存文件 {cache_path}")
                    return None
        elif self.use_cache_only:
            logger.error(f"仅缓存模式错误: 找不到有效缓存 {cache_path}")
            return None
        
        # 如果是仅使用缓存模式，不发起API请求
        if self.use_cache_only:
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
        return None
    
    def fetch_coin_data(self, count=1000):
        """获取蔬菜市场数据"""
        logger.info(f"正在获取前 {count} 种蔬菜数据...")
        
        endpoint = 'coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': min(250, count),  # API单页最大250个
            'page': 1,
            'sparkline': 'false',
            'locale': 'en',
            'price_change_percentage': '24h,7d'
        }
        
        all_coins = []
        pages_needed = math.ceil(count / params['per_page'])
        
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
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                
                if data:
                    all_coins.extend(data)
                    logger.info(f"已获取 {len(all_coins)}/{count} 种蔬菜数据")
                    
                    # 达到要求的数量后结束
                    if len(all_coins) >= count:
                        break
                        
                # API请求之间暂停，避免触发速率限制
                if not self.use_cache_only and page < pages_needed:
                    time.sleep(5)
            
            # 限制数量并返回
            return all_coins[:count]
            
        except Exception as e:
            logger.error(f"获取蔬菜数据时出错: {e}")
            return all_coins if all_coins else None
    
    def fetch_price_history(self, coin_id, days=30):
        """获取蔬菜价格历史数据"""
        logger.debug(f"获取蔬菜 {coin_id} 的价格历史 (过去 {days} 天)")
        
        endpoint = f'coins/{coin_id}/market_chart'
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        try:
            # 尝试从缓存获取数据
            cache_path = self._get_cache_path(endpoint, params)
            if os.path.exists(cache_path) and self._is_cache_valid(cache_path) and (self.use_cache_only or days > 1):
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
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                    
            # 检查数据有效性
            if not data or 'prices' not in data or not data['prices']:
                logger.error(f"获取到的价格历史数据无效: {data}")
                return None
                
            # 将数据转换为DataFrame
            prices = data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'close'])
            
            # 将时间戳转换为日期
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取价格历史时出错: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """计算蔬菜价格的技术指标"""
        try:
            # 确保有'close'列
            if 'close' not in df.columns and 'price' in df.columns:
                df['close'] = df['price']  # 兼容不同数据格式
                
            # 确保数据足够用于计算指标
            if len(df) < 30:
                logger.warning(f"数据点不足，无法计算完整的技术指标: 仅有 {len(df)} 个数据点")
                return None
                
            # 计算RSI (新鲜度指标) - 14天周期
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 计算MACD (价格趋势指标)
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # 计算布林带 (价格区间)
            middle = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper = middle + (std * 2)
            lower = middle - (std * 2)
            
            # 返回最新的指标值
            return {
                'rsi': rsi,
                'macd': macd.iloc[-1],
                'signal': signal.iloc[-1],
                'upper_band': upper.iloc[-1],
                'middle_band': middle.iloc[-1],
                'lower_band': lower.iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {e}")
            return None
    
    def analyze_market_trend(self, df):
        """分析市场走势"""
        # 检查数据是否足够进行分析
        if len(df) < 5:
            return "数据不足"
            
        # 分析收盘价趋势
        last_5_prices = df['close'].tail(5).values
        current_price = last_5_prices[-1]
        
        # 计算前5天价格的均值和标准差
        mean_price = np.mean(last_5_prices)
        std_price = np.std(last_5_prices)
        
        # 计算价格变化率
        if len(last_5_prices) >= 2:
            price_change = (current_price - last_5_prices[0]) / last_5_prices[0]
        else:
            price_change = 0
        
        # 判断市场趋势
        if price_change > 0.05:  # 5%以上涨幅视为上升趋势
            return "强势上升"
        elif price_change > 0.02:  # 2-5%涨幅视为上升
            return "上升趋势"
        elif price_change < -0.05:  # 5%以上跌幅视为下降趋势
            return "强势下降"
        elif price_change < -0.02:  # 2-5%跌幅视为下降
            return "下降趋势"
        elif abs(price_change) <= 0.005:  # 价格几乎不变
            if current_price < mean_price - std_price:
                return "可能回升"  # 价格低于均值一个标准差但稳定
            elif current_price > mean_price + std_price:
                return "可能回落"  # 价格高于均值一个标准差但稳定
            else:
                return "横盘整理"  # 价格在均值附近波动
        else:
            return "短期波动"  # 其他情况

    def determine_buy_action(self, coin, indicators, market_trend, verbose=False):
        """确定是否推荐购买"""
        symbol = coin.get('symbol', '').upper()
        current_price = coin.get('current_price', 0)
        
        recommendation = {
            'symbol': symbol,
            'name': coin.get('name', ''),
            'price': current_price,
            'market_cap': coin.get('market_cap', 0),
            'price_change_24h': coin.get('price_change_percentage_24h', 0),
            'price_change_7d': coin.get('price_change_percentage_7d', 0),
            'volume_24h': coin.get('total_volume', 0),
            'rsi': indicators.get('rsi', 50),
            'reason': [],
            'score': 0
        }
        
        # 提取指标
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        signal = indicators.get('signal', 0)
        lower_band = indicators.get('lower_band', 0)
        upper_band = indicators.get('upper_band', 0)
        
        # 记录详细分析过程
        analysis_details = []
        if rsi < 30:
            analysis_details.append(f"新鲜度指标低估 ({rsi:.2f})")
        elif rsi > 70:
            analysis_details.append(f"新鲜度指标高估 ({rsi:.2f})")
        else:
            analysis_details.append(f"新鲜度指标正常 ({rsi:.2f})")
            
        if macd > signal:
            analysis_details.append(f"价格趋势上升信号 (价格趋势={macd:.6f}, Signal={signal:.6f})")
        else:
            analysis_details.append(f"价格趋势下降信号 (价格趋势={macd:.6f}, Signal={signal:.6f})")
            
        if current_price < lower_band:
            analysis_details.append(f"价格低于价格区间底部 (价格={current_price:.6f}, 底部={lower_band:.6f}, 顶部={upper_band:.6f})")
        elif current_price > upper_band:
            analysis_details.append(f"价格高于价格区间顶部 (价格={current_price:.6f}, 底部={lower_band:.6f}, 顶部={upper_band:.6f})")
        else:
            analysis_details.append(f"价格在价格区间内 (价格={current_price:.6f}, 底部={lower_band:.6f}, 顶部={upper_band:.6f})")
            
        analysis_details.append(f"市场走势分析: {market_trend}")
        
        # RSI指标判断
        rsi_signal = False
        if rsi < 30:  # RSI低于30视为低估
            recommendation['reason'].append("新鲜度指标低估")
            rsi_signal = True
            recommendation['score'] += 10
        
        # MACD判断
        macd_signal = False
        if macd > signal:  # MACD高于信号线视为上升信号
            recommendation['reason'].append("价格趋势上升信号")
            macd_signal = True
            recommendation['score'] += 20
            
        # 布林带判断
        bb_signal = False
        if current_price < lower_band:  # 价格低于下轨
            recommendation['reason'].append("价格低于价格区间底部")
            bb_signal = True
            recommendation['score'] += 15
            
        # 市场趋势判断
        trend_signal = False
        if "上升" in market_trend:
            recommendation['reason'].append(f"市场走势: {market_trend}")
            trend_signal = True
            recommendation['score'] += 15
        elif "回升" in market_trend:
            recommendation['reason'].append(f"市场走势: {market_trend}")
            trend_signal = True
            recommendation['score'] += 10
            
        # 结合信号，判断最终买入决策
        buy_decision = False
        
        # 组合条件1：MACD金叉 + (RSI低估或价格低于布林带下轨或上升趋势)
        if macd_signal and (rsi_signal or bb_signal or trend_signal):
            buy_decision = True
            
        # 特殊情况：主要趋势为强势上升
        if market_trend == "强势上升" and macd_signal:
            buy_decision = True
            recommendation['score'] += 10
            
        # 价格变化情况加分
        if coin.get('price_change_percentage_24h', 0) > 5:
            recommendation['score'] += 5
        if coin.get('price_change_percentage_7d', 0) > 10:
            recommendation['score'] += 5
            
        # 确定最终推荐
        if buy_decision:
            recommendation['action'] = "适合购买"
            final_decision = "适合购买 | 理由: " + ", ".join(recommendation['reason'])
        else:
            recommendation['action'] = "暂不购买"
            reasons = []
            if not macd_signal:
                reasons.append("价格趋势下降信号")
            if not rsi_signal and not bb_signal and not trend_signal:
                reasons.append(f"缺乏其他支持信号")
            if "下降" in market_trend:
                reasons.append(f"市场走势: {market_trend}")
                
            final_decision = "暂不购买 | 理由: " + (", ".join(reasons) if reasons else "无明显入场信号")
        
        # 打印详细分析记录
        if verbose:
            print(f"\n分析蔬菜: {symbol} ({recommendation['name']})")
            for detail in analysis_details:
                print(f"  {detail}")
            print(f"  最终决策: {final_decision}")
            
        recommendation['analysis'] = analysis_details
        return buy_decision, recommendation

    def append_recommendation_to_csv(self, symbol, data):
        """将推荐添加到CSV文件"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    symbol, data['name'], data['price'], data['market_cap'],
                    data['volume_24h'], data['price_change_7d'], data['price_change_24h'],
                    data['price_change_30d'], data['rsi'], data['action'], data['reason'],
                    data['buy_time'], data['sell_time']
                ])
        except Exception as e:
            logger.error(f"保存推荐到CSV出错: {e}")
            
    def save_results_with_timestamp(self, recommendations, timestamp=None):
        """保存带时间戳的分析结果"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # 准备要保存的数据结构
        data_to_save = []
        for rec in recommendations:
            data_to_save.append({
                'symbol': rec['symbol'],
                'name': rec['name'],
                'price': rec['price'],
                'market_cap': rec['market_cap'],
                'volume_24h': rec.get('volume_24h', 0),
                'price_change_24h': rec['price_change_24h'],
                'price_change_7d': rec['price_change_7d'],
                'rsi': rec['rsi'],
                'score': rec['score'],
                'reason': rec['reason'],
                'timestamp': timestamp
            })
            
        # 保存JSON格式
        json_filename = f"crypto_data/recommendations_{timestamp}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存推荐数据到: {json_filename}")
        except Exception as e:
            logger.error(f"保存JSON推荐数据失败: {e}")
            
        # 保存CSV格式（更易于在Excel中查看）
        csv_filename = f"crypto_data/recommendations_{timestamp}.csv"
        try:
            df = pd.DataFrame(data_to_save)
            
            # 将嵌套的reason列表转换为字符串
            df['reason'] = df['reason'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            
            # 按得分降序排序
            df = df.sort_values(by='score', ascending=False)
            
            # 保存CSV文件
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # 使用带BOM的UTF-8以兼容Excel
            logger.info(f"已保存排序后的推荐数据到: {csv_filename}")
        except Exception as e:
            logger.error(f"保存CSV推荐数据失败: {e}")
            
        return {
            'json_file': json_filename,
            'csv_file': csv_filename,
            'recommendations_count': len(recommendations)
        }
    
    def generate_recommendations(self, current_date, limit=None, sort_by='score', save_timestamp=True, save_all_data=False):
        """生成蔬菜购买推荐"""
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        
        # 获取前N个蔬菜数据
        try:
            coins = self.fetch_coin_data(count=limit or 1000)  # 默认分析前1000种蔬菜
            all_coins_count = len(coins)
            logger.info(f"成功获取 {len(coins)} 种蔬菜数据")
            
            if save_all_data:
                # 保存所有获取的原始数据
                raw_data_path = self.data_dir / f"all_coins_{timestamp}.json"
                with open(raw_data_path, 'w', encoding='utf-8') as f:
                    json.dump(coins, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存原始蔬菜数据到: {raw_data_path}")
        except Exception as e:
            logger.error(f"获取蔬菜数据失败: {e}")
            return None
            
        # 初始化推荐列表
        recommendations = []
        
        # 设置进度条
        progress_bar = tqdm(total=len(coins), desc="分析蔬菜")
        
        # 遍历并分析每种蔬菜
        for i, coin in enumerate(coins):
            try:
                symbol = coin.get('symbol', '').upper()
                
                # 获取历史价格数据
                history = self.fetch_price_history(coin['id'])
                if history is None or history.empty:
                    continue
                    
                # 计算技术指标
                indicators = self.calculate_technical_indicators(history)
                
                # 分析市场趋势
                market_trend = self.analyze_market_trend(history)
                
                # 确定是否推荐购买
                buy_decision, recommendation_data = self.determine_buy_action(
                    coin, 
                    indicators, 
                    market_trend, 
                    verbose=(i < 3)  # 只打印前3个详细分析
                )
                
                # 如果推荐购买，添加到推荐列表
                if buy_decision:
                    recommendations.append(recommendation_data)
                    
                # 更新进度条
                progress_bar.update(1)
                
            except Exception as e:
                logger.error(f"分析蔬菜 {coin.get('symbol', '')} 时出错: {e}")
                progress_bar.update(1)
                continue
                
        progress_bar.close()
        
        # 根据指定方式排序推荐
        if recommendations:
            if sort_by == 'score':
                recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)
            elif sort_by in recommendations[0].keys():
                recommendations.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
                
        # 更新当前持仓信息
        self.portfolio = recommendations
        
        # 打印推荐结果
        print("\n" + "="*50)
        print(f"推荐生成完成，共分析了 {len(coins)}/{all_coins_count} 种蔬菜")
        print(f"其中符合购买条件的蔬菜: {len(recommendations)} 种")
        print(f"当前购物车数量: {len(recommendations)} 种")
        print()
        
        if recommendations:
            print("推荐蔬菜排名 (按综合评分排序):")
            print("排名   蔬菜       名称                   价格           受欢迎度/亿       24h价格变化      7d价格变化       新鲜度      评分     推荐原因")
            print("-"*120)
            
            for i, rec in enumerate(recommendations[:10]):  # 只显示前10个
                print(f"{i+1:<5} {rec['symbol']:<8} {rec['name']:<20} {rec['price']:<15.6f} {rec['market_cap']/1e8:<10.2f} "
                      f"{rec['price_change_24h']:<10.2f} % {rec['price_change_7d']:<10.2f} % {rec['rsi']:<10.2f} "
                      f"{rec['score']:<8.1f} {', '.join(rec['reason'])}")
        
        # 保存带时间戳的推荐结果
        if save_timestamp and recommendations:
            results = self.save_results_with_timestamp(recommendations, timestamp)
            
            result_summary = {
                'timestamp': timestamp,
                'analyzed_count': len(coins),
                'total_count': all_coins_count,
                'recommendations_count': len(recommendations),
                'recommendations_fields': ['symbol', 'name', 'price', 'market_cap', 
                                           'price_change_24h', 'price_change_7d', 'rsi', 'score', 'reason']
            }
            return result_summary
            
        return {
            'timestamp': timestamp,
            'analyzed_count': len(coins),
            'total_count': all_coins_count,
            'recommendations_count': len(recommendations)
        }

    def simulate_daily_reminders(self, days=7, limit=None, sort_by='score', save_timestamp=True, save_all_data=False):
        """模拟每日菜价提醒"""
        logger.info(f"开始模拟菜价提醒，分析天数: {days}")
        
        # 获取当前日期
        current_date = datetime.now()
        
        # 生成推荐
        recommendations = self.generate_recommendations(
            current_date=current_date,
            limit=limit,
            sort_by=sort_by,
            save_timestamp=save_timestamp,
            save_all_data=save_all_data
        )
        
        return recommendations

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

def send_results_by_email(to_email, subject, text_content, files=None):
    """发送结果到指定邮箱"""
    logger.info(f"准备发送结果到邮箱: {to_email}")
    
    try:
        # 因为我们不知道用户的SMTP服务器信息，先提示用户需自行配置
        print(f"\n要发送结果到 {to_email}，您需要配置SMTP服务器信息。")
        print("通常的配置如下：")
        print("- QQ邮箱: smtp.qq.com，端口465，需要应用专用密码")
        print("- 163邮箱: smtp.163.com，端口465，需要授权码")
        print("- Gmail: smtp.gmail.com，端口587，需要应用专用密码\n")
        
        smtp_server = input("SMTP服务器地址 (例如 smtp.qq.com): ")
        smtp_port = int(input("SMTP端口 (例如 465 或 587): "))
        smtp_user = input("SMTP用户名/邮箱: ")
        smtp_password = input("SMTP密码/授权码: ")
        use_ssl = input("使用SSL? (y/n): ").lower() == 'y'
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        
        # 添加文本内容
        msg.attach(MIMEText(text_content, 'plain'))
        
        # 添加附件
        if files:
            for file_path in files:
                try:
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                except Exception as e:
                    logger.error(f"添加附件 {file_path} 失败: {e}")
        
        # 连接SMTP服务器并发送邮件
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        logger.info("邮件发送成功！")
        print(f"结果已成功发送到 {to_email}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        print(f"发送邮件失败: {e}")
        return False

def sanitize_text(text, use_obfuscation=True):
    """
    处理文本中的术语
    
    参数:
    text -- 要处理的文本
    use_obfuscation -- 是否启用术语混淆 (True: 加密货币→蔬菜, False: 保持原术语)
    """
    # 如果不启用混淆，直接返回原文本
    if not use_obfuscation:
        return text
        
    # 术语映射表 - 加密货币术语 -> 混淆术语
    replacements = {
        # 基础术语替换
        '加密货币': '菜价',
        '数字资产': '菜价',
        '币种': '蔬菜',
        '项目': '蔬菜',
        '虚拟货币': '菜价',
        '区块链': '市场分析',
        '分布式技术': '市场分析',
        '交易': '购买',
        '操作': '购买',
        '买入': '适合购买',
        '入场': '适合购买',
        '卖出': '暂不购买',
        '退场': '暂不购买',
        '持仓': '购物车',
        '趋势': '走势',
        '市值': '受欢迎度',
        '价格': '价格',
        '推荐': '推荐',
        '涨幅': '价格变化',
        '成交量': '交易量',
        '投资': '购买',
        
        # 英文替换
        'crypto': 'vegetable',
        'cryptocurrency': 'vegetable price',
        'digital asset': 'vegetable price',
        'coin': 'vegetable',
        'token': 'item',
        'blockchain': 'market analysis',
        'trading': 'shopping',
        'buy': 'buy',
        'sell': 'not buy',
        'market': 'market',
        
        # 技术指标替换
        'RSI': '新鲜度指标',
        'MACD': '价格趋势',
        '布林带': '价格区间',
        '金叉': '上升信号',
        '死叉': '下降信号',
        '超卖': '低估',
        '超买': '高估',
        '下轨': '底部',
        '上轨': '顶部',
        '下跌趋势': '下降趋势',
        '上涨趋势': '上升趋势',
        '强势上涨': '强势上升',
        '潜在反弹': '可能回升',
        '短期调整': '短期波动',
        
        # 常见货币名称替换
        'Bitcoin': '高档蔬菜',
        'BTC': '高档蔬菜',
        'Ethereum': '精品蔬菜',
        'ETH': '精品蔬菜',
        'Tether': '稳定蔬菜',
        'USDT': '稳定蔬菜',
        'BNB': '特色蔬菜',
        'Solana': '新兴蔬菜',
        'SOL': '新兴蔬菜',
        'XRP': '传统蔬菜',
        'Cardano': '优质蔬菜',
        'ADA': '优质蔬菜',
        'Dogecoin': '趣味蔬菜',
        'DOGE': '趣味蔬菜',
        'Polkadot': '创新蔬菜',
        'DOT': '创新蔬菜',
        'SHIB': '热门蔬菜',
        'Shiba': '热门蔬菜',
        'USDC': '标准蔬菜',
        'Litecoin': '轻量蔬菜',
        'LTC': '轻量蔬菜',
    }
    
    # 进行替换
    for old, new in replacements.items():
        text = text.replace(old, new)
        text = text.replace(old.capitalize(), new.capitalize())
        text = text.replace(old.upper(), new.upper())
    
    return text

def send_results_to_qq_email(to_email, subject, text_content, files=None, use_obfuscation=True):
    """
    直接发送结果到QQ邮箱，无需用户手动输入SMTP信息
    
    参数:
    to_email -- 接收邮件的邮箱地址
    subject -- 邮件主题
    text_content -- 邮件内容
    files -- 附件列表
    use_obfuscation -- 是否启用术语混淆 (True: 加密货币→蔬菜, False: 保持原术语)
    """
    # 对主题和内容进行过滤
    subject = sanitize_text(subject, use_obfuscation)
    text_content = sanitize_text(text_content, use_obfuscation)
    
    logger.info(f"准备发送结果到QQ邮箱: {to_email}")
    
    try:
        # QQ邮箱授权码映射表
        qq_auth_codes = {
            "840137950@qq.com": "gmcohszrhqxhbbji",
            "3077463778@qq.com": "wqszeiyhrbnoddij"
        }
        
        # 使用映射表中的授权码，如果没有则使用默认授权码
        smtp_user = to_email
        smtp_password = qq_auth_codes.get(to_email, "gmcohszrhqxhbbji")  # 从映射表获取授权码，未找到使用默认授权码
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        
        # 添加文本内容
        msg.attach(MIMEText(text_content, 'plain'))
        
        # 添加附件
        if files:
            for file_path in files:
                try:
                    # 判断文件类型
                    file_ext = os.path.splitext(file_path)[1].lower()
                    is_text_file = file_ext in ['.txt', '.csv', '.json', '.md']
                    
                    if is_text_file:
                        try:
                            # 尝试作为文本文件处理
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # 过滤文件内容
                            filtered_content = sanitize_text(file_content, use_obfuscation)
                            
                            # 创建临时文件
                            temp_file_path = file_path + '.temp'
                            with open(temp_file_path, 'w', encoding='utf-8') as f:
                                f.write(filtered_content)
                            
                            # 附加过滤后的文件
                            with open(temp_file_path, 'rb') as f:
                                file_data = f.read()
                                
                            # 删除临时文件
                            try:
                                os.remove(temp_file_path)
                            except:
                                pass
                                
                        except UnicodeDecodeError:
                            # 如果不是文本文件，作为二进制处理
                            is_text_file = False
                    
                    # 如果不是文本文件或读取失败，则直接作为二进制文件处理
                    if not is_text_file:
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                    
                    # 修改文件名中的敏感词
                    original_filename = os.path.basename(file_path)
                    safe_filename = sanitize_text(original_filename, use_obfuscation)
                    
                    part = MIMEApplication(file_data, Name=safe_filename)
                    part['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                    msg.attach(part)
                    
                except Exception as e:
                    logger.error(f"添加附件 {file_path} 失败: {e}")
        
        # 连接QQ邮箱SMTP服务器并发送邮件
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        logger.info("邮件发送成功！")
        print(f"结果已成功发送到 {to_email}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        print(f"发送邮件失败: {e}")
        return False

def create_scheduler_script(output_path="schedule_crypto.bat", use_obfuscation=True, use_proxies=True):
    """
    创建一个计划任务脚本，用于定期执行分析
    
    参数:
    output_path -- 输出脚本的路径
    use_obfuscation -- 是否使用术语混淆
    use_proxies -- 是否使用代理IP池
    """
    # 使用固定的邮箱地址
    email_address = "840137950@qq.com"
    email_param = f"--qq-email {email_address}"
    
    # 添加术语混淆选项
    obfuscation_param = "" if use_obfuscation else "--no-obfuscation"
    
    # 添加代理选项
    proxy_param = "--use-proxies" if use_proxies else ""
    
    # 根据是否混淆选择描述文本
    task_description = "菜价分析任务" if use_obfuscation else "加密货币分析任务"
    
    script_content = f"""@echo off
echo 开始执行{task_description}: %date% %time%
python bn.py --coins 1000 --save-raw --cache-only=false {email_param} {obfuscation_param} {proxy_param}
echo 完成执行: %date% %time%
"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"已创建计划任务脚本: {output_path}")
        print("您可以使用 Windows 计划任务来定期执行此脚本")
    except Exception as e:
        logger.error(f"创建计划任务脚本失败: {e}")

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
        parser.add_argument('--create-scheduler', action='store_true', help='创建一个计划任务脚本，用于定期执行分析')
        parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，减少输出信息')
        parser.add_argument('--email', type=str, help='发送结果到指定邮箱地址')
        parser.add_argument('--qq-email', type=str, help='发送结果到指定QQ邮箱地址(简化流程)，多个邮箱用逗号分隔')
        parser.add_argument('--no-obfuscation', action='store_true', help='不使用术语混淆，直接使用加密货币术语')
        parser.add_argument('--use-proxies', action='store_true', help='启用代理IP池，避免API请求限制')
        parser.add_argument('--add-proxy', type=str, help='添加代理到代理池，格式为http://ip:port或socks5://username:password@host:port')
        parser.add_argument('--add-proxies-from-url', type=str, help='从URL添加代理到代理池')
        parser.add_argument('--add-socks5-proxy', type=str, metavar='HOST:PORT', help='添加SOCKS5代理，格式为host:port')
        parser.add_argument('--socks5-username', type=str, help='SOCKS5代理用户名')
        parser.add_argument('--socks5-password', type=str, help='SOCKS5代理密码')
        parser.add_argument('--list-proxies', action='store_true', help='列出当前代理池中的所有代理')
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
        
        # 创建计划任务脚本
        if args.create_scheduler:
            use_obfuscation = not args.no_obfuscation
            create_scheduler_script(use_obfuscation=use_obfuscation, use_proxies=args.use_proxies)
            return
            
        # 设置日志级别
        if args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        
        print("开始运行菜价分析系统...\n")
        print("初始化...\n")
        recommender = CryptoRecommender(use_cache_only=args.cache_only, use_proxies=args.use_proxies)
        print("初始化完成，开始获取和分析数据...\n")
        
        # 执行分析
        results = recommender.simulate_daily_reminders(
            days=1, 
            limit=args.limit, 
            sort_by=args.sort_by,
            save_timestamp=not args.no_save,
            save_all_data=args.save_raw
        )
        
        print("\n程序执行完成！")
        if results:
            print(f"共分析了 {results['analyzed_count']}/{results['total_count']} 种蔬菜")
            print(f"发现 {results['recommendations_count']} 个推荐")
            
            # 保存结果文件
            saved_files = []
            if not args.no_save and results.get('recommendations_count', 0) > 0:
                json_file = f"crypto_data/recommendations_{results['timestamp']}.json"
                csv_file = f"crypto_data/recommendations_{results['timestamp']}.csv"
                if os.path.exists(json_file):
                    saved_files.append(json_file)
                if os.path.exists(csv_file):
                    saved_files.append(csv_file)
                if args.save_raw:
                    raw_file = f"crypto_data/all_coins_{results['timestamp']}.json"
                    if os.path.exists(raw_file):
                        saved_files.append(raw_file)
                print(f"结果已保存，时间戳: {results['timestamp']}")
            
            # 准备邮件内容
            email_content = f"""
菜价分析结果摘要:

分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析蔬菜: {results['analyzed_count']}/{results['total_count']} 种
推荐购买: {results['recommendations_count']} 种

详细结果请查看附件。
            """
            
            # 确定是否使用术语混淆
            use_obfuscation = not args.no_obfuscation
            
            # 准备邮件主题
            email_subject = "加密货币分析结果" if not use_obfuscation else "菜价分析结果"
            email_subject += f" - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 如果指定了QQ邮箱，使用简化流程发送
            if args.qq_email:
                # 支持多个邮箱地址（逗号分隔）
                email_addresses = [email.strip() for email in args.qq_email.split(',')]
                for email_address in email_addresses:
                    if email_address:  # 确保邮箱地址不为空
                        send_results_to_qq_email(
                            to_email=email_address, 
                            subject=email_subject,
                            text_content=email_content,
                            files=saved_files,
                            use_obfuscation=use_obfuscation
                        )
            # 如果指定了其他邮箱，使用普通流程
            elif args.email:
                send_results_by_email(
                    to_email=args.email, 
                    subject=email_subject,
                    text_content=email_content,
                    files=saved_files
                )
                
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"\n错误: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 