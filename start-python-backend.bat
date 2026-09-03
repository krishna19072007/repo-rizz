@echo off
cd /d "%~dp0python-backend"

echo Starting Repo Rizz Python Backend...
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8001 --no-proxy-headers

echo.
echo Backend stopped.
pause