@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ========================================
echo Atlas Daily Automation
echo Started: %date% %time%
echo ========================================

".venv\Scripts\python.exe" atlas.py

set ATLAS_EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Atlas Daily Automation finished
echo Exit code: %ATLAS_EXIT_CODE%
echo Finished: %date% %time%
echo ========================================

exit /b %ATLAS_EXIT_CODE%