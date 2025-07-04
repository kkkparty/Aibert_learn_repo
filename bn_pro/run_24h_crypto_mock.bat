@echo off
echo Starting 24/7 Binance BTC/ETH monitoring system (MOCK DATA MODE)...
echo This script will run continuously, restarting every 24 hours
echo Press Ctrl+C to stop the program

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:loop
echo.
echo [%date% %time%] Starting new 24-hour monitoring cycle...
echo.

:: Run BTC/ETH analysis with mock data for 24 hours, 5 minute interval
python continuous_binance_crypto_new_fixed.py --hours 24 --interval 5 --coins 2 --email %EMAIL% --mock-data

echo.
echo [%date% %time%] 24-hour cycle completed, restarting...
echo.

:: Wait 5 seconds before restarting
timeout /t 5
goto loop 