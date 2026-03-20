#!/usr/bin/env python

"""
This module handles the business logic for WireGuard configuration management.
"""

import logging
from pathlib import Path
from bic.core import BIC_DB, get_wan_ip

log = logging.getLogger(__name__)

def update_wireguard_config_for_client(db_core: BIC_DB, client_id: str):
    """Generates and saves a WireGuard configuration for a given client."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        log.error(f"Cannot generate WireGuard config: Client {client_id} not found.")
        return

    peer = db_core.find_one("wireguard_peers", {"client_id": client_id})
    if not peer:
        log.error(f"Cannot generate WireGuard config: Peer for client {client_id} not found.")
        return

    interface = db_core.find_one("wireguard_interfaces", {"id": peer['interface_id']})
    if not interface:
        log.error(f"Cannot generate WireGuard config: Interface {peer['interface_id']} not found.")
        return

    wan_ip = get_wan_ip() or "SERVER_PUBLIC_IP"
    allowed_ips = ", ".join(filter(None, ["10.10.10.0/24", "172.30.0.0/16", peer.get('allowed_ips')]))

    conf = f"""[Interface]
PrivateKey = {peer['private_key']}
Address = {peer['address']}
DNS = 1.1.1.1

[Peer]
PublicKey = {interface['public_key']}
Endpoint = {wan_ip}:{interface['listen_port']}
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""
    db_core.update("clients", client_id, {"wireguard_conf": conf})
    log.info(f"Successfully generated WireGuard config for client {client_id}")

def write_server_config_from_db(db_core: BIC_DB, interface_id: str):
    """Generates the main server-side WireGuard configuration file."""
    interface = db_core.find_one("wireguard_interfaces", {"id": interface_id})
    if not interface:
        log.error(f"Cannot write server config: Interface {interface_id} not found.")
        return

    peers = db_core.find_all_by("wireguard_peers", {"interface_id": interface_id})
    
    conf_path = Path(f"/etc/wireguard/{interface['name']}.conf")
    log.info(f"Writing server config to {conf_path}")

    conf = f"""[Interface]
Address = {interface['address']}
ListenPort = {interface['listen_port']}
PrivateKey = {interface['private_key']}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

"""

    for peer in peers:
        conf += f"""[Peer]
# Client: {peer['name']}
PublicKey = {peer['public_key']}
AllowedIPs = {peer['allowed_ips']}

"""
    try:
        conf_path.write_text(conf)
        log.info(f"Successfully wrote server config to {conf_path}")
    except IOError as e:
        log.error(f"Failed to write server config to {conf_path}: {e}")
