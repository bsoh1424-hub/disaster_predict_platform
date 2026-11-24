@echo off
title Storm Surge Platform - Launcher
echo ========================================================
echo  Launching Storm Surge Prediction Platform
echo  1. FastAPI Model Server (Port 8000)
echo  2. Spring Boot Service Server (Port 8080)
echo  3. Next.js Frontend (Port 3000)
echo ========================================================

start "FastAPI Model & RAG Server (8000)" cmd /k "%~dp0start_fastapi.bat"
timeout /t 3 /nobreak > nul

start "Spring Boot Backend Server (8080)" cmd /k "%~dp0start_spring.bat"
timeout /t 5 /nobreak > nul

start "Next.js Frontend (3000)" cmd /k "%~dp0start_frontend.bat"

echo.
echo All services launched!
echo Access Dashboard: http://localhost:3000
echo Spring API Health: http://localhost:8080/api/health
echo FastAPI Docs: http://localhost:8000/docs
echo.
pause
