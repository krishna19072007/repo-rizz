@echo off
cd /d "%~dp0"

echo Starting Repo Rizz Python Backend...
echo.

python -m uvicorn main:app --reload --port 8000

echo.
echo Backend stopped.
pause