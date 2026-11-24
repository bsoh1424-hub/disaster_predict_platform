@echo off
title FastAPI Model Server (Port 8000)
echo ========================================================
echo  Starting FastAPI Deep Learning Server (Port 8000)
echo ========================================================

:: .env 파일 환경변수 자동 로드
if exist "%~dp0.env" (
    for /f "usebackq tokens=1* delims==" %%A in ("%~dp0.env") do (
        if not "%%A"=="" (
            echo %%A | findstr /r "^#" >nul || set "%%A=%%B"
        )
    )
)

cd /d %~dp0fastapi-model
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
