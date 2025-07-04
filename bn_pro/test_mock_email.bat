@echo off
echo Testing Binance cryptocurrency analysis with mock data and email...
echo This will run a quick test with mock data and try to send emails

:: Set QQ email password as environment variable (replace with actual password)
set QQ_EMAIL_PASSWORD=your_password_here

:: Run a quick test (0.01 hours = ~36 seconds)
python continuous_binance_crypto_new_fixed.py --hours 0.01 --interval 1 --coins 2 --mock-data --email 840137950@qq.com

echo Test completed
pause 