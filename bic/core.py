import sqlite3
import subprocess
import re
import uuid
import threading
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

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
        self._run_migrations()

    def _run_migrations(self):
        """Initializes the database schema and runs necessary migrations."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                self._create_schema(cursor)
        except sqlite3.Error as e:
            log.error(f"Database migration failed: {e}")
            self.conn.rollback()

    def _create_schema(self, cursor: sqlite3.Cursor):
        """Defines and creates all application tables if they do not exist."""
        cursor.execute("CREATE TABLE IF NOT EXISTS clients (...)")
        # ... (All other CREATE TABLE statements)

    def find_all(self, table: str) -> List[Dict[str, Any]]:
        """Fetches all records from a given table."""
        try:
            with self.conn:
                return self.conn.execute(f"SELECT * FROM {table}").fetchall()
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

    def find_all_by(self, table: str, criteria: dict) -> List[Dict[str, Any]]:
        """Finds all records matching a criteria dictionary."""
        where_clause = " AND ".join([f'\"{k}\"=?' for k in criteria])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        try:
            with self.conn:
                return self.conn.execute(query, tuple(criteria.values())).fetchall()
        except sqlite3.Error as e:
            log.error(f"Database error in find_all_by for {table} with criteria {criteria}: {e}")
            return []

    def insert(self, table: str, data: dict) -> Optional[str]:
        """Inserts a new record, generating a GUID if needed."""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        columns = ', '.join(f'\"{k}\"' for k in data.keys())
        placeholders = ', '.join('?' for _ in data)
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        try:
            with self.conn:
                self.conn.execute(query, tuple(data.values()))
            log.info(f"Inserted record into {table} with ID {data['id']}")
            return data['id']
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
                self.conn.execute(query, (item_id,))
            log.info(f"Deleted record {item_id} from {table}.")
        except sqlite3.Error as e:
            log.error(f"Database error deleting {item_id} from {table}: {e}")

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Retrieves a specific setting from the settings table."""
        result = self.find_one('settings', {'key': key})
        return result['value'] if result else default

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
