@echo off
title FastAPI Model Server (Port 8000)
echo ========================================================
echo  Starting FastAPI Deep Learning Server (Port 8000)
echo ========================================================
cd /d %~dp0fastapi-model
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
