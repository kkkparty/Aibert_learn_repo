import requests
import time
import logging
from datetime import datetime, timedelta
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CoinGecko API 的基础 URL
COINGECKO_API = "https://api.coingecko.com/api/v3"

class CryptoRecommender:
    def __init__(self, target_profit: float = 0.20, max_hold_days: int = 7):
        """初始化推荐系统"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.recommendations = {}
        self.holdings = {}
        self.target_profit = target_profit
        self.max_hold_days = max_hold_days
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def fetch_coin_data(self):
        """从 CoinGecko 获取币种市场数据，并打印调试信息"""
        try:
            url = f"{COINGECKO_API}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h,7d'
            }
            print(f"正在请求 API: {url}，参数: {params}")
            response = self.session.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            coins = response.json()
            print(f"API 返回的数据长度: {len(coins)}")
            if len(coins) == 0:
                print("API 返回空数据，可能的原因：API 限制、网络问题或服务器无响应")
            else:
                print(f"前 3 个币种示例: {coins[:3]}")  # 打印前 3 个币种的数据

            # 筛选市值小于 1 亿美元的币种
            filtered_coins = [coin for coin in coins if coin.get('market_cap') < 100_000_000]
            print(f"筛选条件：市值 < 1 亿美元")
            print(f"筛选后符合条件的币种数量: {len(filtered_coins)}")
            if len(filtered_coins) == 0 and len(coins) > 0:
                print("筛选后无符合条件的币种，可能是所有币种市值都超过 1 亿美元")
                # 打印前几个币种的市值，检查筛选逻辑
                print(f"前 3 个币种的市值: {[coin.get('market_cap') for coin in coins[:3]]}")

            time.sleep(10)  # 等待 10 秒，避免频率限制
            return filtered_coins
        except requests.RequestException as e:
            logger.error(f"无法获取 CoinGecko 市场数据: {e}")
            print(f"请求失败，错误信息: {e}")
            return []

    def fetch_price_history(self, coin_id: str, days: int = 7):
        """获取指定币种的 7 天价格历史"""
        try:
            url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
            params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
            response = self.session.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            time.sleep(10)
            return [price[1] for price in data['prices']]
        except requests.RequestException as e:
            logger.error(f"无法获取 {coin_id} 的价格历史: {e}")
            return []

    def calculate_rsi(self, prices, period: int = 7):
        """计算 RSI（相对强弱指数）"""
        if len(prices) < period:
            return None
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def generate_recommendations(self, current_date):
        """生成每日买入推荐并跟踪持仓"""
        coins = self.fetch_coin_data()
        if not coins:
            print("没有获取到任何币种数据，跳过推荐生成")
            return
        for coin in coins[:5]:
            symbol = coin['symbol'].upper()
            if symbol in self.holdings:
                continue

            current_price = coin['current_price']
            price_change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
            volume_24h = coin.get('total_volume', 0)
            prices = self.fetch_price_history(coin['id'])
            rsi = self.calculate_rsi(prices) if prices else None

            action, reason = self.determine_buy_action(price_change_7d, rsi, volume_24h)
            print(f"{symbol} 的推荐: {action}, 原因: {reason}")
            if action == "买入":
                self.holdings[symbol] = {
                    'name': coin['name'],
                    'buy_price': current_price,
                    'buy_date': current_date,
                    'rsi': rsi,
                    'volume_24h': volume_24h,
                    'status': '持有'
                }
                self.recommendations[symbol] = {
                    'name': coin['name'],
                    'price': current_price,
                    'price_change_7d': price_change_7d,
                    'rsi': rsi,
                    'volume_24h': volume_24h,
                    'action': action,
                    'reason': reason,
                    'buy_time': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'sell_time': '待定'
                }

    def determine_buy_action(self, price_change_7d, rsi, volume_24h):
        """决定是否买入（放宽后的条件）"""
        if rsi is None:
            return "持有", "缺少足够数据计算 RSI"
        if price_change_7d > 2 and rsi < 75 and volume_24h > 50_000:
            return "买入", f"7 天涨幅 {price_change_7d:.2f}%，RSI {rsi:.2f} 未超买，交易量活跃"
        return "持有", f"7 天涨幅 {price_change_7d:.2f}%，RSI {rsi:.2f}，条件未满足"

    def check_sell_conditions(self, current_date):
        """检查持仓是否满足卖出条件"""
        for symbol, holding in list(self.holdings.items()):
            if holding['status'] != '持有':
                continue

            coin_data = next((c for c in self.fetch_coin_data() if c['symbol'].upper() == symbol), None)
            if not coin_data:
                continue

            current_price = coin_data['current_price']
            prices = self.fetch_price_history(coin_data['id'])
            rsi = self.calculate_rsi(prices) if prices else holding['rsi']
            days_held = (current_date - holding['buy_date']).days
            profit = (current_price - holding['buy_price']) / holding['buy_price']

            if profit >= self.target_profit:
                reason = f"收益率达 {profit*100:.2f}%，超过目标 {self.target_profit*100}%"
                sell_time = current_date
            elif rsi is not None and rsi > 70:
                reason = f"RSI {rsi:.2f} 超买，可能回调"
                sell_time = current_date
            elif days_held >= self.max_hold_days:
                reason = f"持有 {days_held} 天，未达目标，超时卖出"
                sell_time = current_date
            else:
                continue

            holding['status'] = '已卖出'
            holding['sell_price'] = current_price
            holding['sell_date'] = sell_time
            if symbol in self.recommendations:
                self.recommendations[symbol].update({
                    'action': '卖出',
                    'reason': reason,
                    'sell_time': sell_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'profit': profit
                })

    def print_report(self, current_date):
        """打印报告到控制台"""
        if not self.recommendations:
            print(f"日期: {current_date.strftime('%Y-%m-%d')}\n暂无推荐或持仓更新")
            return

        print(f"日期: {current_date.strftime('%Y-%m-%d')}\n===== 每日加密货币推荐和持仓状态 =====")
        for symbol, info in self.recommendations.items():
            print(f"币种: {symbol} ({info['name']})")
            print(f"当前价格: ${info['price']:.2f}")
            print(f"7 天涨幅: {info['price_change_7d']:.2f}%")
            print(f"RSI: {info['rsi']:.2f if info['rsi'] else 'N/A'}")
            print(f"24 小时交易量: ${info['volume_24h']:,.2f}")
            print(f"建议: {info['action']}")
            print(f"原因: {info['reason']}")
            print(f"买入时间: {info['buy_time']}")
            print(f"卖出时间: {info['sell_time']}")
            if 'profit' in info:
                print(f"收益率: {info['profit']*100:.2f}%")
            print("-------------------")

    def simulate_daily_reminders(self, days: int = 7):
        """模拟多天提醒并打印报告"""
        current_date = datetime.now()  # 使用当前日期
        for _ in range(days):
            logger.info(f"\n模拟日期: {current_date.strftime('%Y-%m-%d')}")
            self.generate_recommendations(current_date)
            self.check_sell_conditions(current_date)
            self.print_report(current_date)
            current_date += timedelta(days=1)
            time.sleep(10)

def main():
    recommender = CryptoRecommender(target_profit=0.20, max_hold_days=7)
    logger.info("开始模拟 7 天加密货币推荐和交易提醒，并打印报告...")
    recommender.simulate_daily_reminders(days=7)

if __name__ == "__main__":
    main()