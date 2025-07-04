@echo off
echo =====================================================
echo Binance BTC/ETH 持续分析系统 (优化版)
echo =====================================================
echo 将持续运行24小时，每30分钟分析一次
echo 使用两个QQ邮箱接收通知
echo 按Ctrl+C可随时停止程序
echo.

:: 设置环境变量
set EMAIL=840137950@qq.com,3077463778@qq.com

:: 确保logs目录存在
if not exist logs mkdir logs

:: 显示运行信息
echo 运行配置:
echo - 两个邮箱接收通知: %EMAIL%
echo - 运行时间: 24小时
echo - 分析间隔: 30分钟
echo - 启用日志保存: logs目录
echo - 重试机制: 出错自动重试3次
echo - 缓存模式: 优先使用缓存
echo.

:: 检查是否有网络连接
ping -n 1 api.binance.com >nul 2>nul
if %errorlevel% equ 0 (
    echo 网络连接正常，使用API模式运行
    set USE_MOCK=
) else (
    echo 无法连接Binance API，将使用模拟数据模式
    set USE_MOCK=--mock-data
)

:: 运行BTC和ETH分析
echo 开始分析 - %DATE% %TIME%
python continuous_binance_crypto.py --hours 24 --interval 30 --email %EMAIL% --btc-eth-only --retry-interval 2 --max-retries 3 --log-level INFO %USE_MOCK%

echo.
echo 分析结束 - %DATE% %TIME%
echo 日志文件保存在logs目录中

pause 