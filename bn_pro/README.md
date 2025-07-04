# Binance 加密货币分析系统

这是一个使用Binance API的加密货币分析系统，可以分析各种加密货币并提供技术分析和推荐。

## 主要功能

- 从Binance API获取实时加密货币数据
- 计算RSI、MACD和布林带等技术指标
- 提供买入/卖出推荐
- 支持BTC和ETH的定期状态通知
- 自动生成分析报告和推荐
- 支持邮件通知
- 缓存机制，避免过多API请求
- 代理支持和模拟数据模式

## 系统架构

- **binance_api_adapter.py**: Binance API适配器，处理API请求和数据格式转换
- **binance_crypto_recommender.py**: 加密货币分析和推荐系统的核心逻辑
- **binance_filter.py**: 技术分析过滤器
- **continuous_binance_crypto.py**: 持续运行分析的主程序
- **mock_data_generator.py**: 模拟数据生成器，用于测试或无法访问API的环境
- **config.py**: 系统配置文件

## 运行脚本

系统提供了多个批处理文件用于不同场景：

- **run_btc_eth_continuous.bat**: 持续运行BTC和ETH分析，每30分钟一次，运行24小时
- **run_btc_eth_frequent.bat**: 高频BTC和ETH分析，每分钟一次，运行12小时
- **run_btc_eth_minimal.bat**: 快速单次BTC和ETH分析，使用模拟数据
- **test_btc_eth_fixed.bat**: 用于测试系统的批处理文件
- **run_binance_crypto.bat**: 分析多种加密货币并生成推荐

## 优化功能

最新版本包含以下优化:

- **增强的邮件可靠性**: 支持同时发送到多个邮箱，增加重试机制
- **改进的缓存处理**: 修复null bytes和编码问题，提高缓存读写可靠性
- **内存管理**: 优化长时间运行的内存使用
- **完善的日志系统**: 同时输出到控制台和日志文件
- **强大的错误处理**: 自动重试失败的API请求和分析
- **网络检测**: 自动检测网络连接状况，在无法访问API时切换到模拟数据模式

## 使用方法

### BTC和ETH分析

要运行BTC和ETH的定期分析:

```
run_btc_eth_continuous.bat
```

对于高频分析:

```
run_btc_eth_frequent.bat
```

对于快速测试:

```
run_btc_eth_minimal.bat
```

### 邮件通知

系统支持两个预设QQ邮箱:
- 840137950@qq.com
- 3077463778@qq.com

这些邮箱配置在批处理文件中，可以根据需要修改。

### 命令行参数

系统支持多种命令行参数:

```
python continuous_binance_crypto.py --help
```

主要参数包括:
- `--hours`: 运行时间（小时）
- `--interval`: 分析间隔（分钟）
- `--email`: 接收邮件通知的邮箱地址
- `--btc-eth-only`: 仅分析BTC和ETH
- `--mock-data`: 使用模拟数据模式
- `--log-level`: 设置日志级别
- `--retry-interval`: API请求失败重试间隔
- `--max-retries`: API请求最大重试次数

## 数据存储

- 分析结果保存在`crypto_data`目录中
- 日志文件保存在`logs`目录中
- 缓存数据保存在`crypto_data/cache`目录中

## 模拟数据模式

当无法访问Binance API时，系统可以使用模拟数据模式运行。使用`--mock-data`参数启用此模式:

```
python continuous_binance_crypto.py --btc-eth-only --mock-data
```

## 注意事项

- 对于长时间运行，建议使用间隔较长的分析频率，以避免API限制
- 确保Python环境中安装了必要的依赖库
- 监控日志文件以排查可能的问题 