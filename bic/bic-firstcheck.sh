#!/bin/bash
# BIC - System Integrity & Diagnostics Check

echo "
╔══════════════════════════════════════════════════════╗
║    BGP in the Cloud (BIC) Diagnostics Tool         ║
╚══════════════════════════════════════════════════════╝
"

# Function to check command existence
check_command() {
    if command -v "$1" &> /dev/null; then
        echo "[✔] Found '$1'"
    else
        echo "[❌] '$1' is not installed or not in PATH."
    fi
}

# Function to check package installation on Debian
check_package() {
    if dpkg -s "$1" &> /dev/null; then
        echo "[✔] Package '$1' is installed."
    else
        echo "[❌] Package '$1' is NOT installed. Please run bic-installer.sh"
    fi
}

# --- System Checks ---
echo "
▶️  Performing System Checks..."
check_package "wireguard"
check_package "bird2"
check_package "python3-venv"

# --- Project Structure Checks ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.." || exit # Move to project root

echo "
▶️  Performing Project File Checks..."

# Check for venv
if [ -d "venv" ]; then
    echo "[✔] Python virtual environment ('venv') found."
else
    echo "[❌] Python virtual environment ('venv') NOT found. Please run bic-installer.sh"
fi

# Check for database (it may not exist until first run, which is okay)
if [ -f "ipam.db" ]; then
    echo "[✔] Database ('ipam.db') found."
else
    echo "[ℹ️] Database ('ipam.db') not found. It will be created on first run."
fi

# --- Python Dependency Check ---
echo "
▶️  Verifying Python Dependencies inside venv..."
if [ -f "venv/bin/python" ]; then
    source venv/bin/activate
    pip check
    if [ $? -eq 0 ]; then
        echo "[✔] All Python dependencies are correctly installed."
    else
        echo "[❌] Python dependency issues detected. Try running: pip install -r requirements.txt"
    fi
    deactivate
else
    echo "[❌] Cannot check Python dependencies because venv is missing."
fi

echo "

✅ Diagnostics Complete.
"
