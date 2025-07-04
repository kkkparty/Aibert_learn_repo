@echo off
echo =====================================================
echo Binance API 高级连接测试
echo =====================================================
echo 此工具将测试多种方法访问Binance API:
echo 1. 测试替代域名
echo 2. 测试多个代理服务器
echo.

REM 检查Python环境
python --version
if %ERRORLEVEL% neq 0 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python并确保其在系统PATH中
    pause
    exit /b 1
)

REM 运行测试脚本
echo 开始测试 - %DATE% %TIME%
python test_binance_api_proxy.py

echo.
echo 测试完成 - %DATE% %TIME%
echo.

pause 