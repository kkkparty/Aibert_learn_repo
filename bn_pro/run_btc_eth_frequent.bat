@echo off
echo =====================================================
echo Binance BTC/ETH 频繁分析系统 (优化版)
echo =====================================================
echo 将持续运行12小时，每1分钟分析一次
echo 使用两个QQ邮箱接收通知
echo 按Ctrl+C可随时停止程序

:: 设置环境变量
set EMAIL=840137950@qq.com,3077463778@qq.com

:: 确保logs目录存在
if not exist logs mkdir logs

:: 显示运行信息
echo.
echo 运行配置:
echo - 两个邮箱接收通知: %EMAIL%
echo - 运行时间: 12小时
echo - 分析间隔: 1分钟
echo - 启用日志保存: logs目录
echo - 重试机制: 出错自动重试3次
echo.

:: 运行BTC和ETH频繁分析
echo 开始分析 - %DATE% %TIME%
python continuous_binance_crypto.py --hours 12 --interval 1 --email %EMAIL% --btc-eth-only --retry-interval 1 --max-retries 3 --log-level INFO

echo.
echo 分析结束 - %DATE% %TIME%
echo 日志文件保存在logs目录中

pause 