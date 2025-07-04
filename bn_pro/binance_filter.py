#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import os
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 币安常用币种列表，当API访问失败时使用
COMMON_BINANCE_SYMBOLS = [
    "BTC", "ETH", "BNB", "USDT", "USDC", "BUSD", "XRP", "ADA", "DOGE", "SOL",
    "DOT", "SHIB", "LTC", "TRX", "AVAX", "LINK", "MATIC", "UNI", "ATOM", "ETC",
    "BCH", "XLM", "ALGO", "NEAR", "XMR", "FIL", "VET", "EGLD", "HBAR", "MANA",
    "SAND", "AAVE", "AXS", "EOS", "ICP", "FTM", "XTZ", "THETA", "NEO", "WAVES",
    "CAKE", "ONE", "CHZ", "ROSE", "ZIL", "ENJ", "BAT", "DASH", "KSM", "FTT",
    "GALA", "RVN", "IOTA", "GRT", "CELO", "LRC", "CRV", "HOT", "YFI", "BTT",
    "KLAY", "1INCH", "COMP", "AR", "MKR", "QTUM", "SRM", "OMG", "SUSHI", "DYDX",
    "ANKR", "XEM", "LUNA", "UST", "STX", "ZEC", "ENS", "ICX", "BTTC", "BNX",
    "CELR", "CFX", "SNX", "ONT", "KNC", "SXP", "ZEN", "IOST", "JST", "REEF",
    "CVC", "ANT", "RSR", "SKL", "BAL", "STORJ", "KAVA", "RLC", "BAND", "DENT"
]

class BinanceFilter:
    def __init__(self, cache_dir='crypto_data/cache', cache_expiry_hours=24):
        """初始化币安过滤器"""
        self.cache_dir = cache_dir
        self.cache_expiry_hours = cache_expiry_hours
        self.binance_symbols = self.get_binance_symbols()
        logger.info(f"已加载 {len(self.binance_symbols)} 个币安支持的币种")
        
    def get_binance_symbols(self):
        """获取币安支持的所有币种符号"""
        cache_file = os.path.join(self.cache_dir, 'binance_symbols.json')
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # 检查是否有有效的缓存
        if os.path.exists(cache_file):
            file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
            if file_age_hours < self.cache_expiry_hours:
                try:
                    with open(cache_file, 'r') as f:
                        symbols = json.load(f)
                        logger.info(f"从缓存加载了 {len(symbols)} 个币安币种")
                        if len(symbols) > 0:
                            return symbols
                except Exception as e:
                    logger.error(f"读取币安币种缓存失败: {e}")
        
        # 没有有效缓存，请求API
        try:
            logger.info("请求币安API获取支持的币种列表...")
            response = requests.get('https://api.binance.com/api/v3/exchangeInfo', timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 提取所有的基础货币和报价货币
                all_symbols = set()
                for pair in data['symbols']:
                    if pair['status'] == 'TRADING':  # 只考虑当前可交易的
                        base_asset = pair['baseAsset']
                        quote_asset = pair['quoteAsset']
                        all_symbols.add(base_asset)
                        all_symbols.add(quote_asset)
                
                # 保存到缓存
                with open(cache_file, 'w') as f:
                    json.dump(list(all_symbols), f)
                
                logger.info(f"成功获取 {len(all_symbols)} 个币安支持的币种")
                return list(all_symbols)
            else:
                logger.error(f"获取币安币种列表失败: HTTP {response.status_code}")
                # 如果有旧缓存，尝试使用
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r') as f:
                            symbols = json.load(f)
                            if len(symbols) > 0:
                                logger.warning(f"API请求失败，使用过期缓存，包含 {len(symbols)} 个币种")
                                return symbols
                    except:
                        pass
                
                # 如果API请求失败且没有可用缓存，使用预定义的常用币种列表
                logger.warning(f"使用内置的常用币安币种列表（{len(COMMON_BINANCE_SYMBOLS)}个币种）")
                
                # 保存到缓存
                with open(cache_file, 'w') as f:
                    json.dump(COMMON_BINANCE_SYMBOLS, f)
                    
                return COMMON_BINANCE_SYMBOLS
                
        except Exception as e:
            logger.error(f"请求币安API出错: {e}")
            # 如果有旧缓存，尝试使用
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        symbols = json.load(f)
                        if len(symbols) > 0:
                            logger.warning(f"API请求出错，使用过期缓存，包含 {len(symbols)} 个币种")
                            return symbols
                except:
                    pass
            
            # 如果出错且没有可用缓存，使用预定义的常用币种列表
            logger.warning(f"使用内置的常用币安币种列表（{len(COMMON_BINANCE_SYMBOLS)}个币种）")
            return COMMON_BINANCE_SYMBOLS
    
    def is_supported_by_binance(self, symbol):
        """检查一个币种符号是否被币安支持"""
        # 统一转换为大写
        symbol = symbol.upper()
        return symbol in self.binance_symbols
    
    def filter_recommendations(self, recommendations):
        """过滤推荐列表，只保留币安支持的币种"""
        original_count = len(recommendations)
        filtered = [rec for rec in recommendations if self.is_supported_by_binance(rec.get('symbol', ''))]
        
        logger.info(f"币安过滤: 从 {original_count} 个推荐中筛选出 {len(filtered)} 个币安支持的币种")
        return filtered

class TechnicalAnalysisFilter:
    """技术分析过滤器，用于计算技术指标"""
    
    def __init__(self):
        """初始化技术分析过滤器"""
        # 设置RSI参数
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # 设置MACD参数
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # 设置布林带参数
        self.bollinger_period = 20
        self.bollinger_std = 2
        
        # 设置移动平均线参数
        self.ma_short = 10
        self.ma_medium = 50
        self.ma_long = 200
        
    def analyze_coin(self, coin_id, name, symbol, current_price, price_history):
        """分析币种的技术指标"""
        try:
            # 确保价格历史数据格式正确
            if not isinstance(price_history, pd.DataFrame):
                logger.error(f"价格历史数据格式错误: {type(price_history)}")
                return None
                
            if 'close' not in price_history.columns:
                if len(price_history.columns) >= 5:  # 假设是OHLCV格式
                    price_history.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                else:
                    logger.error(f"价格历史数据缺少close列: {price_history.columns}")
                    return None
            
            # 计算技术指标
            df = price_history.copy()
            
            # 计算RSI
            rsi = self._calculate_rsi(df['close'], self.rsi_period)
            rsi_value = rsi.iloc[-1] if not rsi.empty else 50
            
            # 计算MACD
            macd, signal, hist = self._calculate_macd(df['close'], self.macd_fast, self.macd_slow, self.macd_signal)
            macd_value = macd.iloc[-1] if not macd.empty else 0
            signal_value = signal.iloc[-1] if not signal.empty else 0
            hist_value = hist.iloc[-1] if not hist.empty else 0
            
            # 计算布林带
            upper, middle, lower = self._calculate_bollinger_bands(df['close'], self.bollinger_period, self.bollinger_std)
            
            # 计算移动平均线
            ma_short = self._calculate_ma(df['close'], self.ma_short)
            ma_medium = self._calculate_ma(df['close'], self.ma_medium)
            ma_long = self._calculate_ma(df['close'], self.ma_long)
            
            # 计算价格变化百分比
            price_change_1d = self._calculate_price_change(df['close'], 1)
            price_change_7d = self._calculate_price_change(df['close'], 7)
            price_change_30d = self._calculate_price_change(df['close'], 30)
            
            # 分析RSI信号
            if rsi_value > self.rsi_overbought:
                rsi_signal = "OVERBOUGHT"
            elif rsi_value < self.rsi_oversold:
                rsi_signal = "OVERSOLD"
            else:
                rsi_signal = "NEUTRAL"
                
            # 分析MACD信号
            if macd_value > signal_value and hist_value > 0:
                macd_signal = "BULLISH"
            elif macd_value < signal_value and hist_value < 0:
                macd_signal = "BEARISH"
            else:
                macd_signal = "NEUTRAL"
                
            # 分析布林带信号
            if current_price > upper.iloc[-1]:
                bollinger_signal = "OVERBOUGHT"
            elif current_price < lower.iloc[-1]:
                bollinger_signal = "OVERSOLD"
            else:
                bollinger_signal = "NEUTRAL"
                
            # 分析趋势信号
            if ma_short.iloc[-1] > ma_medium.iloc[-1] > ma_long.iloc[-1]:
                trend_signal = "STRONG_BULLISH"
            elif ma_short.iloc[-1] > ma_medium.iloc[-1]:
                trend_signal = "BULLISH"
            elif ma_short.iloc[-1] < ma_medium.iloc[-1] < ma_long.iloc[-1]:
                trend_signal = "STRONG_BEARISH"
            elif ma_short.iloc[-1] < ma_medium.iloc[-1]:
                trend_signal = "BEARISH"
            else:
                trend_signal = "NEUTRAL"
                
            # 计算总分
            score = self._calculate_score(
                rsi_value, rsi_signal,
                macd_signal, hist_value,
                bollinger_signal,
                trend_signal,
                price_change_1d, price_change_7d, price_change_30d
            )
            
            # 生成购买信号
            if score >= 70:
                buy_signal = "STRONG_BUY"
            elif score >= 60:
                buy_signal = "BUY"
            elif score <= 30:
                buy_signal = "STRONG_SELL"
            elif score <= 40:
                buy_signal = "SELL"
            else:
                buy_signal = "NEUTRAL"
                
            # 构建分析结果
            analysis = {
                'coin_id': coin_id,
                'name': name,
                'symbol': symbol,
                'current_price': current_price,
                'price_change_1d': price_change_1d,
                'price_change_7d': price_change_7d,
                'price_change_24h': price_change_1d,  # 兼容性别名
                'price_change_30d': price_change_30d,
                'rsi_value': rsi_value,
                'rsi_signal': rsi_signal,
                'macd_value': macd_value,
                'macd_signal': macd_signal,
                'bollinger_signal': bollinger_signal,
                'trend_signal': trend_signal,
                'buy_signal': buy_signal,
                'total_score': score,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析 {coin_id} 时出错: {e}")
            return None
            
    def _calculate_rsi(self, prices, period=14):
        """计算RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _calculate_macd(self, prices, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD"""
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        hist = macd - signal
        
        return macd, signal, hist
        
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """计算布林带"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
        
    def _calculate_ma(self, prices, period):
        """计算移动平均线"""
        return prices.rolling(window=period).mean()
        
    def _calculate_price_change(self, prices, days):
        """计算价格变化百分比"""
        if len(prices) <= days:
            return 0
            
        current = prices.iloc[-1]
        previous = prices.iloc[-days-1] if len(prices) > days else prices.iloc[0]
        
        if previous == 0:
            return 0
            
        return ((current - previous) / previous) * 100
        
    def _calculate_score(self, rsi, rsi_signal, macd_signal, macd_hist, bollinger_signal, trend_signal, change_1d, change_7d, change_30d):
        """计算总分"""
        score = 50  # 初始分数
        
        # RSI评分
        if rsi_signal == "OVERSOLD":
            score += 10
        elif rsi_signal == "OVERBOUGHT":
            score -= 10
        elif rsi < 40:
            score += 5
        elif rsi > 60:
            score -= 5
            
        # MACD评分
        if macd_signal == "BULLISH":
            score += 10
        elif macd_signal == "BEARISH":
            score -= 10
            
        # MACD柱状图变化
        if macd_hist > 0 and abs(macd_hist) > 0.01:
            score += 5
        elif macd_hist < 0 and abs(macd_hist) > 0.01:
            score -= 5
            
        # 布林带评分
        if bollinger_signal == "OVERSOLD":
            score += 10
        elif bollinger_signal == "OVERBOUGHT":
            score -= 10
            
        # 趋势评分
        if trend_signal == "STRONG_BULLISH":
            score += 15
        elif trend_signal == "BULLISH":
            score += 10
        elif trend_signal == "STRONG_BEARISH":
            score -= 15
        elif trend_signal == "BEARISH":
            score -= 10
            
        # 价格变化评分
        if change_1d > 5:
            score += 5
        elif change_1d < -5:
            score -= 5
            
        if change_7d > 10:
            score += 5
        elif change_7d < -10:
            score -= 5
            
        if change_30d > 20:
            score += 5
        elif change_30d < -20:
            score -= 5
            
        # 限制分数范围
        score = max(0, min(100, score))
        
        return score

def filter_binance_coins(results, include_binance_only=False):
    """处理结果，如果需要则只保留币安支持的币种"""
    if not include_binance_only or 'recommendations' not in results:
        return results
    
    binance_filter = BinanceFilter()
    original_count = len(results.get('recommendations', []))
    
    # 过滤推荐列表
    results['recommendations'] = binance_filter.filter_recommendations(results['recommendations'])
    results['recommendations_count'] = len(results['recommendations'])
    
    # 更新长线和短线数量
    if 'long_term_count' in results and 'short_term_count' in results:
        results['long_term_count'] = len([r for r in results['recommendations'] if not r.get('is_short_term', False)])
        results['short_term_count'] = len([r for r in results['recommendations'] if r.get('is_short_term', False)])
    
    print(f"\n币安过滤: 从 {original_count} 个推荐中筛选出 {results['recommendations_count']} 个币安支持的币种")
    return results

if __name__ == "__main__":
    # 测试代码
    bf = BinanceFilter()
    test_symbols = ["BTC", "ETH", "FAKE1", "DOGE", "NOTREAL"]
    for symbol in test_symbols:
        print(f"{symbol} 在币安支持: {bf.is_supported_by_binance(symbol)}") 