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

:menu
cls
echo ==========================================
echo          MT Choose Words
echo ==========================================
echo  [1] Run application
echo  [2] Import words from DOCX/TXT
echo  [3] Run automated tests
echo  [4] Build Windows EXE
echo  [5] Exit
echo ==========================================
set /p "CHOICE=Select menu [1-5]: "

if "%CHOICE%"=="1" goto run_app
if "%CHOICE%"=="2" goto reload_words
if "%CHOICE%"=="3" goto run_tests
if "%CHOICE%"=="4" goto build_exe
if "%CHOICE%"=="5" goto end
echo.
echo Please select a number from 1 to 5.
pause
goto menu

:run_app
cls
echo Starting MT Choose Words...
cd /d "%ROOT%"
"%PYTHON%" -m app
if errorlevel 1 echo Application exited with error code %errorlevel%.
pause
goto menu

:reload_words
cls
echo Importing words from DOCX/TXT...
cd /d "%ROOT%"
"%PYTHON%" scripts\reload_words.py
if errorlevel 1 (
    echo.
    echo [ERROR] Reload failed.
) else (
    echo.
    echo Reload completed.
)
pause
goto menu

:run_tests
cls
echo Running pytest...
cd /d "%ROOT%"
"%PYTHON%" -m pytest -q
if errorlevel 1 (
    echo.
    echo [ERROR] Some tests failed.
) else (
    echo.
    echo All tests passed.
)
pause
goto menu

:build_exe
cls
echo Building Windows EXE. This may take several minutes...
cd /d "%ROOT%"
"%PYTHON%" -m PyInstaller --noconfirm mt_choose_words.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
) else (
    echo.
    echo Build completed: %ROOT%dist\MTChooseWords.exe
)
pause
goto menu

:end
endlocal
exit /b 0
