@echo off
REM 自动测试SOCKS5代理并生成修复代码

echo 开始测试SOCKS5代理

REM 确认Python和依赖库已安装
python -c "import socks, requests" 2>NUL
if %errorlevel% neq 0 (
    echo 正在安装必要的库...
    pip install pysocks requests
)

REM 测试单一代理
if "%1"=="" (
    echo 用法:
    echo   %0 代理字符串                  - 测试单一代理
    echo   %0 --file 代理文件.txt         - 测试文件中的多个代理
    echo   例如: %0 123.123.123.123:1080:username:password
    goto end
) else (
    if "%1"=="--file" (
        if "%2"=="" (
            echo 错误: 必须指定代理文件
            goto end
        )
        echo 测试文件 %2 中的代理...
        python bn_pro/fix_socks5_proxy.py --file "%2" --fix --debug
    ) else (
        echo 测试代理: %1
        python bn_pro/fix_socks5_proxy.py --proxy "%1" --fix --debug
    )
)

REM 检查是否生成了修复代码
if exist socks5_proxy_fix.py (
    echo.
    echo 修复代码已生成到 socks5_proxy_fix.py
    echo 测试修复代码...
    python socks5_proxy_fix.py
) else (
    echo 未能生成修复代码，代理可能无法使用
)

:end
pause 