@echo off
chcp 65001 >nul
title POS Test - ระบุปลายทาง

echo.
echo ========================================
echo   POS Test - กดไปกลับระบุปลายทาง
echo ========================================
echo.
echo กด Ctrl+C เพื่อหยุด
echo.

cd /d "%~dp0"
py test_back_forth_postal.py

echo.
pause
