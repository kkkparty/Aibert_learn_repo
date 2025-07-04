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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import math
import traceback
import requests
import matplotlib.pyplot as plt
from config import EMAIL_CONFIG, EMAIL_PRESETS

from binance_api_adapter import BinanceAPIAdapter
from binance_filter import TechnicalAnalysisFilter

# 导入配置
try:
    from config import EMAIL_PRESETS, EMAIL_CONFIG, DATA_DIR
except ImportError:
    # 如果找不到config.py，创建默认配置
    EMAIL_PRESETS = {
        1: {
            'sender': '840137950@qq.com',
            'password': os.environ.get('QQ_EMAIL_PASSWORD', 'your_password_here'),
            'receiver': '840137950@qq.com'
        },
        2: {
            'sender': '3077463778@qq.com',
            'password': os.environ.get('QQ_EMAIL_PASSWORD', 'your_password_here'),
            'receiver': '3077463778@qq.com'
        }
    }
    EMAIL_CONFIG = {
        'qq': {
            'server': 'smtp.qq.com',
            'port': 465,
            'use_ssl': True
        },
        '163': {
            'server': 'smtp.163.com',
            'port': 25,
            'use_ssl': False
        }
    }
    DATA_DIR = 'crypto_data'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BinanceCryptoRecommender:
    def __init__(self, use_cache_only=False, refresh_cache=False, use_proxies=False, mock_data=False, force_real_api=False):
        """
        初始化推荐系统
        
        Args:
            use_cache_only: 是否只使用缓存
            refresh_cache: 是否强制刷新缓存
            use_proxies: 是否使用代理
            mock_data: 是否使用模拟数据
            force_real_api: 是否强制使用真实API（即使检测不可用）
        """
        self.api = BinanceAPIAdapter(
            use_cache_only=use_cache_only,
            refresh_cache=refresh_cache,
            use_proxies=use_proxies,
            mock_data=mock_data,
            force_real_api=force_real_api
        )
        
        # 技术分析过滤器
        self.filter = TechnicalAnalysisFilter()
        
        # 确保数据目录存在
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
        # 设置缓存选项
        self.use_cache_only = use_cache_only
        self.refresh_cache = refresh_cache
        self.portfolio = None
        
        # 初始化日志消息
        if use_cache_only:
            logging.info("使用缓存模式")
            print("[MODE] 缓存模式 - 仅使用缓存数据")
        elif refresh_cache:
            logging.info("强制刷新模式")
            print("[MODE] 强制刷新模式 - 不使用缓存数据")
        else:
            logging.info("API请求模式")
            print("[MODE] API请求模式 - 优先从网络获取数据")
        
        # 初始化数据存储
        self.holdings = {}
        self.recommendations = {}
        self.total_investment = 0
        self.max_position_size = 0.2  # 单个币种最大仓位为20%
        
        # 设置CSV输出文件
        self.csv_file = self.data_dir / 'recommendations.csv'
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['symbol', 'name', 'price', 'market_cap', 'volume_24h', 
                               'price_change_7d', 'price_change_24h', 'price_change_30d',
                               'rsi', 'action', 'reason', 'buy_time', 'sell_time'])
        
        # 邮件设置
        self.email_sender = None
        self.email_password = None
        self.email_receiver = None
        
        # 使用配置文件中的预设邮箱配置
        self.email_presets = EMAIL_PRESETS
        
    def set_email(self, email):
        """设置邮箱"""
        if isinstance(email, str):
            # 处理多个邮箱地址（逗号分隔）
            email_list = [e.strip() for e in email.split(',') if e.strip()]
            if email_list:
                self.email_sender = email_list[0]  # 使用第一个作为发送者
                self.email_receiver = email
                # 尝试从环境变量获取密码
                if '@qq.com' in self.email_sender.lower():
                    self.email_password = os.environ.get('QQ_EMAIL_PASSWORD')
                    logger.info(f"使用QQ邮箱: {self.email_sender}")
                    
                    # 如果环境变量未设置，尝试从bn2bc.py文件中获取预设密码
                    if not self.email_password:
                        try:
                            # 硬编码的QQ邮箱授权码映射表（来自bn2bc.py）
                            qq_auth_codes = {
                                "840137950@qq.com": "gmcohszrhqxhbbji",
                                "3077463778@qq.com": "wqszeiyhrbnoddij"
                            }
                            self.email_password = qq_auth_codes.get(self.email_sender)
                            if self.email_password:
                                logger.info(f"使用预设QQ邮箱授权码")
                        except:
                            pass
                elif '@163.com' in self.email_sender.lower():
                    self.email_password = os.environ.get('163_EMAIL_PASSWORD')
                    logger.info(f"使用163邮箱: {self.email_sender}")
                else:
                    logger.warning(f"未设置邮箱密码，可能无法发送邮件")
        else:
            logger.error(f"邮箱格式错误: {email}")
        
    def use_preset_email(self, preset_id):
        """使用预设邮箱配置"""
        if preset_id in self.email_presets:
            preset = self.email_presets[preset_id]
            self.email_sender = preset['sender']
            self.email_password = preset['password']
            self.email_receiver = preset['receiver']
            logger.info(f"使用预设邮箱 {preset_id}: {self.email_sender}")
        else:
            logger.error(f"预设邮箱 {preset_id} 不存在")
            
    def fetch_coin_data(self, count=100):
        """获取币种数据"""
        return self.api.fetch_coin_data(count=count)
    
    def fetch_price_history(self, coin_id, days=30):
        """获取价格历史数据"""
        try:
            return self.api.fetch_price_history(coin_id, days)
        except Exception as e:
            logger.error(f"获取{coin_id}价格历史失败: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """计算技术指标"""
        try:
            # 确保有'close'列
            if 'close' not in df.columns and 'price' in df.columns:
                df['close'] = df['price']  # 处理不同数据格式
                
            # 数据点太少无法计算指标
            if len(df) < 30:
                logger.warning(f"数据点太少，无法计算技术指标: {len(df)} 个数据点")
                return None
                
            # RSI (相对强弱指标) - 14天
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD (指数移动平均线)
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # 布林带
            middle = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper = middle + (std * 2)
            lower = middle - (std * 2)
            
            # 返回计算的指标值
            return {
                'rsi': rsi,
                'macd': macd.iloc[-1],
                'signal': signal.iloc[-1],
                'upper_band': upper.iloc[-1],
                'middle_band': middle.iloc[-1],
                'lower_band': lower.iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"计算技术指标错误: {e}")
            return None
    
    def analyze_market_trend(self, df):
        """分析市场趋势"""
        # 数据不足
        if len(df) < 5:
            return "pending"
            
        # 分析最近价格趋势
        last_5_prices = df['close'].tail(5).values
        current_price = last_5_prices[-1]
        
        # 计算均价和标准差
        mean_price = np.mean(last_5_prices)
        std_price = np.std(last_5_prices)
        
        # 计算价格变化
        if len(last_5_prices) >= 2:
            price_change = (current_price - last_5_prices[0]) / last_5_prices[0]
        else:
            price_change = 0
        
        # 判断趋势
        if price_change > 0.05:  # 5%以上涨幅视为明显上升
            return "强势上涨"
        elif price_change > 0.02:  # 2-5%涨幅视为上升
            return "上涨"
        elif price_change < -0.05:  # 5%以上跌幅视为明显下跌
            return "强势下跌"
        elif price_change < -0.02:  # 2-5%跌幅视为下跌
            return "下跌"
        elif abs(price_change) <= 0.005:  # 价格基本稳定
            if current_price < mean_price - std_price:
                return "盘整" # 低于平均水平但稳定
            elif current_price > mean_price + std_price:
                return "盘整" # 高于平均水平但稳定
            else:
                return "震荡" # 在平均水平附近震荡
        else:
            return "弱势震荡" # 其他情况
    
    def determine_buy_action(self, coin, indicators, market_trend, verbose=False):
        """确定是否应该买入"""
        symbol = coin.get('symbol', '').upper()
        name = coin.get('name', symbol)
        current_price = coin.get('current_price', 0)
        market_cap = coin.get('market_cap', 0)
        volume_24h = coin.get('total_volume', 0)
        price_change_24h = coin.get('price_change_percentage_24h', 0)
        price_change_7d = 0  # Binance API没有提供7天数据
        
        # 初始化推荐数据
        recommendation = {
            'symbol': symbol,
            'name': name,
            'price': current_price,
            'market_cap': market_cap,
            'volume_24h': volume_24h,
            'price_change_7d': price_change_7d,
            'price_change_24h': price_change_24h,
            'price_change_30d': 0,  # Binance API暂不提供30天数据
            'rsi': indicators.get('rsi', 0) if indicators else 0,
            'action': "Hold",
            'reason': "无明显信号",
            'buy_time': '',
            'sell_time': ''
        }
        
        # 初始化分析详情
        analysis_details = [
            f"价格: {current_price}",
            f"24h变化: {price_change_24h:.2f}%",
            f"市值: {market_cap:.2f}",
            f"交易量(24h): {volume_24h:.2f}",
            f"RSI(14): {indicators.get('rsi', 0):.2f}",
            f"MACD: {indicators.get('macd', 0):.6f}, 信号: {indicators.get('signal', 0):.6f}",
            f"布林下轨: {indicators.get('lower_band', 0):.6f}, 上轨: {indicators.get('upper_band', 0):.6f}",
            f"市场趋势: {market_trend}"
        ]
        
        # 判断买入信号
        buy_signals = []
        
        # 1. RSI超卖
        rsi_signal = False
        if indicators:
            rsi = indicators.get('rsi', 0)
            if rsi < 30:
                rsi_signal = True
                buy_signals.append("RSI低于30，超卖信号")
            elif rsi < 40:
                rsi_signal = True
                buy_signals.append("RSI低于40，偏向超卖")
        
        # 2. MACD金叉
        macd_signal = False
        if indicators:
            macd = indicators.get('macd', 0)
            signal = indicators.get('signal', 0)
            if macd > signal and macd < 0:
                macd_signal = True
                buy_signals.append("MACD金叉形成")
        
        # 3. 布林带突破
        bb_signal = False
        if indicators:
            lower_band = indicators.get('lower_band', 0)
            if current_price < lower_band:
                bb_signal = True
                buy_signals.append("价格低于布林下轨")
        
        # 4. 市场趋势信号
        trend_signal = False
        if "上涨" in market_trend:
            trend_signal = True
            buy_signals.append(f"市场趋势：{market_trend}")
        elif market_trend == "盘整":
            trend_signal = True
            buy_signals.append("市场处于盘整震荡")
        
        # 5. 价格信号
        price_signal = False
        if price_change_24h > 5 and price_change_24h < 15:
            price_signal = True
            buy_signals.append("24小时价格上涨适度")
        elif price_change_24h < -10:
            price_signal = True
            buy_signals.append("24小时大幅下跌，超卖")
        
        # 综合至少两个买入信号
        buy_decision = False
        final_decision = ""
        
        signal_count = sum([rsi_signal, macd_signal, bb_signal, trend_signal, price_signal])
        
        if signal_count >= 2:
            # 组合信号，比如RSI+MACD或布林带
            if (rsi_signal and (macd_signal or bb_signal)) or (macd_signal and bb_signal):
                buy_decision = True
                recommendation['action'] = "买入"
                recommendation['reason'] = "技术指标组合信号"
                recommendation['buy_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 计算推荐得分
                score = self.calculate_recommendation_score(recommendation)
                recommendation['score'] = score
                recommendation['reason'] = buy_signals
                
                final_decision = f"买入 | 评分: {score:.1f} | 行动: " + (", ".join(buy_signals))
                
        if not buy_decision:
            recommendation['action'] = "Hold"
            reasons = []
            if not macd_signal:
                reasons.append("缺乏MACD金叉")
            if not rsi_signal and not bb_signal and not trend_signal:
                reasons.append("缺乏RSI/布林带/趋势信号")
            if "下跌" in market_trend:
                reasons.append(f"市场: {market_trend}")
                
            final_decision = f"Hold | 原因: " + (", ".join(reasons) if reasons else "无明显入场信号")
        
        # 输出分析详情
        if verbose:
            print(f"\n分析: {symbol} ({recommendation['name']})")
            for detail in analysis_details:
                print(f"  {detail}")
            print(f"  决策: {final_decision}")
                
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
            logger.error(f"添加到CSV错误: {e}")
            
    def save_results_with_timestamp(self, recommendations, timestamp=None):
        """保存结果到文件，使用时间戳命名"""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保目录存在
        os.makedirs("crypto_data", exist_ok=True)
        
        # 保存为JSON
        json_file = f"crypto_data/{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        
        # 保存为CSV（如果可能）
        try:
            csv_file = f"crypto_data/{timestamp}.csv"
            
            # 转换为DataFrame
            if isinstance(recommendations, list):
                df = pd.DataFrame(recommendations)
            elif isinstance(recommendations, dict) and 'recommendations' in recommendations:
                df = pd.DataFrame(recommendations['recommendations'])
            else:
                # 无法转换为DataFrame
                return json_file
                
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            return json_file
        except Exception as e:
            logger.error(f"保存CSV失败: {e}")
            return json_file
    
    def generate_recommendations(self, current_date=None, limit=None, sort_by='score', save_timestamp=True, 
                              save_all_data=False, email_addresses=None, high_score_threshold=50):
        """生成推荐列表"""
        if current_date is None:
            current_date = datetime.now()
            
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        
        # 获取币种数据
        try:
            coins = self.fetch_coin_data(count=limit or 100)  # Binance API获取数据
            all_coins_count = len(coins)
            logger.info(f"获取了 {len(coins)} 个币种数据")
            
            # 保存原始数据
            if save_all_data:
                raw_data_path = self.data_dir / f"all_coins_{timestamp}.json"
                with open(raw_data_path, 'w', encoding='utf-8') as f:
                    json.dump(coins, f, ensure_ascii=False, indent=2)
                logger.info(f"原始数据保存到: {raw_data_path}")
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return None
            
        # 进度条
        try:
            from tqdm import tqdm
            progress_bar = tqdm(total=len(coins), desc="分析币种")
            has_tqdm = True
        except ImportError:
            has_tqdm = False
            logger.info(f"分析 {len(coins)} 个币种...")
        
        # 分析每个币种
        recommendations = []
        high_score_recommendations = []  # 高评分推荐
        
        for i, coin in enumerate(coins):
            try:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id', symbol.lower())
                
                # 获取历史数据
                history = self.fetch_price_history(coin_id)
                if history is None or history.empty:
                    if has_tqdm:
                        progress_bar.update(1)
                    continue
                    
                # 计算技术指标
                indicators = self.calculate_technical_indicators(history)
                if indicators is None:
                    if has_tqdm:
                        progress_bar.update(1)
                    continue
                
                # 分析市场趋势
                market_trend = self.analyze_market_trend(history)
                
                # 确定是否应该买入
                buy_decision, recommendation_data = self.determine_buy_action(
                    coin,
                    indicators,
                    market_trend,
                    verbose=(i < 3)  # 只打印前3个的详细分析
                )
                
                # 检查BTC和ETH，总是发送邮件通知
                if coin_id.lower() in ['bitcoin', 'btc', 'ethereum', 'eth'] and email_addresses:
                    coin_email_subject = f"币种状态: {symbol}"
                    
                    coin_email_content = f"""
币种状态:

代码: {symbol}
名称: {name}
当前价格: {current_price}
市值: {market_cap}
24小时涨跌: {price_change_24h:.2f}%
RSI指标: {indicators.get('rsi', 0):.2f}
市场趋势: {market_trend}

操作建议: {recommendation_data['action']}
                    """
                    
                    # 发送邮件
                    for email_address in email_addresses:
                        if email_address and email_address.strip():
                            try:
                                from bn2bc import send_results_to_qq_email
                                send_results_to_qq_email(
                                    to_email=email_address.strip(),
                                    subject=coin_email_subject,
                                    text_content=coin_email_content,
                                    files=None,  # 无附件
                                    use_obfuscation=False  # 不使用混淆
                                )
                                logger.info(f"已将 {symbol} 数据发送到 {email_address}")
                            except Exception as e:
                                logger.error(f"发送 {symbol} 邮件失败: {e}")
                
                # 如果是买入信号，添加到推荐列表
                if buy_decision:
                    recommendations.append(recommendation_data)
                    
                    # 如果评分超过阈值，添加到高评分列表并发送邮件
                    if recommendation_data.get('score', 0) >= high_score_threshold and email_addresses:
                        high_score_recommendations.append(recommendation_data)
                        
                        # 为高评分推荐发送邮件通知
                        coin_email_subject = f"高评分推荐: {recommendation_data['symbol']} (评分: {recommendation_data['score']})"
                        
                        coin_email_content = f"""
高评分推荐币种:

代码: {recommendation_data['symbol']}
名称: {recommendation_data['name']}
当前价格: {recommendation_data['price']}
市值: {recommendation_data['market_cap']}
24小时涨跌: {recommendation_data['price_change_24h']}%
评分: {recommendation_data['score']}
信号: {', '.join(recommendation_data['reason'])}

此为自动生成的高评分推荐邮件。
                        """
                        
                        # 为每个邮箱发送
                        for email_address in email_addresses:
                            if email_address and email_address.strip():
                                try:
                                    from bn2bc import send_results_to_qq_email
                                    send_results_to_qq_email(
                                        to_email=email_address.strip(),
                                        subject=coin_email_subject,
                                        text_content=coin_email_content,
                                        files=None,  # 无附件
                                        use_obfuscation=False  # 不使用混淆
                                    )
                                    logger.info(f"已将高评分推荐 {recommendation_data['symbol']} 发送到 {email_address}")
                                except Exception as e:
                                    logger.error(f"发送高评分推荐失败: {e}")
                
                # 更新进度
                if has_tqdm:
                    progress_bar.update(1)
                elif i % 10 == 0:
                    logger.info(f"已分析 {i+1}/{len(coins)} 个币种...")
                    
            except Exception as e:
                logger.error(f"分析币种 {coin.get('symbol', '')} 错误: {e}")
                if has_tqdm:
                    progress_bar.update(1)
                continue
                
        if has_tqdm:
            progress_bar.close()
        
        # 如果有推荐，根据指定字段排序
        if recommendations:
            if sort_by == 'score':
                recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)
            elif sort_by in recommendations[0].keys():
                recommendations.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
                
        # 更新投资组合
        self.portfolio = recommendations
        
        # 打印输出结果
        print("\n" + "="*50)
        print(f"生成了 {len(coins)}/{all_coins_count} 个币种分析")
        print(f"产生买入信号: {len(recommendations)} 个")
        print(f"高评分推荐(>={high_score_threshold}分): {len(high_score_recommendations)} 个")
        print(f"推荐总数: {len(recommendations)} 个")
        print()
        
        if recommendations:
            print("推荐币种排名 (按评分):")
            print("序号   代码      名称               价格         市值/量      24h变化      RSI    评分   信号")
            print("-"*120)
            
            for i, rec in enumerate(recommendations[:10]):  # 只显示前10个
                print(f"{i+1:<5} {rec['symbol']:<8} {rec['name']:<18} {rec['price']:<15.6f} {rec['market_cap']/1e8:<10.2f} "
                     f"{rec['price_change_24h']:<10.2f}% {rec['rsi']:<10.2f} "
                     f"{rec['score']:<8.1f} {', '.join(rec['reason'])}")
        
        # 保存结果
        result_files = {}
        if save_timestamp and recommendations:
            results = self.save_results_with_timestamp(recommendations, timestamp)
            result_files = {
                'json_file': results.get('json_file', ''),
                'csv_file': results.get('csv_file', '')
            }
            
        result_summary = {
            'timestamp': timestamp,
            'analyzed_count': len(coins),
            'total_count': all_coins_count,
            'recommendations_count': len(recommendations),
            'high_score_count': len(high_score_recommendations),
            'recommendations_fields': ['symbol', 'name', 'price', 'market_cap',
                                      'price_change_24h', 'rsi', 'score', 'reason'],
            'result_files': result_files
        }
            
        return result_summary
    
    def simulate_daily_reminders(self, days=1, limit=None, sort_by='score', save_timestamp=True, 
                              save_all_data=False, email_addresses=None, high_score_threshold=50):
        """模拟每日提醒系统"""
        logger.info(f"模拟币种分析和提醒，周期: {days}天")
        
        # 当前时间
        current_date = datetime.now()
        
        # 生成推荐
        recommendations = self.generate_recommendations(
            current_date=current_date,
            limit=limit,
            sort_by=sort_by,
            save_timestamp=save_timestamp,
            save_all_data=save_all_data,
            email_addresses=email_addresses,
            high_score_threshold=high_score_threshold
        )
        
        return recommendations
    
    def calculate_recommendation_score(self, coin_data):
        """计算推荐得分"""
        score = 0
        
        # 1. 根据RSI计算得分
        rsi = coin_data.get('rsi', 50)
        # RSI: 低于30(超卖)高分，30-50中等分，其他零分
        if rsi <= 30:
            score += 20 * (1 - rsi/30)  # RSI越低，分数越高
        elif rsi <= 50:
            score += 10 * (50 - rsi) / 20  # 30-50之间线性递减
            
        # 2. 根据市场趋势打分
        reason = coin_data.get('reason', '')
        if isinstance(reason, list):
            reason_text = ''.join(reason)
        else:
            reason_text = str(reason)
            
        if '上升' in reason_text:
            score += 15
        elif '上涨' in reason_text:
            score += 10
        elif '震荡' in reason_text:
            score += 5
            
        # 3. 根据MACD金叉打分
        if 'MACD金叉' in reason_text:
            score += 20
            
        # 4. 根据布林带打分
        if '布林带下轨' in reason_text:
            score += 15
            
        # 5. 根据价格涨跌打分
        price_change_24h = coin_data.get('price_change_24h', 0)
        
        # 适中上涨(3-8%)加分
        if price_change_24h > 5:
            score += 5  # 24小时涨幅超过5%
        elif 2 < price_change_24h <= 5:
            score += 3  # 2-5%适中涨幅
            
        # 6. 成交量/市值比率 (流动性指标)
        market_cap = coin_data.get('market_cap', 0)
        volume_24h = coin_data.get('volume_24h', 0)
        if market_cap > 0:
            liquidity_ratio = volume_24h / market_cap
            # 流动性比例0.05-0.5之间最佳
            score += min(liquidity_ratio * 100, 15)  # 最高15分
            
        # 7. 市值评分 (大市值币种更稳健)
        # 按市值分层级
        if market_cap >= 10_000_000_000:  # 百亿美元
            score += 8
        elif market_cap >= 1_000_000_000:  # 十亿美元
            score += 3
        elif market_cap >= 100_000_000:  # 亿美元
            score += 1
            
        return score

    def analyze_crypto_market(self, coin_count=100, top_count=10):
        """分析加密货币市场并生成推荐"""
        logger.info(f"正在获取前{coin_count}种加密货币数据...")
        
        # 获取币种数据
        coins = self.api.fetch_coin_data(count=coin_count)
        if not coins:
            logger.error("获取数据失败: 无法获取币种列表")
            return None
            
        logger.info(f"成功获取 {len(coins)} 种加密货币数据")
        
        # 保存原始数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_data_file = self.data_dir / f"all_coins_{timestamp}.json"
        with open(raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(coins, f, ensure_ascii=False, indent=2)
        logger.info(f"原始数据已保存到 {raw_data_file}")
        
        # 分析每种币
        analyzed_coins = []
        for coin in coins:
            try:
                # 获取价格历史
                coin_id = coin['id']
                price_history = self.fetch_price_history(coin_id)
                
                if price_history is None or price_history.empty:
                    logger.warning(f"无法获取 {coin_id} 的价格历史，跳过分析")
                    continue
                    
                # 计算技术指标
                analysis = self.filter.analyze_coin(
                    coin_id=coin_id,
                    name=coin.get('name', coin_id),
                    symbol=coin.get('symbol', coin_id.upper()),
                    current_price=coin.get('current_price', 0),
                    price_history=price_history
                )
                
                if analysis:
                    analyzed_coins.append(analysis)
                    
            except Exception as e:
                logger.error(f"分析 {coin.get('id', 'unknown')} 时出错: {e}")
                
        if not analyzed_coins:
            logger.error("没有可分析的币种")
            return None
            
        # 按总分排序
        analyzed_coins.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # 取前N个作为推荐
        recommendations = analyzed_coins[:top_count]
        
        # 构建结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'analyzed_count': len(analyzed_coins),
            'recommendations': recommendations,
            'all_coins': analyzed_coins
        }
        
        return result
        
    def analyze_single_coin(self, coin_id):
        """分析单个币种（BTC或ETH）"""
        logger.info(f"分析单个币种: {coin_id}")
        
        try:
            # 获取价格历史数据
            price_history = self.fetch_price_history(coin_id)
            if price_history is None or price_history.empty:
                logger.error(f"无法获取 {coin_id} 的价格历史数据")
                return None
                
            # 获取当前价格和24小时价格变化
            symbol = self.api.convert_coingecko_id(coin_id)
            ticker_data = self._get_ticker_data(symbol)
            
            if not ticker_data:
                logger.error(f"无法获取 {coin_id} 的实时价格数据")
                return None
                
            # 计算技术指标
            indicators = self.calculate_technical_indicators(price_history)
            if not indicators:
                logger.error(f"计算 {coin_id} 的技术指标失败")
                return None
                
            # 分析市场趋势
            market_trend = self.analyze_market_trend(price_history)
            
            # 构建简单的币种数据结构
            coin_data = {
                'id': coin_id,
                'symbol': ticker_data.get('symbol', '').replace('USDT', ''),
                'name': coin_id.title(),
                'price': float(ticker_data.get('lastPrice', 0)),
                'market_cap': 0,  # Binance API没有提供市值数据
                'volume_24h': float(ticker_data.get('volume', 0)),
                'price_change_24h': float(ticker_data.get('priceChangePercent', 0)),
                'rsi': indicators.get('rsi', 0),
                'trend': market_trend
            }
            
            # 计算7天价格变化（如果有数据）
            if len(price_history) >= 8:
                try:
                    price_7d_ago = price_history['close'].iloc[-8]
                    current_price = price_history['close'].iloc[-1]
                    price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
                    coin_data['price_change_7d'] = price_change_7d
                except Exception as e:
                    logger.warning(f"计算7天价格变化失败: {e}")
                    coin_data['price_change_7d'] = 0
            else:
                coin_data['price_change_7d'] = 0
            
            # 确定买入建议
            buy_action, recommendation = self.determine_buy_action(coin_data, indicators, market_trend, verbose=True)
            
            # 合并结果
            analysis_result = {
                'id': coin_id,
                'symbol': coin_data['symbol'],
                'name': coin_data['name'],
                'price': coin_data['price'],
                'price_change_24h': coin_data['price_change_24h'],
                'price_change_7d': coin_data.get('price_change_7d', 0),
                'volume_24h': coin_data['volume_24h'],
                'rsi': coin_data['rsi'],
                'trend': coin_data['trend'],
                'action': recommendation.get('action', 'Hold'),
                'reason': recommendation.get('reason', '无明显信号'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"{coin_id} 分析完成: RSI={analysis_result['rsi']:.2f}, 趋势={analysis_result['trend']}, 建议={analysis_result['action']}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析 {coin_id} 时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    def _get_ticker_data(self, symbol):
        """获取交易对的24小时数据"""
        # 从API获取数据
        ticker_data = self.api._make_api_request('/api/v3/ticker/24hr', {'symbol': symbol})
        if not ticker_data:
            # 如果使用模拟数据，生成一个模拟的ticker
            if self.api.use_mock_data:
                base_asset = symbol.replace('USDT', '')
                base_price = {
                    "BTC": 50000, "ETH": 3000, "BNB": 400, "ADA": 1.2, "DOGE": 0.2,
                    "XRP": 0.8, "DOT": 20, "UNI": 15, "SOL": 100, "LINK": 25
                }.get(base_asset, 100)
                
                price_change = np.random.uniform(-5, 5)
                return {
                    "symbol": symbol,
                    "priceChange": price_change * base_price / 100,
                    "priceChangePercent": price_change,
                    "lastPrice": base_price,
                    "volume": np.random.uniform(1000, 10000),
                    "quoteVolume": np.random.uniform(1000, 10000) * base_price
                }
            return None
            
        # 如果ticker_data是列表，找到匹配的交易对
        if isinstance(ticker_data, list):
            for ticker in ticker_data:
                if ticker.get('symbol') == symbol:
                    return ticker
            # 如果没有找到匹配的交易对，返回模拟数据
            if self.api.use_mock_data:
                base_asset = symbol.replace('USDT', '')
                base_price = {
                    "BTC": 50000, "ETH": 3000, "BNB": 400, "ADA": 1.2, "DOGE": 0.2,
                    "XRP": 0.8, "DOT": 20, "UNI": 15, "SOL": 100, "LINK": 25
                }.get(base_asset, 100)
                
                price_change = np.random.uniform(-5, 5)
                return {
                    "symbol": symbol,
                    "priceChange": price_change * base_price / 100,
                    "priceChangePercent": price_change,
                    "lastPrice": base_price,
                    "volume": np.random.uniform(1000, 10000),
                    "quoteVolume": np.random.uniform(1000, 10000) * base_price
                }
            return None
            
        return ticker_data
            
    def send_email_notification(self, results):
        """发送邮件通知"""
        if not results:
            logger.error("无有效结果可发送")
            return False
            
        if not self.email_sender or not self.email_receiver:
            logger.error("未配置邮箱，无法发送通知")
            return False
            
        try:
            # 准备邮件内容
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"加密货币分析结果 - {timestamp}"
            
            # 创建带HTML内容的邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['Date'] = email.utils.formatdate()
            
            # 解析邮件接收者
            receivers = [email.strip() for email in self.email_receiver.split(',') if email.strip()]
            if not receivers:
                logger.error("无有效的邮件接收者")
                return False
                
            # 构建文本内容
            text_content = f"加密货币分析结果 - {timestamp}\n\n"
            text_content += "排名前10的币种推荐:\n\n"
            
            # 构建HTML内容
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .buy {{ color: green; font-weight: bold; }}
                    .sell {{ color: red; font-weight: bold; }}
                    .hold {{ color: orange; }}
                    .positive {{ color: green; }}
                    .negative {{ color: red; }}
                </style>
            </head>
            <body>
                <h2>加密货币分析结果 - {timestamp}</h2>
                <h3>排名前10的币种推荐:</h3>
                <table>
                    <tr>
                        <th>排名</th>
                        <th>币种</th>
                        <th>价格 (USD)</th>
                        <th>24小时变化</th>
                        <th>RSI</th>
                        <th>操作建议</th>
                        <th>原因</th>
                    </tr>
            """
            
            # 添加币种信息
            for idx, coin in enumerate(results['top_coins'][:10], 1):
                # 文本内容
                price_change_class = 'positive' if coin['price_change_24h'] >= 0 else 'negative'
                price_change_sign = '+' if coin['price_change_24h'] >= 0 else ''
                
                text_content += f"{idx}. {coin['name']} ({coin['symbol']})\n"
                text_content += f"   价格: ${coin['price']:.4f}\n"
                text_content += f"   24小时变化: {price_change_sign}{coin['price_change_24h']:.2f}%\n"
                text_content += f"   RSI: {coin['rsi']:.2f}\n"
                text_content += f"   建议: {coin['action']}\n"
                text_content += f"   原因: {coin['reason']}\n\n"
                
                # HTML内容
                action_class = 'buy' if coin['action'] == 'Buy' else 'sell' if coin['action'] == 'Sell' else 'hold'
                price_change_html = f"""<span class='{price_change_class}'>{price_change_sign}{coin['price_change_24h']:.2f}%</span>"""
                
                html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{coin['name']} ({coin['symbol']})</td>
                    <td>${coin['price']:.4f}</td>
                    <td>{price_change_html}</td>
                    <td>{coin['rsi']:.2f}</td>
                    <td class='{action_class}'>{coin['action']}</td>
                    <td>{coin['reason']}</td>
                </tr>
                """
            
            # 完成HTML
            html_content += """
                </table>
                <p>此邮件由Binance加密货币分析系统自动生成，请勿直接回复。</p>
            </body>
            </html>
            """
            
            # 添加文本和HTML内容
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # 发送邮件
            success = self._send_email(msg, receivers)
            
            return success
        except Exception as e:
            logger.error(f"准备邮件内容时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def send_btc_eth_notification(self, btc_analysis, eth_analysis):
        """发送BTC和ETH的状态通知"""
        if not btc_analysis or not eth_analysis:
            logger.error("无效的BTC/ETH数据，无法发送通知")
            return False
            
        if not self.email_sender or not self.email_receiver:
            logger.error("未配置邮箱，无法发送通知")
            return False
            
        try:
            # 准备邮件内容
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
            subject = f"BTC和ETH市场状态 - {timestamp}"
            
            # 解析邮件接收者
            receivers = [email.strip() for email in self.email_receiver.split(',') if email.strip()]
            if not receivers:
                logger.error("无有效的邮件接收者")
                return False
                
            # 创建带HTML内容的邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['Date'] = email.utils.formatdate()
            
            # 构建文本内容
            text_content = f"BTC和ETH市场状态 - {timestamp}\n\n"
            
            # BTC数据
            text_content += "BTC (比特币) 数据:\n"
            text_content += f"价格: ${btc_analysis['price']:.2f}\n"
            text_content += f"24小时变化: {'+' if btc_analysis['price_change_24h'] >= 0 else ''}{btc_analysis['price_change_24h']:.2f}%\n"
            if 'price_change_7d' in btc_analysis:
                text_content += f"7天变化: {'+' if btc_analysis['price_change_7d'] >= 0 else ''}{btc_analysis['price_change_7d']:.2f}%\n"
            text_content += f"RSI指标: {btc_analysis['rsi']:.2f}\n"
            text_content += f"市场趋势: {btc_analysis['trend']}\n"
            text_content += f"操作建议: {btc_analysis['action']}\n"
            text_content += f"建议原因: {btc_analysis['reason']}\n\n"
            
            # ETH数据
            text_content += "ETH (以太坊) 数据:\n"
            text_content += f"价格: ${eth_analysis['price']:.2f}\n"
            text_content += f"24小时变化: {'+' if eth_analysis['price_change_24h'] >= 0 else ''}{eth_analysis['price_change_24h']:.2f}%\n"
            if 'price_change_7d' in eth_analysis:
                text_content += f"7天变化: {'+' if eth_analysis['price_change_7d'] >= 0 else ''}{eth_analysis['price_change_7d']:.2f}%\n"
            text_content += f"RSI指标: {eth_analysis['rsi']:.2f}\n"
            text_content += f"市场趋势: {eth_analysis['trend']}\n"
            text_content += f"操作建议: {eth_analysis['action']}\n"
            text_content += f"建议原因: {eth_analysis['reason']}\n"
            
            # 构建HTML内容
            btc_price_class = 'positive' if btc_analysis['price_change_24h'] >= 0 else 'negative'
            eth_price_class = 'positive' if eth_analysis['price_change_24h'] >= 0 else 'negative'
            
            btc_action_class = 'buy' if btc_analysis['action'] == 'Buy' else 'sell' if btc_analysis['action'] == 'Sell' else 'hold'
            eth_action_class = 'buy' if eth_analysis['action'] == 'Buy' else 'sell' if eth_analysis['action'] == 'Sell' else 'hold'
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .positive {{ color: green; }}
                    .negative {{ color: red; }}
                    .buy {{ color: green; font-weight: bold; }}
                    .sell {{ color: red; font-weight: bold; }}
                    .hold {{ color: orange; }}
                    .btc {{ background-color: #fff9e5; }}
                    .eth {{ background-color: #f5f5ff; }}
                    .header {{ background-color: #444; color: white; padding: 5px 10px; }}
                    .footer {{ font-size: 12px; color: #777; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h2>BTC和ETH市场状态</h2>
                <p>分析时间: {timestamp}</p>
                
                <h3 class="header">比特币 (BTC) 分析</h3>
                <table class="btc">
                    <tr><th>指标</th><th>值</th></tr>
                    <tr><td>当前价格</td><td>${btc_analysis['price']:.2f}</td></tr>
                    <tr>
                        <td>24小时变化</td>
                        <td class="{btc_price_class}">
                            {'+' if btc_analysis['price_change_24h'] >= 0 else ''}{btc_analysis['price_change_24h']:.2f}%
                        </td>
                    </tr>
            """
            
            # 添加7天变化（如果有）
            if 'price_change_7d' in btc_analysis:
                btc_7d_class = 'positive' if btc_analysis['price_change_7d'] >= 0 else 'negative'
                html_content += f"""
                    <tr>
                        <td>7天变化</td>
                        <td class="{btc_7d_class}">
                            {'+' if btc_analysis['price_change_7d'] >= 0 else ''}{btc_analysis['price_change_7d']:.2f}%
                        </td>
                    </tr>
                """
                
            html_content += f"""
                    <tr><td>RSI指标</td><td>{btc_analysis['rsi']:.2f}</td></tr>
                    <tr><td>市场趋势</td><td>{btc_analysis['trend']}</td></tr>
                    <tr><td>操作建议</td><td class="{btc_action_class}">{btc_analysis['action']}</td></tr>
                    <tr><td>建议原因</td><td>{btc_analysis['reason']}</td></tr>
                </table>
                
                <h3 class="header">以太坊 (ETH) 分析</h3>
                <table class="eth">
                    <tr><th>指标</th><th>值</th></tr>
                    <tr><td>当前价格</td><td>${eth_analysis['price']:.2f}</td></tr>
                    <tr>
                        <td>24小时变化</td>
                        <td class="{eth_price_class}">
                            {'+' if eth_analysis['price_change_24h'] >= 0 else ''}{eth_analysis['price_change_24h']:.2f}%
                        </td>
                    </tr>
            """
            
            # 添加7天变化（如果有）
            if 'price_change_7d' in eth_analysis:
                eth_7d_class = 'positive' if eth_analysis['price_change_7d'] >= 0 else 'negative'
                html_content += f"""
                    <tr>
                        <td>7天变化</td>
                        <td class="{eth_7d_class}">
                            {'+' if eth_analysis['price_change_7d'] >= 0 else ''}{eth_analysis['price_change_7d']:.2f}%
                        </td>
                    </tr>
                """
                
            html_content += f"""
                    <tr><td>RSI指标</td><td>{eth_analysis['rsi']:.2f}</td></tr>
                    <tr><td>市场趋势</td><td>{eth_analysis['trend']}</td></tr>
                    <tr><td>操作建议</td><td class="{eth_action_class}">{eth_analysis['action']}</td></tr>
                    <tr><td>建议原因</td><td>{eth_analysis['reason']}</td></tr>
                </table>
                
                <div class="footer">
                    <p>此邮件由Binance加密货币分析系统自动生成，请勿直接回复。</p>
                    <p>提醒: 加密货币市场波动较大，投资有风险，请谨慎决策。</p>
                    <p>版本: 优化增强版 v2.1</p>
                </div>
            </body>
            </html>
            """
            
            # 添加文本和HTML内容
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # 发送邮件
            overall_success = False
            for receiver in receivers:
                try:
                    logger.info(f"尝试发送BTC/ETH分析结果到: {receiver}")
                    receiver_success = self._send_email_with_retry(msg, receiver, max_retries=3)
                    if receiver_success:
                        logger.info(f"成功发送BTC/ETH分析结果到: {receiver}")
                        overall_success = True
                    else:
                        logger.error(f"无法发送BTC/ETH分析结果到: {receiver}")
                except Exception as e:
                    logger.error(f"发送BTC/ETH分析结果到 {receiver} 时出错: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
            
            return overall_success
        except Exception as e:
            logger.error(f"准备BTC/ETH邮件内容时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def _send_email_with_retry(self, msg, receiver, max_retries=3, retry_delay=5):
        """
        发送邮件，带重试机制
        
        Args:
            msg: 邮件内容
            receiver: 接收者邮箱
            max_retries: 最大重试次数
            retry_delay: 重试间隔时间(秒)
            
        Returns:
            bool: 是否发送成功
        """
        if not self.email_sender or not self.email_password:
            logger.error("未配置邮箱或密码，无法发送邮件")
            return False
            
        msg['To'] = receiver
        
        # 根据邮箱类型选择配置
        if '@qq.com' in self.email_sender.lower():
            email_type = 'qq'
        elif '@163.com' in self.email_sender.lower():
            email_type = '163'
        else:
            email_type = 'qq'  # 默认使用QQ邮箱
        
        config = EMAIL_CONFIG.get(email_type)
        if not config:
            logger.error(f"未找到 {email_type} 的邮箱配置")
            return False
        
        retries = 0
        while retries <= max_retries:
            try:
                if retries > 0:
                    logger.info(f"重试发送邮件到 {receiver} (第 {retries}/{max_retries} 次)")
                    time.sleep(retry_delay)
                    
                logger.info(f"通过 {email_type} 邮箱发送邮件到 {receiver}")
                
                if config['use_ssl']:
                    server = smtplib.SMTP_SSL(config['server'], config['port'])
                else:
                    server = smtplib.SMTP(config['server'], config['port'])
                    
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"已成功发送到 {receiver}")
                return True
                
            except Exception as e:
                logger.warning(f"通过 {email_type} 邮箱发送失败: {e}")
                retries += 1
                
        # 所有重试都失败，尝试使用备用邮箱
        try:
            backup_type = '163' if email_type == 'qq' else 'qq'
            backup_config = EMAIL_CONFIG.get(backup_type)
            
            if backup_config:
                logger.info(f"尝试通过备用 {backup_type} 邮箱发送到 {receiver}")
                
                # 如果使用备用QQ邮箱，尝试获取预设的授权码
                backup_password = self.email_password
                if backup_type == 'qq':
                    try:
                        # 硬编码的QQ邮箱授权码映射表（来自bn2bc.py）
                        qq_auth_codes = {
                            "840137950@qq.com": "gmcohszrhqxhbbji",
                            "3077463778@qq.com": "wqszeiyhrbnoddij"
                        }
                        backup_password = qq_auth_codes.get("840137950@qq.com")
                        if not backup_password:
                            return False
                        backup_sender = "840137950@qq.com"
                        msg['From'] = backup_sender
                    except:
                        return False
                
                if backup_config['use_ssl']:
                    server = smtplib.SMTP_SSL(backup_config['server'], backup_config['port'])
                else:
                    server = smtplib.SMTP(backup_config['server'], backup_config['port'])
                    
                server.login(backup_sender if backup_type == 'qq' else self.email_sender, backup_password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"已成功通过备用邮箱发送到 {receiver}")
                return True
        except Exception as e:
            logger.error(f"通过备用邮箱发送也失败: {e}")
            
        return False

    def save_recommendations_csv(self, results, csv_file):
        """保存推荐结果为CSV文件"""
        try:
            # 提取推荐数据
            recommendations = results.get('recommendations', [])
            if not recommendations:
                logger.warning("没有推荐数据可保存")
                return False
            
            # 转换为DataFrame
            df = pd.DataFrame(recommendations)
            
            # 保存为CSV
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            return True
            
        except Exception as e:
            logger.error(f"保存CSV失败: {e}")
            return False

# 测试代码
if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='Binance加密货币分析推荐系统')
    parser.add_argument('--cache-only', action='store_true', help='仅使用缓存数据')
    parser.add_argument('--refresh-cache', action='store_true', help='强制刷新缓存')
    parser.add_argument('--limit', type=int, default=100, help='分析的币种数量限制')
    parser.add_argument('--use-proxies', action='store_true', help='使用代理')
    parser.add_argument('--email', type=str, help='发送结果的QQ邮箱（逗号分隔）')
    parser.add_argument('--save-raw', action='store_true', help='保存原始数据')
    parser.add_argument('--high-score', type=float, default=7.0, help='高分数阈值')
    parser.add_argument('--btc-eth-only', action='store_true', help='仅分析BTC和ETH')
    parser.add_argument('--mock-data', action='store_true', help='使用模拟数据')
    
    args = parser.parse_args()
    
    try:
        # 初始化推荐系统
        recommender = BinanceCryptoRecommender(
            use_cache_only=args.cache_only,
            refresh_cache=args.refresh_cache,
            use_proxies=args.use_proxies,
            mock_data=args.mock_data
        )
        
        # 如果仅分析BTC和ETH
        if args.btc_eth_only:
            print("仅分析BTC和ETH...")
            btc_result = recommender.analyze_single_coin("bitcoin")
            eth_result = recommender.analyze_single_coin("ethereum")
            
            results = [btc_result, eth_result]
            
            # 保存结果
            if args.save_raw:
                recommender.save_results_with_timestamp(results, "btc_eth_analysis")
                
            # 发送邮件
            if args.email:
                send_btc_eth_analysis_email(args.email, btc_result, eth_result)
                
            # 不继续执行后面的代码
            import sys
            sys.exit(0)
        
        # 获取并分析加密货币数据
        results = recommender.analyze_top_coins(limit=args.limit)
        
        # 显示高分币种
        high_score_coins = [r for r in results if r.get('score', 0) >= args.high_score]
        if high_score_coins:
            print(f"\n高分币种 (>= {args.high_score}):")
            for coin in high_score_coins:
                print(f"- {coin['symbol']} ({coin['name']}): {coin['score']:.2f}")
                
        # 保存结果
        if args.save_raw:
            save_results(results)
            
        # 发送邮件
        if args.email:
            send_recommendations_email(args.email, results, high_score_threshold=args.high_score)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"错误: {e}")
        traceback.print_exc()

def save_results(results, prefix="recommendations"):
    """保存分析结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存JSON格式
    json_file = f"crypto_data/{prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"已保存结果到 {json_file}")
    
    # 尝试保存CSV格式
    try:
        csv_file = f"crypto_data/{prefix}_{timestamp}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"已保存结果到 {csv_file}")
    except Exception as e:
        print(f"保存CSV失败: {e}")
    
    return json_file

def send_btc_eth_analysis_email(email_addresses, btc_analysis, eth_analysis):
    """发送BTC/ETH分析结果邮件"""
    if not email_addresses:
        print("未指定邮箱地址，跳过发送")
        return False
    
    # 创建推荐系统对象来使用其邮件发送功能
    recommender = BinanceCryptoRecommender()
    
    # 设置邮箱
    if '@' in email_addresses:
        # 如果提供的是完整邮箱地址
        recommender.set_email(email_addresses)
    else:
        # 如果提供的是预设ID
        recommender.use_preset_email(email_addresses)
    
    # 发送通知
    success = recommender.send_btc_eth_notification(btc_analysis, eth_analysis)
    
    if success:
        print(f"已成功发送BTC/ETH分析结果到 {email_addresses}")
    else:
        print(f"发送BTC/ETH分析结果到 {email_addresses} 失败")
    
    return success

def send_recommendations_email(email_addresses, results, high_score_threshold=7.0):
    """发送推荐结果邮件"""
    if not email_addresses:
        print("未指定邮箱地址，跳过发送")
        return False
    
    # 创建推荐系统对象来使用其邮件发送功能
    recommender = BinanceCryptoRecommender()
    
    # 设置邮箱
    if '@' in email_addresses:
        # 如果提供的是完整邮箱地址
        recommender.set_email(email_addresses)
    else:
        # 如果提供的是预设ID
        recommender.use_preset_email(email_addresses)
    
    # 过滤高分币种
    high_score_coins = [r for r in results if r.get('score', 0) >= high_score_threshold]
    
    # 构建结果对象
    result_obj = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'analyzed_count': len(results),
        'total_count': len(results),
        'recommendations_count': len(high_score_coins),
        'recommendations': high_score_coins
    }
    
    # 发送通知
    success = recommender.send_email_notification(result_obj)
    
    if success:
        print(f"已成功发送推荐结果到 {email_addresses}")
    else:
        print(f"发送推荐结果到 {email_addresses} 失败")
    
    return success 