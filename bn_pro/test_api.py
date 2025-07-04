import requests
import time

def test_coingecko_api():
    print("测试CoinGecko API连接...")
    try:
        response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
        if response.status_code == 200:
            print(f"API正常响应! 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return True
        else:
            print(f"API响应异常. 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"连接错误: {e}")
        return False

if __name__ == "__main__":
    # 测试基本连接
    test_coingecko_api()
    
    # 测试市场数据接口
    print("\n测试市场数据接口...")
    try:
        # 使用较小的请求参数测试
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 5,  # 只请求5个币种
            'page': 1
        }
        
        print("正在请求数据...")
        start_time = time.time()
        response = requests.get("https://api.coingecko.com/api/v3/coins/markets", params=params, timeout=30)
        end_time = time.time()
        
        print(f"请求耗时: {end_time - start_time:.2f} 秒")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取数据! 获取了 {len(data)} 条记录")
            print("示例数据:")
            if data and len(data) > 0:
                print(f"第一个币种: {data[0]['name']} ({data[0]['symbol'].upper()})")
                print(f"当前价格: ${data[0]['current_price']}")
        else:
            print(f"请求失败. 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}") 