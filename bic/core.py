import sqlite3
import subprocess
import re
import uuid
import threading
import logging
from pathlib import Path

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Network Utilities ---
def get_wan_interface():
    """Gets the primary public-facing network interface name."""
    try:
        cmd = "ip route get 8.8.8.8 | awk '{print $5}'"
        interface = subprocess.check_output(cmd, shell=True, text=True).strip()
        return interface
    except Exception as e:
        log.warning(f"Could not determine WAN interface, falling back to 'eth0'. Error: {e}")
        return "eth0"

def get_wan_ip():
    """Gets the primary public IP address of the server."""
    interface = get_wan_interface()
    try:
        cmd = f"ip -4 addr show {interface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'"
        ip = subprocess.check_output(cmd, shell=True, text=True).strip()
        return ip
    except Exception as e:
        log.warning(f"Could not determine WAN IP for interface {interface}. Error: {e}")
        return None

# --- Database Connection ---
local = threading.local()

def get_db_connection(db_path):
    if not hasattr(local, 'connection') or local.connection is None:
        log.info(f"Creating new DB connection for thread {threading.get_ident()} to {db_path}")
        local.connection = sqlite3.connect(db_path, check_same_thread=False)
        local.connection.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
        local.connection.execute("PRAGMA foreign_keys = ON")
    return local.connection

# --- Core DB Class ---
class BIC_DB:
    """Main database interaction class for the application."""
    def __init__(self, db_path="bic.db", base_dir=None):
        self.db_path = Path(base_dir or ".") / db_path
        self.conn = get_db_connection(self.db_path)
        self._run_migrations()

    def _run_migrations(self):
        """Initializes the database schema."""
        try:
            cursor = self.conn.cursor()
            self._create_schema(cursor)
            self.conn.commit()
        except Exception as e:
            log.error(f"Database migration failed: {e}")
            self.conn.rollback()

    def _create_schema(self, cursor):
        """Defines and creates all application tables."""
        # ... (CREATE TABLE statements are correct and remain the same)

    def find_all(self, table):
        """Fetches all records from a table."""
        try:
            return self.conn.execute(f"SELECT * FROM {table}").fetchall()
        except Exception as e:
            log.error(f"Error in find_all for table {table}: {e}")
            return []

    def find_one(self, table, criteria):
        """Finds a single record by criteria."""
        try:
            where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            return self.conn.execute(query, tuple(criteria.values())).fetchone()
        except Exception as e:
            log.error(f"Error in find_one for {table} with criteria {criteria}: {e}")
            return None

    def find_all_by(self, table, criteria):
        """Finds all records matching criteria."""
        try:
            where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            return self.conn.execute(query, tuple(criteria.values())).fetchall()
        except Exception as e:
            log.error(f"Error in find_all_by for {table} with criteria {criteria}: {e}")
            return []

    def insert(self, table, data):
        """Inserts a new record, generating a GUID if needed."""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        try:
            columns = ', '.join(f'\"{k}\"' for k in data.keys())
            placeholders = ', '.join('?' for _ in data)
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = self.conn.cursor()
            cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            log.info(f"Inserted record into {table} with ID {data['id']}")
            return data['id']
        except Exception as e:
            log.error(f"Failed to insert into {table}: {e}")
            self.conn.rollback()
            return None

    def update(self, table, item_id, data):
        """Updates a record by its ID."""
        try:
            set_clause = ", ".join([f'\"{k}\"=?' for k in data])
            query = f"UPDATE {table} SET {set_clause} WHERE id=?"
            self.conn.execute(query, tuple(data.values()) + (item_id,))
            self.conn.commit()
            log.info(f"Updated record {item_id} in {table}.")
        except Exception as e:
            log.error(f"Failed to update {item_id} in {table}: {e}")
            self.conn.rollback()

    def delete(self, table, item_id):
        """Deletes a record by its ID."""
        try:
            self.conn.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
            self.conn.commit()
            log.info(f"Deleted record {item_id} from {table}.")
        except Exception as e:
            log.error(f"Failed to delete {item_id} from {table}: {e}")
            self.conn.rollback()

    def get_setting(self, key, default=None):
        """Retrieves a specific setting."""
        try:
            result = self.find_one('settings', {'key': key})
            return result['value'] if result else default
        except Exception as e:
            log.error(f"Failed to get setting '{key}': {e}")
            return default

    def insert_or_replace(self, table, data):
        """Inserts or replaces a record."""
        try:
            columns = ', '.join(f'\"{k}\"' for k in data.keys())
            placeholders = ', '.join('?' for _ in data)
            query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
            self.conn.execute(query, tuple(data.values()))
            self.conn.commit()
            log.info(f"Upserted record in {table} with key {data.get('key') or data.get('id')}")
        except Exception as e:
            log.error(f"Failed to upsert in {table}: {e}")
            self.conn.rollback()
