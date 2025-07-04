@echo off
echo Starting Binance BTC/ETH analysis (MOCK DATA MODE)...
echo Will run continuously for 24 hours, analyzing every 5 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: BTC and ETH analysis with mock data (24 hours, 5 minute interval, minimal coins)
python continuous_binance_crypto_new_fixed.py --hours 24 --interval 5 --coins 2 --email %EMAIL% --mock-data

echo Program execution completed
pause 