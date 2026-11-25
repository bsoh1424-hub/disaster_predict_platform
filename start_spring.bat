@echo off
title Spring Boot Backend Server (Port 8080)
echo ========================================================
echo  Starting Spring Boot MVC and Security Server (Port 8080)
echo ========================================================

:: .env 파일 환경변수 자동 로드
if exist "%~dp0.env" (
    for /f "usebackq tokens=1* delims==" %%A in ("%~dp0.env") do (
        if not "%%A"=="" (
            echo %%A | findstr /r "^#" >nul || set "%%A=%%B"
        )
    )
)

echo Active Profile : mariadb
echo Database URL   : jdbc:mariadb://localhost:3306/storm_surge...
echo Database User  : surge
echo ========================================================

cd /d %~dp0backend
call "%USERPROFILE%\.gradle\wrapper\dists\gradle-9.7.1-bin\1w1c7tv4s851m17nbqdsro2tv\gradle-9.7.1\bin\gradle.bat" bootRun
pause
