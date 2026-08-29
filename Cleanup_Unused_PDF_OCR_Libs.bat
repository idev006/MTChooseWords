@echo off
setlocal EnableExtensions
title Cleanup Unused PDF/OCR Libraries

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found:
    echo %PYTHON%
    pause
    exit /b 1
)

echo ==========================================
echo   Cleanup unused PDF/OCR word-reader libs
echo ==========================================
echo.
echo This project no longer imports words from PDF/OCR.
echo The worksheet PDF export feature is kept and will not be removed.
echo.
echo This cleanup uses only:
echo %PYTHON%
echo.
echo Packages to uninstall:
echo   pdfplumber pdfminer.six pypdfium2 pymupdf pytesseract pythainlp
echo   cryptography cffi pycparser tzdata
echo.
choice /C YN /N /M "Continue uninstall? [Y/N] "
if errorlevel 2 goto cancelled

cd /d "%ROOT%"
"%PYTHON%" -m pip uninstall -y pdfplumber pdfminer.six pypdfium2 pymupdf pytesseract pythainlp cryptography cffi pycparser tzdata
if errorlevel 1 (
    echo.
    echo [ERROR] Uninstall failed.
    pause
    exit /b 1
)

echo.
echo Checking installed dependency health...
"%PYTHON%" -m pip check
if errorlevel 1 (
    echo.
    echo [WARNING] pip check found dependency issues. Review the message above.
    pause
    exit /b 1
)

echo.
echo Cleanup completed.
pause
exit /b 0

:cancelled
echo.
echo Cleanup cancelled.
pause
exit /b 0
