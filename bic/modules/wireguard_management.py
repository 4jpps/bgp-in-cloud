#!/usr/bin/env python
"""
This module handles the generation of WireGuard configurations.
"""

import logging
import subprocess
import ipaddress
import os
import uuid
from pathlib import Path
from bic.core import BIC_DB, get_logger

log = get_logger(__name__)
WG_CONF_DIR = Path("/etc/wireguard")

def update_wireguard_config_for_client(db_core: BIC_DB, client_id: str, client_ipv4: str, client_ipv6: str, server_ipv4: str, server_ipv6: str, allowed_ips: list):
    """Generates and saves a complete WireGuard configuration for a client."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        log.error(f"Cannot generate WireGuard config: Client {client_id} not found.")
        return

    # The server interface holds the endpoint info
    server_interfaces = db_core.find_all("server_interfaces")
    if not server_interfaces:
        log.error("Cannot generate client config: No server interface is defined.")
        return
    server_interface = server_interfaces[0]

    peer = db_core.find_one("wireguard_peers", {"client_id": client_id})

    # If peer doesn't exist, create it with new keys
    if not peer:
        log.info(f"No WireGuard peer found for client {client_id}. Creating a new one.")
        try:
            private_key_proc = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True)
            client_private_key = private_key_proc.stdout.strip()
            public_key_proc = subprocess.run(["wg", "pubkey"], input=client_private_key, capture_output=True, text=True, check=True)
            client_public_key = public_key_proc.stdout.strip()

            peer_data = {
                "id": str(uuid.uuid4()),
                "client_id": client_id,
                "client_public_key": client_public_key,
                "client_private_key": client_private_key,
                "allowed_ips": ", ".join(allowed_ips),
            }
            peer_id = db_core.insert("wireguard_peers", peer_data)
            peer = db_core.find_one("wireguard_peers", {"id": peer_id})
            log.info(f"Successfully created new WireGuard peer {peer_id} for client {client_id}.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log.critical(f"Failed to generate WireGuard keys. Is 'wg' installed and in the system PATH? Error: {e}")
            return

    # Update existing peer
    db_core.update("wireguard_peers", peer['id'], {"allowed_ips": ", ".join(allowed_ips)})

    # Get settings for the config file
    dns_servers = db_core.get_setting('dns_servers', '1.1.1.1, 1.0.0.1')
    server_endpoint = db_core.get_setting('wireguard_endpoint', 'SERVER_PUBLIC_IP') # User must configure this

    client_conf_str = f"""[Interface]
PrivateKey = {peer['client_private_key']}
Address = {client_ipv4}/32, {client_ipv6}/128
DNS = {dns_servers}

[Peer]
PublicKey = {server_interface['public_key']}
Endpoint = {server_endpoint}:{server_interface['listen_port']}
AllowedIPs = {server_ipv4}/32, {server_ipv6}/128
PersistentKeepalive = 25
"""
    db_core.update("wireguard_peers", peer['id'], {"client_conf": client_conf_str})
    log.info(f"Successfully generated WireGuard config for client {client_id}")
    
    # After updating a client, always regenerate the server config
    update_server_wireguard_config(db_core)

def update_server_wireguard_config(db_core: BIC_DB, server_ipv4: str, server_ipv6: str):
    """Generates the main server-side WireGuard configuration file from the database."""
    server_interfaces = db_core.find_all("server_interfaces")
    if not server_interfaces:
        log.error("Cannot write server config: No server interface defined.")
        return
    server_interface = server_interfaces[0]

    peers = db_core.find_all("wireguard_peers")
    conf_path = WG_CONF_DIR / f"{server_interface['name']}.conf"
    wan_interface = db_core.get_setting('wan_interface', 'eth0')

    conf = f"""[Interface]
Address = {server_ipv4}/24, {server_ipv6}/64
ListenPort = {server_interface['listen_port']}
PrivateKey = {server_interface['private_key']}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {wan_interface} -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {wan_interface} -j MASQUERADE

"""

    for peer in peers:
        client = db_core.find_one("clients", {"id": peer['client_id']})
        client_name = client['name'] if client else 'Unknown Client'
        conf += f"""# Client: {client_name} (ID: {peer['client_id']})
[Peer]
PublicKey = {peer['client_public_key']}
AllowedIPs = {peer['allowed_ips']}

"""
    try:
        conf_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = conf_path.with_suffix('.tmp')
        tmp_path.write_text(conf)
        # Using os.rename for atomic move, as sudo might not be available in test env
        os.rename(tmp_path, conf_path)
        log.info(f"Successfully wrote server config to {conf_path}")
        _reload_wg_interface(server_interface['name'])
    except (IOError, OSError, subprocess.CalledProcessError) as e:
        log.error(f"Failed to write or reload server config {conf_path}: {e}")

def _reload_wg_interface(interface_name: str):
    """Reloads a WireGuard interface to apply new configuration."""
    try:
        log.info(f"Reloading WireGuard interface {interface_name}...")
        # Use wg syncconf for a more graceful reload
        with open(WG_CONF_DIR / f"{interface_name}.conf", 'r') as f:
            conf_content = f.read()
            subprocess.run(["sudo", "wg", "syncconf", interface_name], input=conf_content, text=True, check=True, capture_output=True)
        log.info(f"WireGuard interface {interface_name} reloaded successfully.")
    except (IOError, subprocess.CalledProcessError) as e:
        log.error(f"Error reloading WireGuard interface {interface_name}: {getattr(e, 'stderr', e)}")

def force_reload_wireguard_server(db_core: BIC_DB, **kwargs):
    """Triggers a WireGuard server reload. Intended for UI actions."""
    log.info("Force-reloading WireGuard server configuration via UI action.")
    update_server_wireguard_config(db_core)

def get_server_wireguard_config(db_core: BIC_DB, **kwargs) -> dict:
    """Reads the content of the WireGuard server configuration file."""
    server_interface = db_core.find_one("server_interfaces")
    if not server_interface or not server_interface.get('name'):
        return {"title": "WireGuard Server Config", "content": "# No server interface configured"}
    
    if_name = server_interface['name']
    config_file = WG_CONF_DIR / f"{if_name}.conf"
    log.info(f"Reading WireGuard server config from {config_file}")
    try:
        content = config_file.read_text()
        return {"title": f"WireGuard Server Config ({if_name}.conf)", "content": content}
    except FileNotFoundError:
        log.warning(f"WireGuard server config file not found at {config_file}")
        return {"title": f"WireGuard Server Config ({if_name}.conf)", "content": "# File not found"}
    except Exception as e:
        log.error(f"Error reading WireGuard server config: {e}", exc_info=True)
        return {"title": f"WireGuard Server Config ({if_name}.conf)", "content": f"# Error reading file: {e}"}

def list_wireguard_peers(db_core: BIC_DB, **kwargs) -> list:
    """Lists all WireGuard peers with their associated client name."""
    log.info("Fetching all WireGuard peers with client names.")
    query = """
        SELECT 
            wp.id, 
            wp.client_id, 
            c.name as client_name, 
            wp.client_public_key, 
            wp.allowed_ips
        FROM wireguard_peers wp
        LEFT JOIN clients c ON wp.client_id = c.id
    """
    return db_core.query_to_dict(query)

def get_client_wireguard_config(db_core: BIC_DB, client_id: str) -> dict | None:
    """Gets a specific client's WireGuard configuration."""
    log.info(f"Fetching WireGuard config for client {client_id}")
    peer = db_core.find_one("wireguard_peers", {"client_id": client_id})
    if not peer or not peer.get('client_conf'):
        log.warning(f"No WireGuard config found for client {client_id}")
        return None
    
    client = db_core.find_one("clients", {"id": client_id})
    client_name = client['name'] if client else 'Unknown'
    
    return {
        "filename": f"{client_name.replace(' ', '_')}.conf",
        "content": peer['client_conf']
    }


def get_wireguard_peers_for_dropdown(db_core: BIC_DB, **kwargs) -> list:
    """Returns a list of WireGuard peers formatted for a select dropdown."""
    peers = list_wireguard_peers(db_core)
    return [{'value': peer['id'], 'label': f"{peer['client_name']} ({peer['allowed_ips']})"} for peer in peers]

