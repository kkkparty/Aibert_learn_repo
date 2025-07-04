@echo off
echo Starting Binance cryptocurrency analysis system (NEW VERSION)...
echo Will run continuously for 24 hours, analyzing every 15 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Standard analysis (24 hours, 15 minute interval, 100 coins)
python continuous_binance_crypto_new.py --hours 24 --interval 15 --limit 100 --email %EMAIL%

echo Program execution completed
pause 