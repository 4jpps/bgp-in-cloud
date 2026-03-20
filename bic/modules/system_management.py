#!/usr/bin/env python
"""
This module provides functions for managing system-wide settings stored in the database.
"""

from bic.core import BIC_DB, get_logger, get_db_connection
from bic.modules import client_management # Import the client management module
import ipaddress
import re
import socket
import requests
import platform
import shutil
from datetime import datetime
from pathlib import Path

# Initialize logger
log = get_logger(__name__)

def get_all_settings(db_core: BIC_DB) -> dict:
    """Loads all settings from the database 'settings' table.

    This function retrieves all key-value pairs from the settings table and
    assembles them into a single dictionary for easy access throughout the
    application.

    Args:
        db_core: An instance of the BIC_DB database core.

    Returns:
        A dictionary of all settings, or an empty dictionary if an error occurs.
    """
    log.info("Loading all settings from the database.")
    try:
        settings_list = db_core.find_all('settings')
        return {setting['key']: setting['value'] for setting in settings_list}
    except Exception as e:
        log.error(f"Failed to load settings from database: {e}", exc_info=True)
        return {}

def save_all_settings(db_core: BIC_DB, **kwargs) -> dict:
    """Validates and saves all system settings, then regenerates client configs.

    This function takes a dictionary of settings, performs validation (e.g., on
    the WireGuard endpoint), and saves them to the database. After a successful
    save, it triggers a full regeneration of all client configurations to ensure
    that any relevant changes are immediately applied.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: A dictionary of key-value pairs representing the settings to be saved.

    Returns:
        A dictionary with a "success" status and a message for the user.
    """
    log.info(f"Saving {len(kwargs)} settings to the database.")

    # Validate WireGuard endpoint
    wg_endpoint = kwargs.get('wireguard_endpoint')
    if wg_endpoint:
        is_ip_address = False
        try:
            ipaddress.ip_address(wg_endpoint)
            is_ip_address = True
        except ValueError:
            # Not an IP address, treat as a domain
            if not re.match(r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", wg_endpoint):
                return {"success": False, "message": f"Invalid WireGuard endpoint: {wg_endpoint} is not a valid IP or domain."}

        if platform.system() == "Linux":
            try:
                wan_ip = requests.get('https://api.ipify.org').text
            except requests.RequestException as e:
                log.error(f"Could not fetch public WAN IP: {e}")
                return {"success": False, "message": "Could not verify WAN IP."}
        else: # Mock for Windows
            wan_ip = "1.2.3.4"

        if is_ip_address:
            if wg_endpoint != wan_ip:
                return {"success": False, "message": f"Error: The IP {wg_endpoint} does not match the server's WAN IP {wan_ip}."}
        else: # Is a domain
            try:
                resolved_ip = socket.gethostbyname(wg_endpoint)
                if resolved_ip != wan_ip:
                    return {"success": False, "message": f"Error: The domain resolves to {resolved_ip}, but the server's WAN IP is {wan_ip}."}
            except socket.gaierror:
                return {"success": False, "message": f"Could not resolve domain: {wg_endpoint}"}

    try:
        for key, value in kwargs.items():
            if value is None:
                value = '' # Ensure we don't save None to the database
            log.debug(f"Saving setting: {key} = '{value}'")
            db_core.insert_or_replace('settings', {'key': key, 'value': str(value)})
        
        log.info("Successfully saved all settings. Now regenerating all client configs.")
        # After saving settings, trigger a regeneration of all client configs
        client_management.regenerate_all_client_configs(db_core)

        return {"success": True, "message": "Settings saved and all client configs regenerated."}
    except Exception as e:
        log.error(f"An error occurred while saving settings: {e}", exc_info=True)
        return {"success": False, "message": f"An error occurred: {e}"}

def get_audit_logs(db_core: BIC_DB, search: str = None, **kwargs) -> list:
    """Fetches audit log entries, with optional search filtering.

    Retrieves a list of all audit log events, joining with the users table to
    get the username of the actor. If a search term is provided, it filters
    the results by username, action, or details.

    Args:
        db_core: An instance of the BIC_DB database core.
        search: An optional string to filter the audit logs.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents an audit log entry.
    """
    log.info(f"Fetching audit logs with search term: {search}")
    
    query = """
        SELECT a.timestamp, u.username, a.action, a.details
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
    """
    params = []

    if search:
        query += " WHERE u.username LIKE ? OR a.action LIKE ? OR a.details LIKE ?"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    query += " ORDER BY a.timestamp DESC"

    return db_core.query_to_dict(query, tuple(params))

# --- Backup and Restore ---

def _get_backup_dir(db_core: BIC_DB) -> Path:
    backup_dir = Path(db_core.db_path).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def list_backups(db_core: BIC_DB, **kwargs) -> list:
    """Lists all available database backups in the backup directory.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, each representing a backup file with its
        filename, creation time, and size.
    """
    backup_dir = _get_backup_dir(db_core)
    backups = []
    for f in backup_dir.glob("*.db"):
        backups.append({
            "filename": f.name,
            "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            "size": f.stat().st_size,
        })
    return sorted(backups, key=lambda x: x['created_at'], reverse=True)

def create_backup(db_core: BIC_DB, **kwargs):
    """Creates a timestamped backup of the main SQLite database file.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A dictionary with a "success" status and a message for the user.
    """
    backup_dir = _get_backup_dir(db_core)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"bic_db_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename

    shutil.copyfile(db_core.db_path, backup_path)
    log.info(f"Successfully created database backup: {backup_path}")
    return {"success": True, "message": f"Backup created: {backup_filename}"}

def restore_backup(db_core: BIC_DB, filename: str, **kwargs):
    """Restores the database from a specified backup file.

    This function overwrites the current live database file with the contents
    of the selected backup file. This is a destructive operation.

    Args:
        db_core: An instance of the BIC_DB database core.
        filename: The filename of the backup to restore (e.g., "bic_db_backup_....db").
        **kwargs: Catches any unused arguments.

    Returns:
        A dictionary with a "success" status and a message for the user.
    """
    backup_dir = _get_backup_dir(db_core)
    backup_path = backup_dir / filename

    if not backup_path.exists():
        log.error(f"Backup file not found: {filename}")
        return {"success": False, "message": "Backup not found."}

    # Close the current connection to release the file lock
    db_core.conn.close()

    shutil.copyfile(backup_path, db_core.db_path)
    log.warning(f"Database successfully restored from {filename}")

    # Re-establish the connection
    db_core.conn = get_db_connection(db_core.db_path)

    return {"success": True, "message": "Database restored. It is recommended to restart the application."}
def delete_backup(db_core: BIC_DB, filename: str, **kwargs):
    """Deletes a specified database backup file.

    Args:
        db_core: An instance of the BIC_DB database core.
        filename: The filename of the backup to delete.
        **kwargs: Catches any unused arguments.

    Returns:
        A dictionary with a "success" status and a message for the user.
    """
    backup_dir = _get_backup_dir(db_core)
    backup_path = backup_dir / filename

    if not backup_path.exists():
        log.error(f"Backup file not found for deletion: {filename}")
        return {"success": False, "message": "Backup not found."}

    backup_path.unlink()
    log.info(f"Deleted database backup: {filename}")
    return {"success": True, "message": f"Backup {filename} deleted."}
