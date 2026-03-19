import sqlite3
import os

class BIC_DB:
    """
    BGP in the Cloud - Database Core
    Handles all SQLite interactions and provides schema migration utilities.
    """
    def __init__(self, base_dir):
        self.db_path = os.path.join(base_dir, "ipam.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.initialize_schema()
        self._seed_initial_data()

    def get_connection(self):
        """Returns the current database connection."""
        return self.conn

    def _execute(self, query, params=()):
        """Executes a query and returns the cursor."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def initialize_schema(self):
        """Creates the initial core tables and handles schema migrations."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA user_version")
        user_version = cursor.fetchone()[0]

        if user_version < 1:
            # Version 1: Initial Schema
            self.create_table_if_not_exists('settings', [
                'key TEXT PRIMARY KEY',
                'value TEXT'
            ])
            self.create_table_if_not_exists('clients', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'name TEXT UNIQUE NOT NULL',
                'email TEXT',
                'type TEXT',
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

            self.create_table_if_not_exists('ip_pools', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'name TEXT UNIQUE NOT NULL',
                'cidr TEXT UNIQUE NOT NULL',
                'description TEXT'
            ])

            self.create_table_if_not_exists('ip_allocations', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'pool_id INTEGER NOT NULL',
                'client_id INTEGER NOT NULL',
                'ip_address TEXT NOT NULL UNIQUE',
                'description TEXT',
                'FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE',
                'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE'
            ])

            self.insert_or_replace('settings', {'key': 'bgp_local_asn', 'value': '401575'})
            self.conn.execute("PRAGMA user_version = 1")
            self.conn.commit()
            user_version = 1 # Update for the next migration step

        if user_version < 2:
            # Version 2: Add afi to ip_pools and make name/afi unique
            self.conn.execute("PRAGMA foreign_keys=off")
            self.conn.execute("BEGIN TRANSACTION")
            try:
                self.conn.execute("CREATE TABLE ip_pools_new (id INTEGER PRIMARY KEY, name TEXT NOT NULL, afi TEXT NOT NULL, cidr TEXT NOT NULL, description TEXT, UNIQUE(name, afi))")
                self.conn.execute("INSERT INTO ip_pools_new (id, name, afi, cidr, description) SELECT id, name, 'ipv4', cidr, description FROM ip_pools")
                self.conn.execute("DROP TABLE ip_pools")
                self.conn.execute("ALTER TABLE ip_pools_new RENAME TO ip_pools")
                self.conn.execute("COMMIT")
            except:
                self.conn.execute("ROLLBACK")
                raise
            finally:
                self.conn.execute("PRAGMA foreign_keys=on")
            
            self.conn.execute("PRAGMA user_version = 2")
            self.conn.commit()
            user_version = 2

        if user_version < 3:
            # Version 3: Add the missing ip_allocations table
            self.create_table_if_not_exists('ip_allocations', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'pool_id INTEGER NOT NULL',
                'client_id INTEGER NOT NULL',
                'ip_address TEXT NOT NULL UNIQUE',
                'description TEXT',
                'FOREIGN KEY(pool_id) REFERENCES ip_pools(id) ON DELETE CASCADE',
                'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE'
            ])
            self.conn.execute("PRAGMA user_version = 3")
            self.conn.commit()
            user_version = 3

        if user_version < 4:
            # Version 4: Add bgp_sessions and wireguard_interfaces tables
            self.create_table_if_not_exists('bgp_sessions', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'client_id INTEGER NOT NULL',
                'state TEXT NOT NULL DEFAULT \'pending\'',
                'last_updated DATETIME DEFAULT CURRENT_TIMESTAMP',
                'FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE'
            ])
            self.create_table_if_not_exists('wireguard_interfaces', [
                'id INTEGER PRIMARY KEY AUTOINCREMENT',
                'name TEXT NOT NULL UNIQUE',
                'listen_port INTEGER NOT NULL',
                'address TEXT NOT NULL',
                'private_key TEXT NOT NULL',
                'public_key TEXT NOT NULL'
            ])
            self.conn.execute("PRAGMA user_version = 4")
            self.conn.commit()
            user_version = 4

        if user_version < 5:
            # Version 5: Add conf storage to clients table
            self.add_column_if_not_exists('clients', 'wireguard_conf', 'TEXT')
            self.add_column_if_not_exists('clients', 'bgp_conf', 'TEXT')
            self.conn.execute("PRAGMA user_version = 5")
            self.conn.commit()
            user_version = 5

        if user_version < 6:
            # Version 6: Add configurable DNS settings
            self.insert('settings', {'key': 'dns_server_ipv4', 'value': '1.1.1.1'}, or_ignore=True)
            self.insert('settings', {'key': 'dns_server_ipv6', 'value': '2606:4700:4700::1111'}, or_ignore=True)
            self.conn.execute("PRAGMA user_version = 6")
            self.conn.commit()
            user_version = 6

        if user_version < 7:
            # Version 7: Add configurable WG endpoint setting
            self.insert('settings', {'key': 'wg_server_endpoint', 'value': 'your-server.example.com'}, or_ignore=True)
            self.conn.execute("PRAGMA user_version = 7")
            self.conn.commit()
            user_version = 7

        if user_version < 8:
            # Version 8: Add branding settings
            self.insert('settings', {'key': 'branding_company_name', 'value': 'BGP in the Cloud'}, or_ignore=True)
            self.insert('settings', {'key': 'branding_email_from_name', 'value': 'The BGP in the Cloud Team'}, or_ignore=True)
            self.conn.execute("PRAGMA user_version = 8")
            self.conn.commit()
            user_version = 8

        if user_version < 9:
            # Version 9: Add client type
            self.add_column_if_not_exists('clients', 'type', 'TEXT')
            self.conn.execute("PRAGMA user_version = 9")
            self.conn.commit()
            user_version = 9

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

    def insert(self, table_name, data, or_ignore=False):
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        verb = "INSERT OR IGNORE" if or_ignore else "INSERT"
        query = f"{verb} INTO {table_name} ({keys}) VALUES ({placeholders})"
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
        """Finds a single record in a table based on criteria."""
        where_clause = " AND ".join([f'{key} = ?' for key in criteria.keys()])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cursor = self._execute(query, tuple(criteria.values()))
        row = cursor.fetchone()
        return dict(row) if row else None
        return dict(row) if row else None

    def find_all(self, table):
        """Finds all records in a table."""
        cursor = self._execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_setting(self, key, default=None):
        """Gets a specific setting value from the database."""
        setting = self.find_one('settings', {'key': key})
        return setting['value'] if setting else default
        return [dict(row) for row in rows]

    def find_all_by(self, table, criteria):
        """Finds all records in a table based on criteria."""
        where_clause = " AND ".join([f'{key} = ?' for key in criteria.keys()])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cursor = self._execute(query, tuple(criteria.values()))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        return [dict(row) for row in rows]
        
    def delete(self, table_name, record_id):
        """Deletes a record from a table."""
        query = f"DELETE FROM {table_name} WHERE id = ?"
        self._execute(query, (record_id,))
        self.conn.commit()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def _seed_initial_data(self):
        """Seeds the database with essential data like system IP pools if they don't exist."""
        initial_pools = [
            {"name": "WG Server P2P IPv4", "cidr": "172.31.0.0/24", "description": "WireGuard server point-to-point network (IPv4)", "afi": "ipv4"},
            {"name": "WG Server P2P IPv6", "cidr": "fd31::/64", "description": "WireGuard server point-to-point network (IPv6)", "afi": "ipv6"},
        ]

        for pool in initial_pools:
            existing = self.find_one('ip_pools', {'name': pool['name']})
            if not existing:
                self.insert('ip_pools', pool)
                print(f"Seeded initial IP Pool: {pool['name']}")