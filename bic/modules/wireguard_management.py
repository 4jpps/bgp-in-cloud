#!/usr/bin/env python

"""
This module handles the generation of WireGuard configurations.
"""

import logging
import subprocess
from pathlib import Path
from bic.core import BIC_DB

log = logging.getLogger(__name__)

def update_wireguard_config_for_client(db_core: BIC_DB, client_id: str):
    """Generates and saves a complete WireGuard configuration for a client."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        log.error(f"Cannot generate WireGuard config: Client {client_id} not found.")
        return

    peer = db_core.find_one("wireguard_peers", {"client_id": client_id})
    if not peer:
        # This client doesn't have a WG peer, which is a valid state.
        log.info(f"Skipping WireGuard config for client {client_id} as they have no peer.")
        return

    interface = db_core.find_one("wireguard_interfaces", {"id": peer['interface_id']})
    if not interface:
        log.error(f"Cannot generate WireGuard config: Interface {peer['interface_id']} not found for peer {peer['id']}.")
        return

    # Get settings from DB, with sensible defaults
    dns_servers = db_core.get_setting('dns_servers', '1.1.1.1, 1.0.0.1')
    server_endpoint = db_core.get_setting('wireguard_endpoint', 'SERVER_PUBLIC_IP')

    # Collect all assigned IPs and subnets for this client to build AllowedIPs
    client_ips = [a['ip_address'] for a in db_core.find_all_by('ip_allocations', {'client_id': client_id})]
    client_subnets = [s['subnet'] for s in db_core.find_all_by('ip_subnets', {'client_id': client_id})]
    allowed_ips = ", ".join(client_ips + client_subnets)

    conf = f"""[Interface]
PrivateKey = {peer['private_key']}
Address = {peer['address']}
DNS = {dns_servers}

[Peer]
PublicKey = {interface['public_key']}
Endpoint = {server_endpoint}:{interface['listen_port']}
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""
    db_core.update("clients", client_id, {"wireguard_conf": conf})
    log.info(f"Successfully generated WireGuard config for client {client_id}")

def write_server_config_from_db(db_core: BIC_DB, interface_id: str):
    """Generates the main server-side WireGuard configuration file from the database."""
    interface = db_core.find_one("wireguard_interfaces", {"id": interface_id})
    if not interface:
        log.error(f"Cannot write server config: Interface {interface_id} not found.")
        return

    peers = db_core.find_all_by("wireguard_peers", {"interface_id": interface_id})
    conf_path = Path(f"/etc/wireguard/{interface['name']}.conf")
    wan_interface = db_core.get_setting('wan_interface', 'eth0') # Get from settings

    conf = f"""[Interface]
Address = {interface['address']}
ListenPort = {interface['listen_port']}
PrivateKey = {interface['private_key']}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {wan_interface} -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {wan_interface} -j MASQUERADE

"""

    for peer in peers:
        client = db_core.find_one("clients", {"id": peer['client_id']})
        client_name = client['name'] if client else 'Unknown Client'
        conf += f"""[Peer]
# Client: {client_name}
PublicKey = {peer['public_key']}
AllowedIPs = {peer['address']}

"""
    try:
        # Write to a temporary file first, then move, to be more atomic
        tmp_path = conf_path.with_suffix('.tmp')
        tmp_path.write_text(conf)
        subprocess.run(["sudo", "mv", str(tmp_path), str(conf_path)], check=True)
        log.info(f"Successfully wrote server config to {conf_path}")
        _reload_wg_interface(interface['name'])
    except (IOError, subprocess.CalledProcessError) as e:
        log.error(f"Failed to write or reload server config {conf_path}: {e}")

def _reload_wg_interface(interface_name: str):
    """Reloads a WireGuard interface to apply new configuration."""
    try:
        log.info(f"Reloading WireGuard interface {interface_name}...")
        subprocess.run(["sudo", "wg-quick", "down", interface_name], check=False)
        subprocess.run(["sudo", "wg-quick", "up", interface_name], check=True, capture_output=True, text=True)
        log.info(f"WireGuard interface {interface_name} reloaded successfully.")
    except subprocess.CalledProcessError as e:
        log.error(f"Error reloading WireGuard interface {interface_name}: {e.stderr}")
