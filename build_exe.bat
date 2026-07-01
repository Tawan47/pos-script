@echo off
chcp 65001 >nul
title Build EXE - test_back_forth_postal

echo.
echo ========================================
echo   Build test_back_forth_postal.exe
echo ========================================
echo.

cd /d "%~dp0"

:: ตรวจสอบ Python
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python ก่อน
    pause
    exit /b 1
)

:: ติดตั้ง PyInstaller ถ้ายังไม่มี
echo [1/3] ตรวจสอบ PyInstaller...
py -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ติดตั้ง PyInstaller...
    py -m pip install pyinstaller
)

:: ติดตั้ง dependencies
echo [2/3] ติดตั้ง dependencies...
py -m pip install pywinauto pywin32 comtypes

:: Build exe
echo [3/3] กำลัง build .exe ...
py -m PyInstaller test_back_forth_postal.spec --clean

echo.
if exist "dist\test_back_forth_postal.exe" (
    echo ========================================
    echo   BUILD สำเร็จ!
    echo   ไฟล์อยู่ที่: dist\test_back_forth_postal.exe
    echo ========================================
) else (
    echo [ERROR] Build ไม่สำเร็จ ดู log ด้านบน
)
echo.
pause
