@echo off
echo Starting Binance BTC/ETH analysis (FIXED VERSION)...
echo Will run continuously for 24 hours, analyzing every 5 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: BTC and ETH analysis (24 hours, 5 minute interval, minimal coins)
python continuous_binance_crypto_new_fixed.py --hours 24 --interval 5 --coins 2 --email %EMAIL%

echo Program execution completed
pause 