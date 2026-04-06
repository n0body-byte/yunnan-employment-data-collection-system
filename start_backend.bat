@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"

if not exist "%CONDA_BAT%" (
  echo [ERROR] conda.bat not found: %CONDA_BAT%
  echo Please update CONDA_BAT in start_backend.bat
  pause
  exit /b 1
)

cd /d "%ROOT_DIR%"
call "%CONDA_BAT%" activate yunnan-employment
if errorlevel 1 (
  echo [ERROR] Failed to activate conda environment: yunnan-employment
  pause
  exit /b 1
)

echo [INFO] Starting backend on http://127.0.0.1:8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

