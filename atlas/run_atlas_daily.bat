@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Atlas Daily Automation
echo Started: %date% %time%
echo ========================================

".venv\Scripts\python.exe" atlas.py

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Atlas finished
echo Exit code: %EXIT_CODE%
echo Finished: %date% %time%
echo ========================================

exit /b %EXIT_CODE%