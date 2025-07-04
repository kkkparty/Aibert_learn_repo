@echo off
echo =====================================================
echo Binance BTC/ETH 分析系统 - 强制真实API测试
echo =====================================================
echo 此脚本将强制使用真实的Binance API数据运行分析
echo 将分析BTC和ETH，并发送邮件通知
echo.

REM 设置环境变量
set EMAIL=840137950@qq.com,3077463778@qq.com

REM 显示运行信息
echo 测试配置:
echo - 两个邮箱接收通知: %EMAIL%
echo - 单次分析，完成后退出
echo - 强制使用真实API数据
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
python continuous_binance_crypto.py --hours 0.01 --interval 1 --email %EMAIL% --btc-eth-only --force-real-api --log-level DEBUG

echo.
echo 测试完成 - %DATE% %TIME%
echo 日志文件保存在logs目录中
echo.
echo 按任意键退出
pause 