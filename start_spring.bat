@echo off
title Spring Boot Backend Server (Port 8080)
echo ========================================================
echo  Starting Spring Boot MVC & Security Server (Port 8080)
echo ========================================================
cd /d %~dp0backend
call "C:\Users\ohbs1\.gradle\wrapper\dists\gradle-9.7.1-bin\1w1c7tv4s851m17nbqdsro2tv\gradle-9.7.1\bin\gradle.bat" bootRun
pause
