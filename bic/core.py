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
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA user_version = 12")
        self._create_schema(cursor)
        self.conn.commit()

    def _create_schema(self, cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS clients (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, name TEXT NOT NULL, email TEXT, type TEXT NOT NULL, asn INTEGER, wireguard_conf TEXT, bgp_frr_conf TEXT, bgp_bird_conf TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS ip_pools (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, name TEXT NOT NULL UNIQUE, afi TEXT NOT NULL, cidr TEXT NOT NULL UNIQUE, description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS ip_allocations (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, pool_id TEXT NOT NULL, client_id TEXT, ip_address TEXT NOT NULL UNIQUE, description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE, FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS ip_subnets (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, pool_id TEXT NOT NULL, client_id TEXT, subnet TEXT NOT NULL UNIQUE, description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE, FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS wireguard_interfaces (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, name TEXT NOT NULL UNIQUE, listen_port INTEGER NOT NULL, address TEXT NOT NULL, private_key TEXT NOT NULL, public_key TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS wireguard_peers (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, interface_id TEXT NOT NULL, client_id TEXT UNIQUE, name TEXT NOT NULL, public_key TEXT NOT NULL, allowed_ips TEXT, FOREIGN KEY(interface_id) REFERENCES wireguard_interfaces(id) ON DELETE CASCADE, FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS bgp_sessions (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, client_id TEXT NOT NULL, state TEXT, last_updated DATETIME, FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS email_log (id TEXT PRIMARY KEY, display_id INTEGER UNIQUE, client_id TEXT NOT NULL, subject TEXT, sent_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

    def find_all(self, table):
        return self.conn.execute(f"SELECT * FROM {table}").fetchall()

    # ... (all other DB methods)
