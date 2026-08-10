@echo off
setlocal

cd /d "%~dp0"

call run_atlas_daily.bat

exit /b %ERRORLEVEL%