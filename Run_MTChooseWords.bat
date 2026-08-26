@echo off
setlocal EnableExtensions
title MT Choose Words
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found:
    echo %PYTHON%
    pause
    exit /b 1
)
cd /d "%ROOT%"
"%PYTHON%" -m app
if errorlevel 1 echo Application exited with error code %errorlevel%.
pause
