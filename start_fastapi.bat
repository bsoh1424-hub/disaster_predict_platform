@echo off
title FastAPI Model & RAG Server (Port 8000)
echo ========================================================
echo  Starting FastAPI Deep Learning & RAG Engine (Port 8000)
echo ========================================================
cd /d %~dp0fastapi-model
python app\main.py
pause
