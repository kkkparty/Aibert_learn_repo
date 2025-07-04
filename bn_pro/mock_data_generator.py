#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模拟数据生成器
用于生成Binance API的模拟响应数据，便于在无法访问API的环境中测试
"""

import json
import random
import datetime
import numpy as np
from typing import Dict, List, Any, Union

class MockDataGenerator:
    """生成模拟的Binance API响应数据"""
    
    def __init__(self):
        """初始化模拟数据生成器"""
        self.coins = {
            "BTC": {"name": "Bitcoin", "symbol": "BTCUSDT"},
            "ETH": {"name": "Ethereum", "symbol": "ETHUSDT"},
            "BNB": {"name": "Binance Coin", "symbol": "BNBUSDT"},
            "SOL": {"name": "Solana", "symbol": "SOLUSDT"},
            "XRP": {"name": "XRP", "symbol": "XRPUSDT"},
            "ADA": {"name": "Cardano", "symbol": "ADAUSDT"},
            "DOGE": {"name": "Dogecoin", "symbol": "DOGEUSDT"},
            "AVAX": {"name": "Avalanche", "symbol": "AVAXUSDT"},
            "DOT": {"name": "Polkadot", "symbol": "DOTUSDT"},
            "SHIB": {"name": "Shiba Inu", "symbol": "SHIBUSDT"}
        }
        
        # 基础价格参考（美元）
        self.base_prices = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "BNB": 400.0,
            "SOL": 100.0,
            "XRP": 0.5,
            "ADA": 0.4,
            "DOGE": 0.08,
            "AVAX": 35.0,
            "DOT": 7.0,
            "SHIB": 0.00001
        }
    
    def generate_klines(self, symbol: str, interval: str = "1d", limit: int = 30) -> List[List]:
        """
        生成K线数据
        
        Args:
            symbol: 交易对符号，如 BTCUSDT
            interval: 时间间隔，如 1d, 4h, 1h
            limit: 返回的K线数量
            
        Returns:
            List[List]: K线数据列表
        """
        now = datetime.datetime.now()
        coin_code = symbol.replace("USDT", "")
        base_price = self.base_prices.get(coin_code, 100.0)
        
        # 生成随机波动的价格序列
        prices = []
        price = base_price
        for _ in range(limit):
            # 添加一些随机波动
            change_percent = random.uniform(-0.05, 0.05)  # -5% 到 +5% 的变化
            price = price * (1 + change_percent)
            prices.append(price)
        
        # 确保价格序列有一些趋势和波动
        prices = np.array(prices)
        
        # 添加一些趋势
        trend = np.linspace(-0.1, 0.1, limit)
        prices = prices * (1 + trend)
        
        # 生成K线数据
        klines = []
        for i in range(limit):
            timestamp = int((now - datetime.timedelta(days=limit-i-1)).timestamp() * 1000)
            open_price = prices[i] * random.uniform(0.99, 1.01)
            high_price = prices[i] * random.uniform(1.01, 1.05)
            low_price = prices[i] * random.uniform(0.95, 0.99)
            close_price = prices[i]
            volume = base_price * close_price * random.uniform(100, 1000)
            
            kline = [
                timestamp,                    # 开盘时间
                str(open_price),              # 开盘价
                str(high_price),              # 最高价
                str(low_price),               # 最低价
                str(close_price),             # 收盘价
                str(volume),                  # 成交量
                int(timestamp + 86400000),    # 收盘时间
                str(volume * close_price),    # 成交额
                100,                          # 成交笔数
                str(volume * 0.6),            # 主动买入成交量
                str(volume * 0.6 * close_price), # 主动买入成交额
                "0"                           # 忽略
            ]
            klines.append(kline)
        
        return klines
    
    def generate_ticker_24hr(self, symbol: str = None) -> Union[Dict, List[Dict]]:
        """
        生成24小时行情数据
        
        Args:
            symbol: 交易对符号，如 BTCUSDT，如果为None则返回所有交易对
            
        Returns:
            Dict 或 List[Dict]: 24小时行情数据
        """
        if symbol:
            coin_code = symbol.replace("USDT", "")
            base_price = self.base_prices.get(coin_code, 100.0)
            
            return {
                "symbol": symbol,
                "priceChange": str(base_price * random.uniform(-0.05, 0.05)),
                "priceChangePercent": str(random.uniform(-5, 5)),
                "weightedAvgPrice": str(base_price * random.uniform(0.98, 1.02)),
                "prevClosePrice": str(base_price * random.uniform(0.98, 1.02)),
                "lastPrice": str(base_price),
                "lastQty": str(random.uniform(0.1, 10)),
                "bidPrice": str(base_price * 0.999),
                "bidQty": str(random.uniform(1, 100)),
                "askPrice": str(base_price * 1.001),
                "askQty": str(random.uniform(1, 100)),
                "openPrice": str(base_price * random.uniform(0.97, 1.03)),
                "highPrice": str(base_price * random.uniform(1.01, 1.05)),
                "lowPrice": str(base_price * random.uniform(0.95, 0.99)),
                "volume": str(base_price * random.uniform(1000, 10000)),
                "quoteVolume": str(base_price * base_price * random.uniform(1000, 10000)),
                "openTime": int((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp() * 1000),
                "closeTime": int(datetime.datetime.now().timestamp() * 1000),
                "firstId": 12345,
                "lastId": 67890,
                "count": 55555
            }
        else:
            # 返回所有交易对的数据
            result = []
            for coin_code, coin_info in self.coins.items():
                result.append(self.generate_ticker_24hr(coin_info["symbol"]))
            return result
    
    def generate_exchange_info(self) -> Dict:
        """
        生成交易所信息
        
        Returns:
            Dict: 交易所信息
        """
        symbols = []
        for coin_code, coin_info in self.coins.items():
            symbols.append({
                "symbol": coin_info["symbol"],
                "status": "TRADING",
                "baseAsset": coin_code,
                "baseAssetPrecision": 8,
                "quoteAsset": "USDT",
                "quotePrecision": 8,
                "quoteAssetPrecision": 8,
                "baseCommissionPrecision": 8,
                "quoteCommissionPrecision": 8,
                "orderTypes": ["LIMIT", "LIMIT_MAKER", "MARKET", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"],
                "icebergAllowed": True,
                "ocoAllowed": True,
                "quoteOrderQtyMarketAllowed": True,
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": True,
                "filters": [],
                "permissions": ["SPOT", "MARGIN"]
            })
        
        return {
            "timezone": "UTC",
            "serverTime": int(datetime.datetime.now().timestamp() * 1000),
            "rateLimits": [],
            "exchangeFilters": [],
            "symbols": symbols
        }
    
    def generate_mock_response(self, endpoint: str, params: Dict = None) -> Any:
        """
        根据API端点生成模拟响应
        
        Args:
            endpoint: API端点路径
            params: API参数
            
        Returns:
            Any: 模拟的API响应
        """
        # 确保params不为None
        if params is None:
            params = {}
        
        if endpoint == "/api/v3/klines":
            symbol = params.get("symbol", "BTCUSDT")
            interval = params.get("interval", "1d")
            limit = int(params.get("limit", 30))
            return self.generate_klines(symbol, interval, limit)
        
        elif endpoint == "/api/v3/ticker/24hr":
            symbol = params.get("symbol")
            if symbol:
                return self.generate_ticker_24hr(symbol)
            else:
                return self.generate_ticker_24hr()
        
        elif endpoint == "/api/v3/exchangeInfo":
            return self.generate_exchange_info()
        
        # 默认返回空字典
        return {}

# 全局实例，可直接导入使用
mock_data = MockDataGenerator()

if __name__ == "__main__":
    # 测试代码
    generator = MockDataGenerator()
    
    # 测试K线数据生成
    klines = generator.generate_klines("BTCUSDT", "1d", 30)
    print(f"K线数据示例 (共{len(klines)}条):")
    print(json.dumps(klines[0], indent=2))
    
    # 测试24小时行情数据生成
    ticker = generator.generate_ticker_24hr("BTCUSDT")
    print("\n24小时行情数据示例:")
    print(json.dumps(ticker, indent=2))
    
    # 测试交易所信息生成
    exchange_info = generator.generate_exchange_info()
    print(f"\n交易所信息示例 (共{len(exchange_info['symbols'])}个交易对):")
    print(json.dumps(exchange_info["symbols"][0], indent=2)) 