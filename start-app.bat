@echo off
title Repo Rizz Server
echo Starting Repo Rizz Application (FastAPI + HTML/CSS/JS Frontend)...
echo.
cd /d "%~dp0python-backend"
start http://localhost:8001
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --no-proxy-headers
pause
