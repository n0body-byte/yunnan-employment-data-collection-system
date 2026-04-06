@echo off
setlocal

taskkill /FI "WINDOWTITLE eq Yunnan Backend" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Yunnan Frontend" /T /F >nul 2>nul

echo [INFO] Requested shutdown for backend/frontend windows.

