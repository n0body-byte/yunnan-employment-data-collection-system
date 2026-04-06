@echo off
setlocal

set "ROOT_DIR=%~dp0"

start "Yunnan Backend" cmd /k call "%ROOT_DIR%start_backend.bat"
start "Yunnan Frontend" cmd /k call "%ROOT_DIR%start_frontend.bat"

echo [INFO] Backend and frontend start commands have been launched.
echo [INFO] Backend:  http://127.0.0.1:8000
echo [INFO] Frontend: http://127.0.0.1:5173
