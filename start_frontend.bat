@echo off
setlocal

set "ROOT_DIR=%~dp0"

cd /d "%ROOT_DIR%frontend"
echo [INFO] Starting frontend on http://127.0.0.1:5173
npm.cmd run dev

