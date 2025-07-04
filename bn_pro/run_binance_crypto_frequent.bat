@echo off
echo Starting Binance cryptocurrency frequent analysis system...
echo Will run continuously for 12 hours, analyzing every 5 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Frequent analysis (12 hours, 5 minute interval, 50 coins)
python continuous_binance_crypto.py --hours 12 --interval 5 --limit 50 --email %EMAIL%

echo Program execution completed
pause 