@echo off
echo Starting 24/7 Binance BTC/ETH analysis system...
echo This will run continuously and restart every 24 hours
echo Press Ctrl+C to stop the program

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:loop
echo.
echo ======================================================
echo Starting new 24-hour analysis cycle at %time% on %date%
echo ======================================================
echo.

:: Run BTC/ETH analysis for 24 hours with 5-minute intervals
python continuous_binance_crypto.py --hours 24 --interval 5 --email %EMAIL% --btc-eth-only

echo.
echo ======================================================
echo 24-hour cycle completed, restarting...
echo ======================================================
echo.

:: Wait 5 seconds before restarting
timeout /t 5 /nobreak > nul
goto loop 