@echo off
echo Starting Binance cryptocurrency analysis system (MOCK DATA MODE)...
echo Will run continuously for 24 hours, analyzing every 15 minutes
echo Press Ctrl+C to stop the program at any time

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Standard analysis with mock data (24 hours, 15 minute interval, 100 coins)
python continuous_binance_crypto_new_fixed.py --hours 24 --interval 15 --coins 100 --email %EMAIL% --mock-data

echo Program execution completed
pause 