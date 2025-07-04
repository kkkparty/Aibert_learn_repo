@echo off
echo Binance加密货币分析系统 - 功能测试
echo ============================================

:: 运行模拟数据生成器测试
echo 1. 测试模拟数据生成器...
python test_mock_data.py
echo.

:: 运行系统功能测试
echo 2. 测试系统功能...
python test_all_features.py
echo.

:: 测试中文编码
echo 3. 测试中文编码...
python -c "print('中文编码测试: 这是一段中文文本，包含特殊字符：！@#￥%……&*（）')"
echo.

echo 测试完成！
pause 