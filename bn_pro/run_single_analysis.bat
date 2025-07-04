@echo off
echo Running single Binance cryptocurrency analysis...
echo This will analyze the market once and send results via email

:: Use both QQ email addresses
set EMAIL=840137950@qq.com,3077463778@qq.com

:: Run a single analysis (100 coins)
python binance_crypto_recommender.py --limit 100 --refresh-cache --save-raw --email %EMAIL% --high-score 40

echo Analysis completed
pause 