#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
def get_env_or_default(key, default=None):
    """从环境变量获取配置，如果不存在则返回默认值"""
    value = os.environ.get(key, default)
    return value

# Email 配置
EMAIL_CONFIG = {
    'qq': {
        'server': 'smtp.qq.com',
        'port': 465,
        'use_ssl': True,
        'username': get_env_or_default('QQ_EMAIL_USERNAME', '840137950@qq.com'),
        'password': get_env_or_default('QQ_EMAIL_PASSWORD', 'your_password_here')
    },
    '163': {
        'server': 'smtp.163.com',
        'port': 25,
        'use_ssl': False,
        'username': get_env_or_default('163_EMAIL_USERNAME', 'your_email@163.com'),
        'password': get_env_or_default('163_EMAIL_PASSWORD', 'your_password_here')
    }
}

# 邮箱预设配置
EMAIL_PRESETS = {
    1: {
        'sender': '840137950@qq.com',
        'password': get_env_or_default('QQ_EMAIL_PASSWORD', 'your_password_here'),
        'receiver': '840137950@qq.com'
    },
    2: {
        'sender': '3077463778@qq.com',
        'password': get_env_or_default('QQ_EMAIL_PASSWORD', 'your_password_here'),
        'receiver': '3077463778@qq.com'
    }
}

# Binance API 配置
BINANCE_API = {
    'api_key': get_env_or_default('BINANCE_API_KEY', ''),
    'api_secret': get_env_or_default('BINANCE_API_SECRET', ''),
    'use_testnet': get_env_or_default('BINANCE_USE_TESTNET', 'false').lower() == 'true'
}

# 数据目录配置
DATA_DIR = 'crypto_data'

# 技术分析配置
TECHNICAL_ANALYSIS = {
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bollinger_period': 20,
    'bollinger_std': 2
}

# 系统默认设置
DEFAULT_SETTINGS = {
    'coins_to_analyze': 100,
    'top_recommendations': 10,
    'analysis_interval_minutes': 15,
    'run_duration_hours': 24,
    'cache_expiry_hours': 24,
    'use_proxies': False
}

# 打印配置信息
def print_config_info():
    """打印配置信息（隐藏敏感信息）"""
    print("\n=== 系统配置信息 ===")
    print(f"数据目录: {DATA_DIR}")
    print(f"默认分析币种数量: {DEFAULT_SETTINGS['coins_to_analyze']}")
    print(f"默认推荐数量: {DEFAULT_SETTINGS['top_recommendations']}")
    print(f"默认分析间隔(分钟): {DEFAULT_SETTINGS['analysis_interval_minutes']}")
    print(f"默认运行时间(小时): {DEFAULT_SETTINGS['run_duration_hours']}")
    print(f"缓存有效期(小时): {DEFAULT_SETTINGS['cache_expiry_hours']}")
    
    # 邮箱配置
    if EMAIL_PRESETS[1]['password'] != 'your_password_here':
        print("预设QQ邮箱: 已配置")
    else:
        print("预设QQ邮箱: 未配置 (需要设置QQ_EMAIL_PASSWORD环境变量)")
        
    # Binance API配置
    if BINANCE_API['api_key']:
        print("Binance API: 已配置")
    else:
        print("Binance API: 未配置 (需要设置BINANCE_API_KEY和BINANCE_API_SECRET环境变量)")
    
    print("=====================\n")

if __name__ == "__main__":
    # 如果直接运行此文件，打印配置信息
    print_config_info() 