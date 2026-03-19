import sqlite3
import os

class BIC_DB:
    """
    BGP in the Cloud - Database Core
    Handles all SQLite interactions and provides schema migration utilities.
    """
    def __init__(self, base_dir):
        self.db_path = os.path.join(base_dir, "ipam.db")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.initialize_schema()

    def get_connection(self):
        """Returns the current database connection."""
        return self.conn

    def _execute(self, query, params=()):
        """Executes a query and returns the cursor."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def initialize_schema(self):
        """Creates the initial core tables required by the system."""
        self.create_table_if_not_exists('settings', [
            'key TEXT PRIMARY KEY',
            'value TEXT'
        ])
        self.create_table_if_not_exists('clients', [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'name TEXT UNIQUE NOT NULL',
            'email TEXT',
            'asn INTEGER',
            'allow_smtp BOOLEAN DEFAULT 0 NOT NULL'
        ])
        self.create_table_if_not_exists('wireguard_peers', [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'client_id INTEGER',
            'name TEXT NOT NULL',
            'public_key TEXT NOT NULL UNIQUE',
            'preshared_key TEXT',
            'endpoint TEXT',
            'allowed_ips TEXT',
            'interface_id INTEGER NOT NULL',
            'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE',
            'FOREIGN KEY(interface_id) REFERENCES wireguard_interfaces(id) ON DELETE CASCADE'
        ])

        self.create_table_if_not_exists('ip_subnets', [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'pool_id INTEGER NOT NULL',
            'client_id INTEGER',
            'subnet TEXT NOT NULL UNIQUE',
            'description TEXT',
            'FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE',
            'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE',
        ])

        self.create_table_if_not_exists('email_log', [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'client_id INTEGER',
            'timestamp DATETIME DEFAULT CURRENT_TIMESTAMP',
            'subject TEXT',
            'body TEXT',
            'attachment_name TEXT',
            'attachment_content TEXT',
            'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE',
        ])

        self.insert_or_replace('settings', {'key': 'bgp_local_asn', 'value': '401575'})

    def create_table_if_not_exists(self, table_name, columns):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({ ', '.join(columns)})"
        self._execute(query)
        self.conn.commit()

    def add_column_if_not_exists(self, table_name, column_name, column_type):
        cursor = self._execute(f"PRAGMA table_info({table_name})")
        existing_columns = [row['name'] for row in cursor.fetchall()]
        if column_name not in existing_columns:
            self._execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            self.conn.commit()

    def insert(self, table_name, data):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})"
        cursor = self._execute(query, tuple(data.values()))
        self.conn.commit()
        return cursor.lastrowid
        
    def update(self, table_name, record_id, data):
        """Updates a record in a table."""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        params = list(data.values()) + [record_id]
        self._execute(query, tuple(params))
        self.conn.commit()

    def insert_or_replace(self, table_name, data):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT OR REPLACE INTO {table_name} ({keys}) VALUES ({placeholders})"
        self._execute(query, tuple(data.values()))
        self.conn.commit()

    def find_one(self, table, criteria):
        where_clause = " AND ".join([f'{key} = ?' for key in criteria.keys()])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cursor = self._execute(query, tuple(criteria.values()))
        return cursor.fetchone()

    def find_all(self, table):
        cursor = self._execute(f"SELECT * FROM {table}")
        return cursor.fetchall()

    def find_all_by(self, table, criteria):
        """Finds all records in a table based on criteria."""
        where_clause = " AND ".join([f"{key} = ?" for key in criteria.keys()])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cursor = self._execute(query, tuple(criteria.values()))
        return cursor.fetchall()
        
    def delete(self, table_name, record_id):
        """Deletes a record from a table."""
        query = f"DELETE FROM {table_name} WHERE id = ?"
        self._execute(query, (record_id,))
        self.conn.commit()

    def __del__(self):
        if self.conn:
            self.conn.close()