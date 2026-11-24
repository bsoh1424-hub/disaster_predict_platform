@echo off
title Next.js Frontend Server (Port 3000)
echo ========================================================
echo  Starting Next.js Frontend Server (Port 3000)
echo ========================================================
cd /d %~dp0frontend
npm run dev
pause
