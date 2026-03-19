#!/bin/bash
# BGP in the Cloud - Startup Script

# Get the directory where the script is located
BASE_DIR=$(dirname "$0")

# Activate Python virtual environment
# shellcheck source=/dev/null
source "$BASE_DIR/venv/bin/activate"

# --- Dependency Check ---
echo "Verifying Python dependencies..."
pip freeze > installed.txt
if ! diff -q installed.txt <(grep -vE "^#" requirements.txt | sort); then
    echo "-> Dependencies are out of date. Installing..."
    pip install -r requirements.txt
else
    echo "-> Dependencies are up to date."
fi
rm installed.txt

# Default to TUI if no argument is provided
MODE=${1:---tui}

if [ "$MODE" = "--tui" ]; then
    echo "Starting BIC IPAM - TUI Mode..."
    python3 -m bic.tui.main_menu
elif [ "$MODE" = "--web" ]; then
    echo "Starting BIC IPAM - Web App Mode..."
    echo "API will be available at http://127.0.0.1:8000"
    uvicorn bic.webapp:app --host 127.0.0.1 --port 8000 --reload --app-dir "$BASE_DIR"
else
    echo "Error: Invalid argument."
    echo "Usage: $0 [--tui | --web]"
    exit 1
fi
