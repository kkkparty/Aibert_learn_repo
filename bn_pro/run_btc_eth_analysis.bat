@echo off
echo Starting Binance BTC/ETH analysis system...
echo Will run continuously for 24 hours, analyzing every 5 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: BTC and ETH specific analysis (24 hours, 5 minute interval)
python continuous_binance_crypto.py --hours 24 --interval 5 --email %EMAIL% --btc-eth-only

echo Program execution completed
pause 