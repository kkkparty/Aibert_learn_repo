@echo off
echo Testing Binance crypto analysis system...

:: Set Python path (modify if python is not in PATH)
set PYTHON=python

:: Use configured QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Run mock data test first
echo.
echo === Running mock data test ===
%PYTHON% test_mock_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Mock data test failed!
    goto end
)

echo.
echo === Running BTC/ETH analysis (mock data mode) ===
:: Start testing program with mock data mode and short runtime
%PYTHON% continuous_binance_crypto.py --mock-data --cache-only --email %EMAIL% --hours 0.05 --interval 1 --btc-eth-only

:end
echo.
echo Test completed
pause 