@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT_DIR=%%~fI"

cd /d "%ROOT_DIR%frontend"
echo [INFO] Starting frontend on http://127.0.0.1:5173
npm.cmd run dev
