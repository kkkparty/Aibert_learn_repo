@echo off
echo Running single BTC/ETH analysis and sending email notification...

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Single BTC and ETH analysis
python continuous_binance_crypto.py --hours 0.01 --interval 1 --email %EMAIL% --btc-eth-only

echo Analysis completed
pause 