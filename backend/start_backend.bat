@echo off
setlocal

if "%LOCAL_SERVER_NAME%"=="" (
  echo ERROR: LOCAL_SERVER_NAME is not set. Example:
  echo   set LOCAL_SERVER_NAME=Laptop2
  echo   start_backend.bat
  exit /b 1
)

call venv\Scripts\activate
python run_all.py

endlocal
