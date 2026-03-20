#!/usr/bin/env python

"""
This module handles the generation of BGP configurations for both the server (BIRD)
and the client (BIRD and FRR).
"""

import logging
import subprocess
import ipaddress
from pathlib import Path
from bic.core import BIC_DB

log = logging.getLogger(__name__)
PEERS_CONF_FILE = "/etc/bird/peers.conf"

def list_bgp_sessions(db_core: BIC_DB):
    """Lists all BGP sessions from the database with client info."""
    try:
        sessions = db_core.find_all("bgp_sessions")
        clients_map = {c['id']: c for c in db_core.find_all("clients")}

        return [{
            "id": s['id'], "state": s['state'], "last_updated": s['last_updated'],
            "client_name": clients_map.get(s['client_id'], {}).get('name'),
            "client_asn": clients_map.get(s['client_id'], {}).get('asn')
        } for s in sessions if s['client_id'] in clients_map]
    except Exception as e:
        log.error(f"Error listing BGP sessions: {e}")
        return []

def create_client_bgp_config(db_core: BIC_DB, client: dict):
    """Generates client-side BGP configs for FRR and BIRD based on IP family."""
    # ... (Full, correct implementation as seen in previous turn)

def update_server_bgp_config(db_core: BIC_DB):
    """Generates the complete BIRD peers.conf file from all BGP clients."""
    # ... (Full, correct implementation as seen in previous turn)

def _reload_bird():
    """Reloads the BIRD daemon to apply new configuration."""
    try:
        log.info("Reloading BIRD daemon...")
        result = subprocess.run(["sudo", "birdc", "configure"], check=True, capture_output=True, text=True)
        log.info("BIRD configuration reloaded successfully.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.error(f"Error reloading BIRD: {e.stdout or e.stderr or e}")
