#!/bin/bash

# BGP in Cloud (BIC) Installer
# This script automates the setup of the BIC application.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
PYTHON_CMD="python3"
VENV_DIR="venv"

# --- Helper Functions ---
echo_green() {
    echo -e "\033[0;32m$1\033[0m"
}

echo_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# --- Sanity Checks ---
echo_green "[1/5] Checking for dependencies..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo_red "ERROR: $PYTHON_CMD is not installed. Please install Python 3 and try again."
    exit 1
fi

if ! $PYTHON_CMD -m venv --help &> /dev/null; then
    echo_red "ERROR: The 'venv' module is not available. Please install the python3-venv package (or equivalent) for your distribution."
    exit 1
fi

# --- Virtual Environment Setup ---
echo_green "[2/5] Creating Python virtual environment in './$VENV_DIR'..."
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    $PYTHON_CMD -m venv $VENV_DIR
fi

# --- Activate Virtual Environment ---
source "$VENV_DIR/bin/activate"
echo_green "[3/5] Virtual environment activated."

# --- Install Dependencies ---
echo_green "[4/5] Installing required packages from requirements.txt..."
pip install -r requirements.txt

# --- Database Initialization ---
echo_green "[5/5] Initializing the database..."
python init_db.py

# --- Success ---
echo_green "-------------------------------------------------"
echo_green "SUCCESS: BGP in Cloud has been installed!"
echo_green "-------------------------------------------------"
echo "To run the application, first activate the environment:"
echo "  source $VENV_DIR/bin/activate"
echo "Then start the web server:"
echo "  uvicorn bic.webapp:app --reload"
