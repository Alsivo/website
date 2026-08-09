@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Atlas Daily Automation
echo Started: %date% %time%
echo ========================================

".venv\Scripts\python.exe" atlas.py

set ATLAS_EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Atlas main process finished
echo Exit code: %ATLAS_EXIT_CODE%
echo ========================================

echo.
echo Running Atlas Health Check...

".venv\Scripts\python.exe" -m engines.atlas_health

set HEALTH_EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Atlas Daily Automation finished
echo Atlas exit code: %ATLAS_EXIT_CODE%
echo Health exit code: %HEALTH_EXIT_CODE%
echo Finished: %date% %time%
echo ========================================

if not "%ATLAS_EXIT_CODE%"=="0" (
    exit /b %ATLAS_EXIT_CODE%
)

exit /b %HEALTH_EXIT_CODE%