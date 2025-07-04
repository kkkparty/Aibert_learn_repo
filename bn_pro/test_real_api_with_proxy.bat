@echo off
echo Binance加密货币分析系统 - 使用代理进行真实API测试
echo ============================================

:: 设置代理环境变量（请替换为您的代理地址）
set HTTP_PROXY=http://your_proxy_server:port
set HTTPS_PROXY=http://your_proxy_server:port

:: 显示当前代理设置
echo 当前代理设置:
echo HTTP_PROXY=%HTTP_PROXY%
echo HTTPS_PROXY=%HTTPS_PROXY%
echo.

:: 测试网络连接
echo 1. 测试网络连接...
python test_real_api.py --network-only --use-proxy
echo.

:: 测试API连接
echo 2. 测试API连接...
python test_real_api.py --api-only --use-proxy
echo.

:: 运行完整测试
echo 3. 运行完整测试...
python test_real_api.py --use-proxy
echo.

echo 测试完成！
pause 