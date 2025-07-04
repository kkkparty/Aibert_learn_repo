@echo off
echo Starting crypto data collection and analysis task: %date% %time%
:: Wait for Python execution to complete
CALL python bn2bc.py --coins 500 --save-raw --qq-email 840137950@qq.com,3077463778@qq.com --high-score 50 --refresh-cache

:: Check if Python executed successfully
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python script failed with error code %ERRORLEVEL%
    echo System will NOT shutdown due to error.
    echo Press any key to exit...
    pause > nul
    exit /b %ERRORLEVEL%
 )
 echo Task completed successfully: %date% %time%
 :: Add a pause to show execution results
 echo Data collection completed. System will shutdown in 30 seconds.
 echo Press Ctrl+C and then Y to cancel shutdown, or run 'shutdown /a' in another command prompt.
 timeout /t 30
 shutdown /s /t 60 /c "Crypto data collection completed. System will shutdown in 60 seconds." 