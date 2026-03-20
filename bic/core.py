import sqlite3
import subprocess
import re
import uuid
import threading
import logging
import ipaddress
import psutil
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

# --- Logging Setup ---
def get_logger(name):
    """Initializes and returns a logger instance with a default configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(name)


log = get_logger(__name__)

# --- Network Utilities ---
def get_wan_interface() -> str | None:
    """
    Identifies the primary WAN interface by finding the default route.

    Returns:
        The name of the WAN interface, or None if it cannot be determined.
    """
    try:
        # psutil.net_if_addrs() provides addresses for each interface.
        # We are looking for the interface that has the default gateway.
        # A common way to find this is to look for the interface with a public IP.
        # This is not foolproof but is a good heuristic for many environments.
        all_addrs = psutil.net_if_addrs()
        for interface_name, snic_addrs in all_addrs.items():
            for addr in snic_addrs:
                if addr.family == 2:  # AF_INET (IPv4)
                    try:
                        ip = ipaddress.ip_address(addr.address)
                        if not ip.is_loopback and not ip.is_private and not ip.is_link_local:
                            log.info(f"Heuristically determined WAN interface to be '{interface_name}'.")
                            return interface_name
                    except ValueError:
                        continue
        log.warning("Could not determine WAN interface. No public IP found. Falling back to default route check.")
        # Fallback for environments where the public IP isn't obvious (e.g. behind NAT)
        # This part is more complex and OS-specific, so we will leave a placeholder for now
        # and rely on the public IP heuristic which covers many cases.
        return None

    except Exception as e:
        log.error(f"An unexpected error occurred while determining WAN interface: {e}", exc_info=True)
        return None

def get_wan_ip() -> Optional[str]:
    """Gets the primary public IP address of the server."""
    interface = get_wan_interface()
    try:
        cmd = f"ip -4 addr show {interface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'"
        ip = subprocess.check_output(cmd, shell=True, text=True).strip()
        return ip
    except Exception as e:
        log.warning(f"Could not determine WAN IP for interface {interface}. Error: {e}")
        return None

# --- Thread-Local Database Connection ---
local = threading.local()

def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Establishes and returns a thread-local database connection."""
    if not hasattr(local, 'connection') or local.connection is None:
        log.info(f"Creating new DB connection for thread {threading.get_ident()} to {db_path}")
        try:
            local.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
            local.connection.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
            local.connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            log.critical(f"Failed to connect to database at {db_path}: {e}")
            raise
    return local.connection

# --- Core Database Class ---
class BIC_DB:
    """Main database interaction class for the application."""

    def __init__(self, db_path: str = "bic.db", base_dir: str = None):
        self.db_path = Path(base_dir or ".") / db_path
        self.conn = get_db_connection(self.db_path)
        # Migrations are now handled by init_db.py

    def run_migrations(self):
        """Initializes the database schema. Should be run from init_db.py."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                self._create_schema(cursor)
        except sqlite3.Error as e:
            log.error(f"Database migration failed: {e}")
            self.conn.rollback()

    def _create_schema(self, cursor: sqlite3.Cursor):
        """Defines and creates all application tables if they do not exist."""
        # System and Settings
        cursor.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")

        # Clients
        cursor.execute("""CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            type TEXT NOT NULL,
            asn INTEGER,
            bgp_session_enabled INTEGER DEFAULT 0,
            bgp_frr_conf TEXT, -- Holds generated FRR config for the client
            bgp_bird_conf TEXT, -- Holds generated BIRD config for the client
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        # Network Pools and Allocations
        cursor.execute("""CREATE TABLE IF NOT EXISTS ip_pools (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            afi TEXT NOT NULL, -- 'inet' or 'inet6'
            cidr TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS ip_allocations (
            id TEXT PRIMARY KEY,
            pool_id TEXT NOT NULL,
            client_id TEXT,
            address TEXT NOT NULL UNIQUE, -- Can be a single IP or a CIDR subnet
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
        )""")

        # Server-side Network Config
        cursor.execute("""CREATE TABLE IF NOT EXISTS server_interfaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE, -- e.g., 'wg0'
            listen_port INTEGER NOT NULL,
            address TEXT NOT NULL, -- e.g., '10.0.0.1/24,fd00::1/64'
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL
        )""")

        # WireGuard Peers (Clients)
        cursor.execute("""CREATE TABLE IF NOT EXISTS wireguard_peers (
            id TEXT PRIMARY KEY,
            client_id TEXT UNIQUE NOT NULL,
            client_public_key TEXT NOT NULL,
            client_private_key TEXT NOT NULL,
            allowed_ips TEXT NOT NULL,
            client_conf TEXT, -- Holds the generated client-side config
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
        )""")

        # BGP Core Peers
        cursor.execute("""CREATE TABLE IF NOT EXISTS bgp_peers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            hostname TEXT NOT NULL,
            asn INTEGER NOT NULL,
            enabled INTEGER DEFAULT 0,
            wireguard_tunnel_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(wireguard_tunnel_id) REFERENCES wireguard_peers(id) ON DELETE SET NULL
        )""")

        # BGP Prefix Advertisements
        cursor.execute("""CREATE TABLE IF NOT EXISTS bgp_advertisements (
            id TEXT PRIMARY KEY,
            peer_id TEXT NOT NULL,
            prefix TEXT NOT NULL,
            blackholed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(peer_id) REFERENCES bgp_peers(id) ON DELETE CASCADE
        )""")

        # User and Audit Tables
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )""")

        # WebAuthn Credentials
        cursor.execute("""CREATE TABLE IF NOT EXISTS webauthn_credentials (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            credential_id TEXT NOT NULL UNIQUE,
            public_key TEXT NOT NULL,
            sign_count INTEGER NOT NULL,
            transports TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        # YubiKey Credentials
        cursor.execute("""CREATE TABLE IF NOT EXISTS yubikey_credentials (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        # Google Authenticator Secrets
        cursor.execute("""CREATE TABLE IF NOT EXISTS google_authenticator_secrets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE,
            secret TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        # Create default IP pools if they don't exist
        cursor.execute("SELECT COUNT(*) FROM ip_pools WHERE name = ?", ('CLIENT_WG_IPV4_POOL',))
        if cursor.fetchone()['COUNT(*)'] == 0:
            cursor.execute(
                "INSERT INTO ip_pools (id, name, afi, cidr, description) VALUES (?, ?, ?, ?, ?)",
                (self._generate_id(), 'CLIENT_WG_IPV4_POOL', 'inet', '172.31.0.0/24', 'Pool for client WireGuard IPv4 addresses')
            )
            log.info("Created default IPv4 WireGuard client pool.")

        cursor.execute("SELECT COUNT(*) FROM ip_pools WHERE name = ?", ('CLIENT_WG_IPV6_POOL',))
        if cursor.fetchone()['COUNT(*)'] == 0:
            cursor.execute(
                "INSERT INTO ip_pools (id, name, afi, cidr, description) VALUES (?, ?, ?, ?, ?)",
                (self._generate_id(), 'CLIENT_WG_IPV6_POOL', 'inet6', 'fd31::/64', 'Pool for client WireGuard IPv6 addresses')
            )
            log.info("Created default IPv6 WireGuard client pool.")

        # Create a default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()['COUNT(*)'] == 0:
            from bic.modules.user_management import hash_password
            admin_password = "admin"
            admin_user = {
                "id": self._generate_id(),
                "username": "admin",
                "email": "admin@localhost",
                "password_hash": hash_password(admin_password),
                "role": "admin",
            }
            columns = ", ".join([f'\"{c}\"' for c in admin_user.keys()])
            placeholders = ", ".join(['?' for _ in admin_user.values()])
            cursor.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders})", tuple(admin_user.values()))
            log.warning("*****************************************************************")
            log.warning("*** NO USERS FOUND. CREATED DEFAULT ADMIN USER ***")
            log.warning("*** Username: admin")
            log.warning(f"*** Password: {admin_password}")
            log.warning("*** PLEASE CHANGE THIS PASSWORD IMMEDIATELY ***")
            log.warning("*****************************************************************")

    def find_all(self, table: str, criteria: dict = None) -> List[Dict[str, Any]]:
        """Fetches all records from a given table, optionally filtering by criteria."""
        query = f"SELECT * FROM {table}"
        params = ()
        if criteria:
            where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
            query += f" WHERE {where_clause}"
            params = tuple(criteria.values())
        try:
            with self.conn:
                return self.conn.execute(query, params).fetchall()
        except sqlite3.Error as e:
            log.error(f"Database error in find_all for table {table}: {e}")
            return []

    def find_one(self, table: str, criteria: dict) -> Optional[Dict[str, Any]]:
        """Finds a single record based on a criteria dictionary."""
        where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        try:
            with self.conn:
                return self.conn.execute(query, tuple(criteria.values())).fetchone()
        except sqlite3.Error as e:
            log.error(f"Database error in find_one for {table} with criteria {criteria}: {e}")
            return None

    def _generate_id(self) -> str:
        """Generates a new UUID string."""
        return str(uuid.uuid4())

    def insert(self, table: str, data: dict) -> int | str | None:
        """Inserts a record into the database. The caller is responsible for providing the ID if the column is not autoincrementing."""
        columns = list(data.keys())
        values = tuple(data.values())
        cols_str = ", ".join([f'\"{c}\"' for c in columns])
        placeholders = ", ".join(['?' for _ in values])

        query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"

        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, values)
                # For text IDs, the ID is already in the data dict. For autoincrement, it's lastrowid.
                return data.get('id') or cursor.lastrowid
        except sqlite3.Error as e:
            log.error(f"Database error inserting into {table}: {e}")
            return None

    def update(self, table: str, item_id: str, data: dict):
        """Updates a record in a table by its ID."""
        set_clause = ", ".join([f'\"{k}\"=?' for k in data])
        query = f"UPDATE {table} SET {set_clause} WHERE id=?"
        try:
            with self.conn:
                self.conn.execute(query, tuple(data.values()) + (item_id,))
            log.info(f"Updated record {item_id} in {table}.")
        except sqlite3.Error as e:
            log.error(f"Database error updating {item_id} in {table}: {e}")

    def delete(self, table: str, item_id: str):
        """Deletes a record from a table by its ID."""
        query = f"DELETE FROM {table} WHERE id=?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, (item_id,))
                log.info(f"Deleted record {item_id} from {table}.")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            log.error(f"Database error deleting {item_id} from {table}: {e}")
            return False

    def delete_many(self, table: str, criteria: dict):
        """Deletes multiple records from a table based on a criteria dictionary."""
        where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, tuple(criteria.values()))
                log.info(f"Deleted {cursor.rowcount} records from {table} where {criteria}")
                return cursor.rowcount
        except sqlite3.Error as e:
            log.error(f"Database error in delete_many for {table} with criteria {criteria}: {e}")
            return 0

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Retrieves a specific setting from the settings table."""
        result = self.find_one('settings', {'key': key})
        return result['value'] if result else default

    def query_to_dict(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes a query and returns the results as a list of dictionaries.

        Args:
            query: The SQL query to execute.
            params: The parameters to pass to the query.

        Returns:
            A list of dictionaries representing the rows.
        """
        try:
            with self.conn:
                # The connection's row_factory is already configured to return dicts.
                return self.conn.execute(query, params).fetchall()
        except sqlite3.Error as e:
            log.error(f"Database query error: {e}", exc_info=True)
            return []

    def count(self, table: str, where_clause: str = None, params: tuple = ()) -> int:
        """Counts the number of rows in a table, optionally with a WHERE clause."""
        query = f"SELECT COUNT(*) FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            with self.conn:
                result = self.conn.execute(query, params).fetchone()
                return result['COUNT(*)'] if result else 0
        except sqlite3.Error as e:
            log.error(f"Database error counting in {table}: {e}")
            return 0

    def insert_or_replace(self, table: str, data: dict):
        """Inserts a record, or replaces it if the primary key exists."""
        columns = ', '.join(f'\"{k}\"' for k in data.keys())
        placeholders = ', '.join('?' for _ in data)
        query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
        try:
            with self.conn:
                self.conn.execute(query, tuple(data.values()))
            log.info(f"Upserted record in {table} with key {data.get('key') or data.get('id')}")
        except sqlite3.Error as e:
            log.error(f"Database error during insert_or_replace in {table}: {e}")
