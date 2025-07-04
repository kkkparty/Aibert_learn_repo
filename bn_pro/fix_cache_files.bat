@echo off
echo =====================================================
echo Binance 加密货币分析系统 - 缓存文件修复工具
echo =====================================================
echo 此工具将修复缓存文件中的编码问题和null字节
echo 原文件将备份为.bak文件

REM 检查Python环境
python --version
if %ERRORLEVEL% neq 0 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python并确保其在系统PATH中
    pause
    exit /b 1
)

REM 确保crypto_data目录存在
if not exist crypto_data (
    echo 警告: crypto_data目录不存在，将创建空目录
    mkdir crypto_data
)

REM 运行修复脚本
echo 开始修复 - %DATE% %TIME%
python fix_encoding.py

echo.
echo 修复完成 - %DATE% %TIME%
echo 请查看上面的日志以确认修复结果

pause 