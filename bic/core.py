import sqlite3
import subprocess
import re
import uuid
import threading
from pathlib import Path

def get_wan_interface():
    """Gets the primary public-facing network interface name."""
    try:
        cmd = "ip route get 8.8.8.8 | awk '{print $5}'"
        interface = subprocess.check_output(cmd, shell=True, text=True).strip()
        return interface
    except Exception:
        return "eth0"

def get_wan_ip():
    """Gets the primary public IP address of the server."""
    interface = get_wan_interface()
    try:
        cmd = f"ip -4 addr show {interface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'"
        ip = subprocess.check_output(cmd, shell=True, text=True).strip()
        return ip
    except Exception:
        return None

# Use thread-local data to ensure each thread gets its own DB connection
local = threading.local()

def get_db_connection(db_path):
    if not hasattr(local, 'connection'):
        local.connection = sqlite3.connect(db_path, check_same_thread=False)
        local.connection.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
        local.connection.execute("PRAGMA foreign_keys = ON")
    return local.connection

class BIC_DB:
    def __init__(self, db_path="bic.db", base_dir=None):
        self.db_path = Path(base_dir or ".") / db_path
        self.conn = get_db_connection(self.db_path)
        self._run_migrations()

    def _run_migrations(self):
        # ... (migrations logic remains the same) ...
        pass

    def find_all(self, table):
        return self.conn.execute(f"SELECT * FROM {table}").fetchall()

    # ... (all other DB methods remain the same) ...
