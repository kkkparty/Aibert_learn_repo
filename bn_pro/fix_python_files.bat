@echo off
echo 正在修复Python文件中的null bytes问题...

:: 首先尝试直接修复已知问题文件
echo 修复已知问题文件...
python fix_null_bytes.py binance_crypto_recommender.py
python fix_null_bytes.py continuous_binance_crypto.py

:: 然后修复所有Python文件
echo 检查所有Python文件...
python fix_null_bytes.py

echo 修复完成！按任意键运行测试...
pause

:: 运行测试确认是否修复成功
echo 运行测试...
python -c "print('测试Python是否能正确导入:'); import binance_crypto_recommender; print('导入成功!');"

echo 修复过程完成
pause 