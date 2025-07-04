@echo off
echo =====================================================
echo Binance API 连接测试
echo =====================================================
echo 此工具将测试是否能成功连接到Binance API
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
python test_binance_api.py

echo.
echo 测试完成 - %DATE% %TIME%
echo.

REM 根据测试结果提供建议
echo 如果测试成功，您可以使用以下批处理文件运行系统:
echo - run_btc_eth_continuous.bat  (持续分析BTC和ETH，每30分钟一次)
echo - run_btc_eth_frequent.bat    (高频分析BTC和ETH，每分钟一次)
echo.
echo 如果测试失败，您可以使用以下批处理文件(使用模拟数据):
echo - run_btc_eth_minimal.bat     (使用模拟数据分析BTC和ETH)
echo.

pause 