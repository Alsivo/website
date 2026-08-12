@echo off
chcp 65001 >nul

cd /d C:\Users\hkimu\Documents\GitHub\website\atlas

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

"C:\Users\hkimu\Documents\GitHub\website\atlas\.venv\Scripts\python.exe" atlas.py --dry-run

exit /b %ERRORLEVEL%