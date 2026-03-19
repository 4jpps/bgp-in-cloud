#!/bin/bash
# BIC - BGP in the Cloud - System Installer
# This script prepares a fresh Debian 12 system for the BIC application.

# --- Configuration & Constants ---
PYTHON_EXEC="python3"
REQ_FILE="requirements.txt"

echo "
╔══════════════════════════════════════════════════════╗
║      BGP in the Cloud (BIC) System Installer       ║
╚══════════════════════════════════════════════════════╝
"

# --- Root Check ---
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ This script must be run as root. Please use sudo." >&2
  exit 1
fi

# --- Step 1: System Package Update ---
echo "
▶️ [1/5] Updating system packages..."
apt-get update > /dev/null
apt-get upgrade -y
echo "✅ System packages are up to date."

# --- Step 2: Install Core Dependencies ---
echo "
▶️ [2/5] Installing core dependencies (Bird2, WireGuard, Python)..."
apt-get install -y bird2 wireguard python3-venv python3-pip
echo "✅ Core dependencies installed."


# --- Step 3: Firewall Configuration Guidance ---
WG_PORT=51820 # Default WireGuard Port
echo "
▶️ [3/5] Checking firewall status..."
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    echo "🔥 UFW firewall is active. Please ensure the following ports are open:"
    echo "   - Your SSH port (e.g., 22/tcp)"
    echo "   - WireGuard port: $WG_PORT/udp"
    echo "   To open the WireGuard port, you can run: sudo ufw allow $WG_PORT/udp"
elif command -v nft >/dev/null && nft list ruleset | grep -q "hook input"; then
    echo "🔥 nftables is active. Please ensure ports for SSH and WireGuard ($WG_PORT/udp) are open."
else
    echo "✅ No active firewall (UFW/nftables) detected. Ensure your cloud provider's firewall is configured."
fi

# --- Step 4: Python Virtual Environment Setup ---
echo "
▶️ [4/5] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_EXEC -m venv venv
    echo "   -> Virtual environment created."
else
    echo "   -> Virtual environment already exists."
fi

# --- Step 5: Install Python Dependencies ---
echo "
▶️ [5/5] Installing Python dependencies from $REQ_FILE..."

source venv/bin/activate

pip install -r "$REQ_FILE"

deactivate

echo "

🎉 Installation Complete! 🎉

To start the application, run the following command from the project directory:

./bic-start.sh

"
