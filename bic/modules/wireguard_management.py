#!/usr/bin/env python

"""
This module handles the generation of WireGuard configurations.
"""

import logging
import subprocess
from pathlib import Path
from bic.core import BIC_DB

log = logging.getLogger(__name__)

def get_next_available_wg_ip(db_core: BIC_DB, interface_address_range: str):
    """Calculates the next available IP address for a new WireGuard peer."""
    import ipaddress
    network = ipaddress.ip_network(interface_address_range, strict=False)
    allocated_ips = {ipaddress.ip_address(p['address'].split('/')[0]) for p in db_core.find_all('wireguard_peers')}
    
    # Start from .2, as .1 is usually the gateway
    for ip in list(network.hosts())[1:]:
        if ip not in allocated_ips:
            return f"{ip}/{network.prefixlen}"
    return None

def update_wireguard_config_for_client(db_core: BIC_DB, client_id: str):
    """Generates and saves a complete WireGuard configuration for a client."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        log.error(f"Cannot generate WireGuard config: Client {client_id} not found.")
        return

    peer = db_core.find_one("wireguard_peers", {"client_id": client_id})
    interface = db_core.find_one("wireguard_interfaces", {"name": "wg1"}) # Assumption: only one WG interface

    if not peer:
        log.info(f"No WireGuard peer found for client {client_id}. Creating a new one.")
        try:
            # Generate keys
            private_key_proc = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True)
            private_key = private_key_proc.stdout.strip()
            public_key_proc = subprocess.run(["wg", "pubkey"], input=private_key, capture_output=True, text=True, check=True)
            public_key = public_key_proc.stdout.strip()

            # Find next available IP
            next_ip = get_next_available_wg_ip(db_core, interface['address'])
            if not next_ip:
                log.error(f"Failed to create peer for client {client_id}: No available IPs in WireGuard subnet.")
                return

            peer_data = {
                "interface_id": interface['id'],
                "client_id": client_id,
                "name": client['name'],
                "public_key": public_key,
                "private_key": private_key, # Storing private key is not ideal, but required for client config
                "address": next_ip
            }
            peer_id = db_core.insert("wireguard_peers", peer_data)
            peer = db_core.find_one("wireguard_peers", {"id": peer_id})
            log.info(f"Successfully created new WireGuard peer {peer_id} for client {client_id}.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log.critical(f"Failed to generate WireGuard keys. Is 'wg' installed and in the system PATH? Error: {e}")
            return

    # Continue with config generation using the (now existing) peer
    dns_servers = db_core.get_setting('dns_servers', '1.1.1.1, 1.0.0.1')
    server_endpoint = db_core.get_setting('wireguard_endpoint', 'SERVER_PUBLIC_IP')

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
    
    # After updating a peer, the server config must be rewritten
    write_server_config_from_db(db_core, interface['id'])

def write_server_config_from_db(db_core: BIC_DB, interface_id: str):
    # ... (Implementation remains the same, but is now called correctly)
