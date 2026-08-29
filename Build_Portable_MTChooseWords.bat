@echo off
setlocal EnableExtensions

title Build MT Choose Words Portable

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

echo ==========================================
echo      Build MT Choose Words Portable
echo ==========================================
echo.

if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found:
    echo %PYTHON%
    echo.
    pause
    exit /b 1
)

cd /d "%ROOT%"
"%PYTHON%" scripts\build_portable.py

if errorlevel 1 (
    echo.
    echo [ERROR] Portable build failed.
    echo.
    pause
    exit /b 1
)

echo.
echo Portable package is ready:
echo %ROOT%dist\MTChooseWords_Portable
echo.
pause
exit /b 0
