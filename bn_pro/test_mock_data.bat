@echo off
echo Testing Binance cryptocurrency analysis with mock data...
echo This will run a quick test with mock data

:: Run a quick test (0.01 hours = ~36 seconds)
python continuous_binance_crypto_new_fixed.py --hours 0.01 --interval 1 --coins 2 --mock-data

echo Test completed
pause 