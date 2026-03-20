
# BGP in Cloud (BIC) Windows Installer
# This script automates the setup of the BIC application in a PowerShell environment.

# Exit immediately if a command exits with a non-zero status.
$ErrorActionPreference = 'Stop'

# --- Configuration ---
$PYTHON_CMD = "python"
$VENV_DIR = "venv"

# --- Helper Functions ---
function Echo-Green {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Echo-Red {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

# --- Sanity Checks ---
Echo-Green "[1/4] Checking for Python..."
try {
    $pythonVersion = & $PYTHON_CMD --version
    Echo-Green "Found Python: $pythonVersion"
} catch {
    Echo-Red "ERROR: '$PYTHON_CMD' is not installed or not in your PATH. Please install Python 3 and try again."
    exit 1
}

# --- Virtual Environment Setup ---
Echo-Green "[2/4] Creating Python virtual environment in '.\$VENV_DIR'..."
if (Test-Path -Path $VENV_DIR) {
    Write-Host "Virtual environment already exists. Skipping creation."
} else {
    & $PYTHON_CMD -m venv $VENV_DIR
}

# Define paths to venv executables
$VENV_PYTHON = ".\$VENV_DIR\Scripts\python.exe"
$VENV_PIP = ".\$VENV_DIR\Scripts\pip.exe"

# --- Install Dependencies ---
Echo-Green "[3/4] Installing required packages from requirements.txt..."
& $VENV_PIP install -r requirements.txt

# --- Database Initialization ---
Echo-Green "[4/4] Initializing the database..."
& $VENV_PYTHON init_db.py

# --- Success ---
Echo-Green "-------------------------------------------------"
Echo-Green "SUCCESS: BGP in Cloud has been installed!"
Echo-Green "-------------------------------------------------"
Write-Host "To run the application, first activate the environment:"
Write-Host "  .\$VENV_DIR\Scripts\Activate.ps1"
Write-Host "Then start the web server:"
Write-Host "  uvicorn bic.webapp:app --reload"
