@echo off
REM Pose Estimation Service - Windows Startup Script

setlocal
cls

echo ===============================================
echo Pose Estimation Service - Startup
echo ===============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.8+
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

echo [2/4] Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Dependencies not installed. Installing...
    pip install -q -r pose_service\requirements.txt
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies available
)

echo [3/4] Starting Pose Estimation Service...
echo.
echo      WebSocket: ws://127.0.0.1:8000/ws/pose
echo      Health:    http://127.0.0.1:8000/health
echo.

python -m pose_service.server

echo.
echo [!] Service stopped.
pause
