#!/bin/bash
# Pose Estimation Service - Linux/macOS Startup Script

echo "==============================================="
echo "Pose Estimation Service - Startup"
echo "==============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Install Python 3.8+"
    exit 1
fi

echo "[1/4] Checking Python version..."
python3 --version

# Check dependencies
echo "[2/4] Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "[WARN] Dependencies not installed. Installing..."
    pip install -q -r pose_service/requirements.txt
    echo "[OK] Dependencies installed"
else
    echo "[OK] Dependencies available"
fi

# Start service
echo "[3/4] Starting Pose Estimation Service..."
echo "      WebSocket: ws://127.0.0.1:8000/ws/pose"
echo "      Health:    http://127.0.0.1:8000/health"
echo ""

cd "$(dirname "$0")" || exit
python3 -m pose_service.server

echo ""
echo "[!] Service stopped. Press Enter to exit."
read
