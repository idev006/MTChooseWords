@echo off
setlocal EnableExtensions

title MT Choose Words Portable

set "ROOT=%~dp0"
set "EXE=%ROOT%MTChooseWords.exe"
set "CONFIG=%ROOT%config.toml"
set "DATABASE=%ROOT%app\mtchoosewords.sqlite3"
set "FONTS=%ROOT%app\assets\fonts"

echo ==========================================
echo        MT Choose Words Portable
echo ==========================================
echo.

if not exist "%EXE%" (
    echo [ERROR] Program file not found:
    echo %EXE%
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

if not exist "%DATABASE%" (
    echo [ERROR] Word database not found:
    echo %DATABASE%
    echo.
    pause
    exit /b 1
)

if not exist "%FONTS%" (
    echo [ERROR] Fonts folder not found:
    echo %FONTS%
    echo.
    pause
    exit /b 1
)

cd /d "%ROOT%"
start "" "%EXE%"
exit /b 0
