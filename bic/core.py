import sqlite3
import subprocess
import re
import uuid
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

class BIC_DB:
    def __init__(self, db_path="bic.db", base_dir=None):
        self.db_path = Path(base_dir or ".") / db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = self._dict_factory
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._run_migrations()

    def _dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _run_migrations(self):
        cursor = self.conn.cursor()
        user_version = cursor.execute("PRAGMA user_version").fetchone()['user_version']
        if user_version == 0:
            self._create_schema(cursor)
            self.conn.execute("PRAGMA user_version = 12") # Start new DBs at the latest version
        
        if user_version < 12:
            # GUID Migration logic here
            pass # For now, we assume a fresh DB or manual migration

    def _create_schema(self, cursor):
        # Schema using GUIDs (TEXT) for all primary and foreign keys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                display_id INTEGER UNIQUE,
                name TEXT NOT NULL, email TEXT, type TEXT NOT NULL, asn INTEGER,
                wireguard_conf TEXT, bgp_frr_conf TEXT, bgp_bird_conf TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_pools (
                id TEXT PRIMARY KEY,
                display_id INTEGER UNIQUE,
                name TEXT NOT NULL UNIQUE, afi TEXT NOT NULL, cidr TEXT NOT NULL UNIQUE,
                description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_allocations (
                id TEXT PRIMARY KEY, display_id INTEGER UNIQUE,
                pool_id TEXT NOT NULL, client_id TEXT, ip_address TEXT NOT NULL UNIQUE,
                description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_subnets (
                id TEXT PRIMARY KEY, display_id INTEGER UNIQUE,
                pool_id TEXT NOT NULL, client_id TEXT, subnet TEXT NOT NULL UNIQUE,
                description TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wireguard_interfaces (
                id TEXT PRIMARY KEY, display_id INTEGER UNIQUE,
                name TEXT NOT NULL UNIQUE, listen_port INTEGER NOT NULL, address TEXT NOT NULL,
                private_key TEXT NOT NULL, public_key TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wireguard_peers (
                id TEXT PRIMARY KEY, display_id INTEGER UNIQUE,
                interface_id TEXT NOT NULL, client_id TEXT UNIQUE,
                name TEXT NOT NULL, public_key TEXT NOT NULL, allowed_ips TEXT,
                FOREIGN KEY(interface_id) REFERENCES wireguard_interfaces(id) ON DELETE CASCADE,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)
        # ... (Other tables like settings, bgp_sessions, email_log)

    def insert(self, table, data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        if table == 'clients': # Handle display_id for clients
            cursor = self.conn.cursor()
            max_id = cursor.execute("SELECT MAX(display_id) FROM clients").fetchone()[0]
            data['display_id'] = (max_id or 0) + 1

        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.conn.cursor()
        cursor.execute(query, tuple(data.values()))
        self.conn.commit()
        return data['id']

    def find_one(self, table, criteria):
        where_clause = " AND ".join([f"{k}=?" for k in criteria])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        return self.conn.execute(query, tuple(criteria.values())).fetchone()

    def find_all_by(self, table, criteria):
        where_clause = " AND ".join([f"{k}=?" for k in criteria])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        return self.conn.execute(query, tuple(criteria.values())).fetchall()

    def find_all(self, table):
        return self.conn.execute(f"SELECT * FROM {table}").fetchall()

    def update(self, table, item_id, data):
        set_clause = ", ".join([f"{k}=?" for k in data])
        query = f"UPDATE {table} SET {set_clause} WHERE id=?"
        self.conn.execute(query, tuple(data.values()) + (item_id,))
        self.conn.commit()

    def delete(self, table, item_id):
        self.conn.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
        self.conn.commit()

    # ... (rest of the methods)
