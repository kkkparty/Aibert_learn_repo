@echo off
echo =====================================================
echo Binance BTC/ETH 快速分析 (精简版)
echo =====================================================
echo 仅分析BTC和ETH，发送到两个QQ邮箱
echo 使用模拟数据模式，无需API访问
echo.

:: 设置环境变量
set EMAIL=840137950@qq.com,3077463778@qq.com

:: 确保logs目录存在
if not exist logs mkdir logs

:: 显示运行信息
echo 运行配置:
echo - 两个邮箱接收通知: %EMAIL%
echo - 使用模拟数据模式
echo - 单次分析，完成后退出
echo - 简化日志输出
echo.

:: 运行BTC和ETH分析，使用模拟数据
echo 开始分析 - %DATE% %TIME%
python continuous_binance_crypto.py --hours 0.01 --interval 1 --email %EMAIL% --btc-eth-only --mock-data --log-level INFO

echo.
echo 分析结束 - %DATE% %TIME%
echo.
echo 按任意键退出
pause 