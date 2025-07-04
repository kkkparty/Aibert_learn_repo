@echo off
echo =====================================================
echo Binance BTC/ETH 分析系统测试脚本 (优化版)
echo =====================================================
echo 此脚本用于测试BTC和ETH分析系统的可靠性和稳定性
echo 将使用两个QQ邮箱，运行时间较短
echo.

REM 设置环境变量
set EMAIL=840137950@qq.com,3077463778@qq.com

REM 显示运行信息
echo 测试配置:
echo - 两个邮箱接收通知: %EMAIL%
echo - 运行时间: 30分钟
echo - 分析间隔: 5分钟
echo - 启用日志保存: logs目录
echo.

REM 检查Python环境
python --version
if %ERRORLEVEL% neq 0 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python并确保其在系统PATH中
    pause
    exit /b 1
)

REM 确保logs目录存在
if not exist logs mkdir logs

REM 运行脚本
echo 开始测试 - %DATE% %TIME%
echo.
python continuous_binance_crypto.py --hours 0.5 --interval 5 --email %EMAIL% --btc-eth-only --log-level DEBUG

echo.
echo 测试完成 - %DATE% %TIME%
echo 日志文件保存在logs目录中
echo.
echo 按任意键退出
pause 