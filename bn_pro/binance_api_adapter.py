#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Binance API适配器
处理与Binance API的交互，支持实际API调用和模拟数据模式
"""

import os
import json
import time
import logging
import requests
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# 导入模拟数据生成器
try:
    from mock_data_generator import mock_data
    HAS_MOCK_DATA = True
except ImportError:
    HAS_MOCK_DATA = False

# 配置日志
logger = logging.getLogger(__name__)

class BinanceAPIAdapter:
    """Binance API适配器，处理API请求和响应"""
    
    def __init__(self, use_cache_only=False, refresh_cache=False, use_proxies=False, mock_data=False, force_real_api=False):
        """
        初始化Binance API适配器
        
        Args:
            use_cache_only: 是否只使用缓存
            refresh_cache: 是否强制刷新缓存
            use_proxies: 是否使用代理
            mock_data: 是否使用模拟数据
            force_real_api: 是否强制使用真实API（即使检测不可用）
        """
        self.base_url = "https://api.binance.com"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 设置API密钥（如果有）
        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_API_SECRET")
        
        if self.api_key and self.api_secret:
            self.headers["X-MBX-APIKEY"] = self.api_key
            logger.info("已配置Binance API密钥")
        else:
            logger.info("未配置Binance API密钥，部分功能可能受限")
        
        # 缓存设置
        self.use_cache_only = use_cache_only
        self.refresh_cache = refresh_cache
        
        # 确保缓存目录存在
        self.cache_dir = Path("crypto_data") / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 代理设置
        self.use_proxies = use_proxies
        self.proxies = self._load_proxies() if use_proxies else None
        
        # 模拟数据设置
        self.force_real_api = force_real_api
        self.use_mock_data = mock_data
        
        # 如果不是强制使用模拟数据，检查API是否可用
        if not mock_data and not force_real_api:
            if not self._is_api_available():
                logger.warning("无法访问Binance API，将启用模拟数据模式")
                self.use_mock_data = True
        
        if self.use_mock_data:
            logger.info("已启用模拟数据模式")
        
        # 尝试多个Binance API域名
        self.api_urls = [
            "https://api.binance.com",
            "https://api1.binance.com",
            "https://api2.binance.com",
            "https://api3.binance.com"
        ]
        
        # 找到可用的API URL
        if not self.use_mock_data and not self.use_cache_only:
            self._find_available_api_url()
        
        # 初始化币种ID映射
        self.coin_id_map = {
            'bitcoin': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'binancecoin': 'BNBUSDT',
            'ripple': 'XRPUSDT',
            'cardano': 'ADAUSDT',
            'solana': 'SOLUSDT',
            'polkadot': 'DOTUSDT',
            'dogecoin': 'DOGEUSDT',
            'shiba-inu': 'SHIBUSDT',
            'litecoin': 'LTCUSDT',
            'chainlink': 'LINKUSDT',
            'uniswap': 'UNIUSDT',
            'avalanche-2': 'AVAXUSDT',
            'polygon': 'MATICUSDT',
            'tron': 'TRXUSDT',
            'cosmos': 'ATOMUSDT',
            'stellar': 'XLMUSDT',
            'algorand': 'ALGOUSDT'
            # 可以根据需要添加更多映射
        }
    
    def _load_proxies(self):
        """加载代理"""
        proxies = {}
        try:
            with open("proxies.txt", "r") as f:
                proxy_lines = f.readlines()
                if proxy_lines:
                    proxy = random.choice(proxy_lines).strip()
                    proxies = {
                        "http": proxy,
                        "https": proxy
                    }
                    logger.info(f"使用代理: {proxy}")
        except Exception as e:
            logger.error(f"加载代理失败: {e}")
        return proxies
    
    def _find_available_api_url(self):
        """尝试找到可用的Binance API URL"""
        for url in self.api_urls:
            try:
                test_url = f"{url}/api/v3/ping"
                response = requests.get(test_url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    self.base_url = url
                    logger.info(f"使用可用的Binance API URL: {url}")
                    return
            except:
                continue
        
        # 如果所有URL都不可用，使用默认URL
        logger.warning("所有Binance API URL均不可用，使用默认URL")
    
    def _is_api_available(self):
        """
        检查Binance API是否可用
        
        Returns:
            bool: API是否可用
        """
        # 尝试多个API URL和端点
        endpoints = [
            "/api/v3/ping",
            "/api/v3/time",
            "/api/v3/exchangeInfo"
        ]
        
        for url in self.api_urls:
            for endpoint in endpoints:
                try:
                    test_url = f"{url}{endpoint}"
                    response = requests.get(
                        test_url, 
                        headers=self.headers, 
                        timeout=5,
                        proxies=self.proxies
                    )
                    
                    if response.status_code == 200:
                        # 找到可用的API URL，设置为基础URL
                        self.base_url = url
                        return True
                except:
                    continue
        
        return False
    
    def convert_coingecko_id(self, coin_id: str) -> str:
        """
        将CoinGecko的币种ID转换为Binance交易对符号
        
        Args:
            coin_id: CoinGecko的币种ID
            
        Returns:
            str: Binance交易对符号
        """
        # 从映射中获取交易对，如果不存在则尝试构建
        symbol = self.coin_id_map.get(coin_id.lower())
        if not symbol:
            # 对于未知的币种，尝试将其转换为大写并添加USDT后缀
            # 注意：这可能不适用于所有币种，仅作为备选方案
            if '-' in coin_id:
                # 如果ID中包含连字符，通常需要特殊处理
                parts = coin_id.split('-')
                if len(parts) > 1 and parts[0]:
                    symbol = parts[0].upper() + 'USDT'
                else:
                    symbol = coin_id.upper() + 'USDT'
            else:
                symbol = coin_id.upper() + 'USDT'
            logger.warning(f"未找到币种ID '{coin_id}'的映射，使用默认转换: {symbol}")
        
        return symbol
    
    def _read_cache_safely(self, cache_file):
        """
        安全地读取缓存文件，处理可能的编码问题和null字节
        
        Args:
            cache_file: 缓存文件路径
            
        Returns:
            Any: 缓存数据，如果读取失败则返回None
        """
        try:
            # 首先尝试常规方式读取
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 移除可能的null字节
                content = content.replace('\x00', '')
                return json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果有编码问题，尝试使用二进制模式并修复
                with open(cache_file, 'rb') as f:
                    content = f.read()
                # 移除null字节
                content = content.replace(b'\x00', b'')
                # 解码并解析
                return json.loads(content.decode('utf-8', errors='ignore'))
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None

    def _save_cache_safely(self, cache_file, data):
        """
        安全地保存缓存文件，确保完整性
        
        Args:
            cache_file: 缓存文件路径
            data: 要保存的数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 创建临时文件
            temp_file = str(cache_file) + '.tmp'
            
            # 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 确保写入成功
            with open(temp_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # 如果读取成功，替换原文件
            if os.path.exists(cache_file):
                os.remove(cache_file)
            os.rename(temp_file, cache_file)
            
            logger.debug(f"缓存保存成功: {cache_file}")
            return True
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            # 清理临时文件
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
            return False

    def _make_api_request(self, endpoint: str, method: str = "GET", params: Dict = None) -> Any:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            method: 请求方法 (GET, POST, etc.)
            params: 请求参数
            
        Returns:
            Any: API响应数据
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        # 如果使用模拟数据，则返回模拟响应
        if self.use_mock_data:
            logger.info(f"使用模拟数据: {endpoint}")
            return self._generate_mock_response(endpoint, params)
        
        # 构建缓存键
        cache_key = endpoint.replace('/', '_').replace('?', '_')
        if params:
            for k, v in sorted(params.items()):
                cache_key += f"_{k}={v}"
        cache_key = cache_key.replace(' ', '_')
        
        # 缓存文件路径
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # 如果使用缓存且缓存文件存在
        if self.use_cache_only:
            cached_data = self._read_cache_safely(cache_file) if cache_file.exists() else None
            if cached_data is not None:
                logger.info(f"从缓存加载数据: {cache_file}")
                return cached_data
            else:
                logger.error(f"仅缓存模式错误: 找不到有效缓存 {cache_file}")
                # 如果是仅缓存模式且没有缓存，尝试使用模拟数据
                return self._generate_mock_response(endpoint, params)
        
        # 如果不强制刷新缓存且缓存文件存在
        if not self.refresh_cache and cache_file.exists():
            try:
                # 检查缓存是否过期（24小时）
                if cache_file.stat().st_mtime > time.time() - 86400:
                    cached_data = self._read_cache_safely(cache_file)
                    if cached_data is not None:
                        logger.info(f"从缓存加载数据: {cache_file}")
                        return cached_data
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}，将尝试API请求")
        
        # 实际API请求
        url = f"{self.base_url}{endpoint}"
        logger.info(f"请求API: {url}，参数: {params}")
        
        max_retries = 3
        retry_count = 0
        retry_delay = 5
        
        while retry_count <= max_retries:
            try:
                # 添加重试延迟
                if retry_count > 0:
                    time.sleep(retry_delay)
                    logger.warning(f"重试API请求 ({retry_count}/{max_retries})...")
                
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=15  # 15秒超时
                )
                
                # 检查响应状态码
                if response.status_code != 200:
                    logger.error(f"API请求失败，状态码: {response.status_code}")
                    try:
                        error_data = response.json()
                        logger.error(f"错误信息: {error_data}")
                    except:
                        logger.error(f"无法解析错误响应: {response.text}")
                    
                    retry_count += 1
                    if retry_count > max_retries:
                        # 如果API请求失败，尝试使用模拟数据
                        logger.info("API请求失败，使用模拟数据")
                        return self._generate_mock_response(endpoint, params)
                    continue
                
                # 解析响应数据
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error("API响应解析失败，非有效JSON格式")
                    retry_count += 1
                    if retry_count > max_retries:
                        return self._generate_mock_response(endpoint, params)
                    continue
                
                # 保存到缓存
                self._save_cache_safely(cache_file, data)
                
                return data
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    # 如果API请求失败，尝试使用模拟数据
                    logger.info("API请求失败，使用模拟数据")
                    return self._generate_mock_response(endpoint, params)
        
        # 如果所有重试都失败
        logger.error("API请求失败，使用模拟数据")
        return self._generate_mock_response(endpoint, params)
    
    def _generate_mock_response(self, endpoint: str, params: Dict = None) -> Any:
        """
        生成模拟响应数据
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            Any: 模拟响应数据
        """
        # 确保params不为None
        if params is None:
            params = {}
            
        if HAS_MOCK_DATA and mock_data:
            return mock_data.generate_mock_response(endpoint, params)
        
        # 如果没有引入mock_data模块，则使用内置的简单模拟数据生成
        if endpoint == "/api/v3/klines":
            return self._generate_mock_klines(params)
        elif endpoint == "/api/v3/ticker/24hr":
            return self._generate_mock_ticker_24hr(params)
        elif endpoint == "/api/v3/exchangeInfo":
            return self._generate_mock_exchange_info()
        else:
            logger.warning(f"未实现的模拟端点: {endpoint}")
            return {}
    
    def _generate_mock_klines(self, params: Dict = None) -> List[List]:
        """
        生成模拟K线数据
        
        Args:
            params: 请求参数
            
        Returns:
            List[List]: 模拟K线数据
        """
        if not params:
            params = {}
        
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1d")
        limit = int(params.get("limit", 30))
        
        # 确定基础价格和波动范围
        base_price = 0
        price_range = 0
        
        if "BTC" in symbol:
            base_price = 30000.0
            price_range = 3000.0
        elif "ETH" in symbol:
            base_price = 2000.0
            price_range = 200.0
        else:
            # 对于其他币种，使用随机基础价格
            seed = sum(ord(c) for c in symbol)
            random.seed(seed)
            magnitude = 10 ** random.randint(-3, 5)  # 随机数量级
            base_price = random.uniform(1, 100) * magnitude
            price_range = base_price * 0.1  # 价格范围为基础价格的10%
        
        # 生成模拟数据
        now = datetime.now()
        klines = []
        
        # 确定时间间隔（毫秒）
        if interval == "1d":
            time_step = 24 * 60 * 60 * 1000  # 1天的毫秒数
        elif interval == "4h":
            time_step = 4 * 60 * 60 * 1000  # 4小时的毫秒数
        elif interval == "1h":
            time_step = 60 * 60 * 1000  # 1小时的毫秒数
        else:
            time_step = 24 * 60 * 60 * 1000  # 默认使用1天
        
        # 生成每个时间点的K线数据
        for i in range(limit):
            # 计算当前时间戳
            timestamp = int((now - timedelta(days=limit - i - 1)).timestamp() * 1000)
            
            # 使用正弦波生成价格趋势，并添加一些随机性
            trend_factor = np.sin(i / 5) * 0.5 + 0.5  # 0-1之间的趋势因子
            price_factor = 1 + (trend_factor - 0.5) * 0.1  # 价格因子，在0.95-1.05之间
            
            # 计算开盘价、最高价、最低价和收盘价
            current_base = base_price * price_factor
            open_price = current_base * (1 + random.uniform(-0.02, 0.02))
            close_price = current_base * (1 + random.uniform(-0.02, 0.02))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.03))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.03))
            
            # 生成交易量
            volume = base_price * random.uniform(100, 1000)
            
            # 构建K线数据
            kline = [
                timestamp,  # 开盘时间
                f"{open_price:.8f}",  # 开盘价
                f"{high_price:.8f}",  # 最高价
                f"{low_price:.8f}",  # 最低价
                f"{close_price:.8f}",  # 收盘价
                f"{volume:.8f}",  # 成交量
                timestamp + time_step,  # 收盘时间
                f"{volume * close_price:.8f}",  # 成交额
                1000,  # 成交笔数
                f"{volume * 0.6:.8f}",  # 主动买入成交量
                f"{volume * 0.6 * close_price:.8f}",  # 主动买入成交额
                "0"  # 忽略
            ]
            
            klines.append(kline)
        
        return klines
    
    def _generate_mock_ticker_24hr(self, params: Dict = None) -> Union[Dict, List[Dict]]:
        """
        生成模拟24小时行情数据
        
        Args:
            params: 请求参数
            
        Returns:
            Union[Dict, List[Dict]]: 模拟24小时行情数据
        """
        if params and "symbol" in params:
            # 生成单个交易对的数据
            symbol = params["symbol"]
            return self._generate_single_ticker(symbol)
        else:
            # 生成多个交易对的数据
            tickers = []
            
            # 热门交易对
            popular_pairs = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
                "DOGEUSDT", "SHIBUSDT", "SOLUSDT", "DOTUSDT", "MATICUSDT",
                "LINKUSDT", "LTCUSDT", "UNIUSDT", "AVAXUSDT", "TRXUSDT",
                "ATOMUSDT", "XLMUSDT", "NEARUSDT", "ICPUSDT", "ETCUSDT"
            ]
            
            # 为每个交易对生成数据
            for symbol in popular_pairs:
                tickers.append(self._generate_single_ticker(symbol))
            
            # 添加一些随机交易对
            for i in range(80):
                # 生成随机交易对
                random_symbol = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(3, 6))) + "USDT"
                tickers.append(self._generate_single_ticker(random_symbol))
            
            return tickers
    
    def _generate_single_ticker(self, symbol: str) -> Dict:
        """
        生成单个交易对的24小时行情数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            Dict: 模拟行情数据
        """
        # 确定基础价格和波动范围
        base_price = 0
        price_range = 0
        
        if "BTC" in symbol:
            base_price = 30000.0
            price_range = 3000.0
        elif "ETH" in symbol:
            base_price = 2000.0
            price_range = 200.0
        elif "BNB" in symbol:
            base_price = 300.0
            price_range = 30.0
        else:
            # 对于其他币种，使用随机基础价格
            seed = sum(ord(c) for c in symbol)
            random.seed(seed)
            magnitude = 10 ** random.randint(-4, 4)  # 随机数量级
            base_price = random.uniform(1, 100) * magnitude
            price_range = base_price * 0.1  # 价格范围为基础价格的10%
        
        # 生成价格变动
        price_change = random.uniform(-price_range * 0.05, price_range * 0.05)
        price_change_percent = (price_change / base_price) * 100
        
        # 生成当前价格
        current_price = base_price + price_change
        
        # 生成最高价和最低价
        high_price = current_price * (1 + random.uniform(0.01, 0.05))
        low_price = current_price * (1 - random.uniform(0.01, 0.05))
        
        # 生成交易量
        volume = base_price * random.uniform(1000, 10000)
        quote_volume = volume * current_price
        
        # 构建ticker数据
        return {
            "symbol": symbol,
            "priceChange": f"{price_change:.8f}",
            "priceChangePercent": f"{price_change_percent:.2f}",
            "weightedAvgPrice": f"{current_price:.8f}",
            "prevClosePrice": f"{base_price:.8f}",
            "lastPrice": f"{current_price:.8f}",
            "lastQty": f"{random.uniform(0.1, 10):.8f}",
            "bidPrice": f"{current_price * 0.999:.8f}",
            "bidQty": f"{random.uniform(0.1, 10):.8f}",
            "askPrice": f"{current_price * 1.001:.8f}",
            "askQty": f"{random.uniform(0.1, 10):.8f}",
            "openPrice": f"{base_price:.8f}",
            "highPrice": f"{high_price:.8f}",
            "lowPrice": f"{low_price:.8f}",
            "volume": f"{volume:.8f}",
            "quoteVolume": f"{quote_volume:.8f}",
            "openTime": int((datetime.now() - timedelta(days=1)).timestamp() * 1000),
            "closeTime": int(datetime.now().timestamp() * 1000),
            "firstId": 1000,
            "lastId": 10000,
            "count": 9000
        }
    
    def _generate_mock_exchange_info(self) -> Dict:
        """
        生成模拟交易所信息
        
        Returns:
            Dict: 模拟交易所信息
        """
        # 热门交易对
        popular_pairs = [
            "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SHIB", "SOL", "DOT", "MATIC",
            "LINK", "LTC", "UNI", "AVAX", "TRX", "ATOM", "XLM", "NEAR", "ICP", "ETC"
        ]
        
        symbols = []
        
        # 为每个热门交易对生成数据
        for base_asset in popular_pairs:
            symbols.append({
                "symbol": f"{base_asset}USDT",
                "status": "TRADING",
                "baseAsset": base_asset,
                "baseAssetPrecision": 8,
                "quoteAsset": "USDT",
                "quotePrecision": 8,
                "quoteAssetPrecision": 8,
                "orderTypes": ["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"],
                "icebergAllowed": True,
                "ocoAllowed": True,
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": True,
                "filters": [],
                "permissions": ["SPOT", "MARGIN"]
            })
        
        # 添加一些随机交易对
        for i in range(80):
            random_asset = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(3, 6)))
            symbols.append({
                "symbol": f"{random_asset}USDT",
                "status": "TRADING",
                "baseAsset": random_asset,
                "baseAssetPrecision": 8,
                "quoteAsset": "USDT",
                "quotePrecision": 8,
                "quoteAssetPrecision": 8,
                "orderTypes": ["LIMIT", "MARKET"],
                "icebergAllowed": False,
                "ocoAllowed": False,
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": False,
                "filters": [],
                "permissions": ["SPOT"]
            })
        
        return {
            "timezone": "UTC",
            "serverTime": int(datetime.now().timestamp() * 1000),
            "rateLimits": [],
            "exchangeFilters": [],
            "symbols": symbols
        }
    
    def get_klines(self, symbol: str, interval: str = "1d", limit: int = 30) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号，如 BTCUSDT
            interval: 时间间隔，如 1d, 4h, 1h
            limit: 返回的K线数量
            
        Returns:
            List[List]: K线数据列表
        """
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        return self._make_api_request(endpoint, params=params)
    
    def get_ticker_24hr(self, symbol: str = None) -> Union[Dict, List[Dict]]:
        """
        获取24小时行情数据
        
        Args:
            symbol: 交易对符号，如 BTCUSDT，不提供则返回所有交易对
            
        Returns:
            Union[Dict, List[Dict]]: 24小时行情数据
        """
        endpoint = "/api/v3/ticker/24hr"
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._make_api_request(endpoint, params=params)
    
    def get_exchange_info(self) -> Dict:
        """
        获取交易所信息
        
        Returns:
            Dict: 交易所信息
        """
        endpoint = "/api/v3/exchangeInfo"
        return self._make_api_request(endpoint)
    
    def fetch_coin_data(self, count=100):
        """
        获取币种数据
        
        Args:
            count: 返回的币种数量
            
        Returns:
            List[Dict]: 币种数据列表
        """
        logger.info(f"获取前 {count} 种币种数据...")
        
        # 获取24小时行情数据
        ticker_data = self.get_ticker_24hr()
        
        # 过滤出USDT交易对并按成交量排序
        usdt_pairs = [
            ticker for ticker in ticker_data 
            if isinstance(ticker, dict) and 
            ticker.get("symbol", "").endswith("USDT") and 
            not ticker.get("symbol", "").startswith("USDT")
        ]
        
        # 按交易量排序
        usdt_pairs = sorted(usdt_pairs, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
        
        # 只返回指定数量
        top_pairs = usdt_pairs[:count]
        
        # 整理数据格式，使其与CoinGecko API格式兼容
        result = []
        for pair in top_pairs:
            symbol = pair.get("symbol", "")
            base_asset = symbol.replace("USDT", "")
            
            # 计算价格变化百分比
            price_change_percent = float(pair.get("priceChangePercent", "0")) 
            
            # 构建兼容CoinGecko格式的数据
            coin_data = {
                "id": base_asset.lower(),  # 使用币种符号作为ID
                "symbol": base_asset.lower(),
                "name": base_asset,
                "current_price": float(pair.get("lastPrice", "0")),
                "market_cap": float(pair.get("quoteVolume", "0")),  # 使用交易量代替市值
                "market_cap_rank": top_pairs.index(pair) + 1,
                "total_volume": float(pair.get("volume", "0")),
                "price_change_24h": float(pair.get("priceChange", "0")),
                "price_change_percentage_24h": price_change_percent,
                "price_change_percentage_7d": 0.0,  # Binance API 没有直接提供7天变化
                "price_change_percentage_30d": 0.0,  # Binance API 没有直接提供30天变化
                "circulating_supply": 0,  # Binance API 没有提供流通量
                "max_supply": 0,  # Binance API 没有提供最大供应量
                "ath": float(pair.get("highPrice", "0")),  # 24小时最高价
                "ath_change_percentage": 0.0,
                "ath_date": datetime.now().isoformat(),
                "atl": float(pair.get("lowPrice", "0")),  # 24小时最低价
                "atl_change_percentage": 0.0,
                "atl_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            result.append(coin_data)
        
        logger.info(f"成功获取 {len(result)} 种币种数据")
        return result
    
    def get_price_history(self, symbol, interval='1d', limit=30):
        """
        获取价格历史数据
        
        Args:
            symbol: 币种符号，如 BTC
            interval: 时间间隔，如 1d, 4h, 1h
            limit: 返回的数据点数量
            
        Returns:
            pd.DataFrame: 价格历史数据
        """
        try:
            import pandas as pd
            
            # 确保交易对格式正确
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # 获取K线数据
            klines = self.get_klines(symbol, interval, limit)
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_asset_volume',
                'number_of_trades', 'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 处理数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # 设置索引
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol}价格历史失败: {e}")
            return None
    
    def fetch_price_history(self, coin_id, days=30):
        """
        获取币种价格历史
        
        Args:
            coin_id: 币种ID或符号
            days: 天数
            
        Returns:
            pd.DataFrame: 价格历史数据
        """
        try:
            # 如果输入的是CoinGecko ID，转换为Binance交易对
            symbol = coin_id
            if not coin_id.endswith('USDT'):
                symbol = f"{coin_id.upper()}USDT"
            
            # 计算需要的K线数量
            limit = min(1000, days * 24 // 24)  # 日线数据，每天1条
            
            return self.get_price_history(symbol, interval='1d', limit=limit)
        except Exception as e:
            logger.error(f"获取{coin_id}价格历史失败: {e}")
            return None

# 创建一个默认实例
binance_api = BinanceAPIAdapter()

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 测试代码
    api = BinanceAPIAdapter(use_mock_data=True)
    
    # 测试获取K线数据
    klines = api.get_klines("BTCUSDT", "1d", 10)
    print(f"K线数据 (共{len(klines)}条):")
    print(json.dumps(klines[0], indent=2))
    
    # 测试获取24小时行情
    ticker = api.get_ticker_24hr("BTCUSDT")
    print("\n24小时行情数据:")
    print(json.dumps(ticker, indent=2))
    
    # 测试获取交易所信息
    exchange_info = api.get_exchange_info()
    print(f"\n交易所信息 (共{len(exchange_info.get('symbols', []))}个交易对):") 