@echo off
setlocal EnableExtensions

title Run MT Choose Words

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "CONFIG=%ROOT%config.toml"

echo ==========================================
echo          MT Choose Words
echo ==========================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found:
    echo %PYTHON%
    echo.
    echo Please install dependencies in this project environment first:
    echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "%CONFIG%" (
    echo [ERROR] Config file not found:
    echo %CONFIG%
    echo.
    pause
    exit /b 1
)

cd /d "%ROOT%"

echo Starting application with:
echo %PYTHON%
echo.

"%PYTHON%" -m app

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    echo Please review the message above.
    echo.
    pause
    exit /b 1
)

echo.
echo Application closed.
pause
exit /b 0
