#!/usr/bin/env python
"""
This module handles the business logic for BGP peer management.
"""

import uuid
import json
import subprocess
import platform
from bic.core import BIC_DB, get_logger

log = get_logger(__name__)

def list_bgp_peers(db_core: BIC_DB, **kwargs) -> list:
    """Lists all BGP peers with their associated WireGuard tunnel name.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents a BGP peer.
    """
    log.info("Fetching all BGP peers.")
    query = """
        SELECT 
            bp.id, 
            bp.name, 
            bp.hostname, 
            bp.asn, 
            bp.enabled, 
            c.name as wireguard_tunnel
        FROM bgp_peers bp
        LEFT JOIN wireguard_peers wp ON bp.wireguard_tunnel_id = wp.id
        LEFT JOIN clients c ON wp.client_id = c.id
    """
    return db_core.query_to_dict(query)

def get_bgp_peer(db_core: BIC_DB, id: str = None, peer_id: str = None, **kwargs) -> dict | None:
    """Fetches a single BGP peer by its ID.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the BGP peer to fetch.
        peer_id: An alias for the id.
        **kwargs: Catches any unused arguments.

    Returns:
        A dictionary representing the BGP peer, or None if not found.
    """
    peer_id_to_find = id or peer_id
    return db_core.find_one("bgp_peers", {"id": peer_id_to_find})

def create_bgp_peer(db_core: BIC_DB, name: str, hostname: str, asn: int, enabled: bool = False, wireguard_tunnel_id: str = None, user: dict = None, **kwargs):
    """Creates a new BGP peer in the database.

    Args:
        db_core: An instance of the BIC_DB database core.
        name: The name of the BGP peer.
        hostname: The hostname or IP address of the peer.
        asn: The Autonomous System Number of the peer.
        enabled: Whether the peer is enabled.
        wireguard_tunnel_id: The ID of an associated WireGuard tunnel.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    log.info(f"Creating new BGP peer: {name}")
    peer_data = {
        "id": str(uuid.uuid4()),
        "name": name,
        "hostname": hostname,
        "asn": asn,
        "enabled": 1 if enabled else 0,
        "wireguard_tunnel_id": wireguard_tunnel_id if wireguard_tunnel_id else None,
    }
    peer_id = db_core.insert("bgp_peers", peer_data)
    if peer_id:
        from .user_management import add_audit_log
        actor_id = user['id'] if user else None
        add_audit_log(db_core, user_id=actor_id, action="create_bgp_peer", details=f"Created BGP peer {name} (ID: {peer_id})")
        return {"success": True}

def update_bgp_peer(db_core: BIC_DB, id: str, name: str, hostname: str, asn: int, enabled: bool = False, wireguard_tunnel_id: str = None, user: dict = None, **kwargs):
    """Updates an existing BGP peer in the database.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the BGP peer to update.
        name: The new name of the BGP peer.
        hostname: The new hostname or IP address of the peer.
        asn: The new Autonomous System Number of the peer.
        enabled: The new enabled status.
        wireguard_tunnel_id: The new associated WireGuard tunnel ID.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    log.info(f"Updating BGP peer {id} ({name})")
    update_data = {
        "name": name,
        "hostname": hostname,
        "asn": asn,
        "enabled": 1 if enabled else 0,
        "wireguard_tunnel_id": wireguard_tunnel_id if wireguard_tunnel_id else None,
    }
    db_core.update("bgp_peers", id, update_data)
    from .user_management import add_audit_log
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="update_bgp_peer", details=f"Updated BGP peer {name} (ID: {id})")
    return {"success": True}

def delete_bgp_peer(db_core: BIC_DB, id: str, user: dict = None, **kwargs):
    """Deletes a BGP peer from the database.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the BGP peer to delete.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    peer = get_bgp_peer(db_core, id)
    if not peer:
        log.error(f"Cannot delete non-existent BGP peer with ID: {id}")
        return
    
    log.warning(f"Deleting BGP peer {id} ({peer['name']})")
    db_core.delete("bgp_peers", id)
    from .user_management import add_audit_log
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="delete_bgp_peer", details=f"Deleted BGP peer {peer['name']} (ID: {id})")
    return {"success": True}

def get_bgp_summary(db_core: BIC_DB, **kwargs) -> dict:
    """Fetches BGP summary from birdc and correlates it with database peers.

    On Linux, this function executes `birdc show protocols` to get the real-time
    status of BGP sessions. It then parses the text output and correlates it
    with the list of peers from the database to provide a consolidated view.

    On non-Linux systems, it returns mock data to allow UI development.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A dictionary containing the list of correlated peer statuses, or an error message.
    """
    log.info("Fetching BGP summary.")

    if platform.system() != "Linux":
        log.warning("Cannot fetch BGP summary on a non-Linux system. Returning mock data.")
        return {
            "peers": [
                {"name": "Mock Peer 1", "hostname": "192.168.1.1", "remoteAs": 65001, "state": "Established", "peerUptime": "1d2h3m", "pfxRcd": 10},
                {"name": "Mock Peer 2", "hostname": "192.168.1.2", "remoteAs": 65002, "state": "Idle", "peerUptime": "", "pfxRcd": 0},
            ],
            "error": None
        }

    try:
        result = subprocess.run(
            ["sudo", "birdc", "show", "protocols"],
            capture_output=True, text=True, check=True
        )
        summary_data = result.stdout

        # Get peers from the database
        db_peers = {p['asn']: p for p in list_bgp_peers(db_core)}

        # Parse the birdc output
        correlated_summary = []
        for line in summary_data.splitlines():
            if "BGP" in line:
                parts = line.split()
                if len(parts) >= 6 and parts[2] == "BGP":
                    state = parts[5]
                    if state == "Established":
                        asn_str = parts[0].lstrip('p') # Assuming peer name is like p65001
                        try:
                            asn = int(asn_str)
                            db_peer_info = db_peers.get(asn, {})
                            peer_data = {
                                'name': db_peer_info.get('name', parts[0]),
                                'hostname': db_peer_info.get('hostname', 'N/A'),
                                'remoteAs': asn,
                                'state': state,
                                'peerUptime': parts[4],
                                'pfxRcd': parts[7] if len(parts) > 7 else 'N/A'
                            }
                            correlated_summary.append(peer_data)
                        except ValueError:
                            continue

        return correlated_summary

    except FileNotFoundError:
        log.error("birdc command not found. Is BIRD installed and in the system's PATH?")
        return {"error": "birdc command not found."}
    except subprocess.CalledProcessError as e:
        log.error(f"birdc command failed: {e.stderr}")
        return {"error": e.stderr}
    except Exception as e:
        log.error(f"An unexpected error occurred while fetching BGP summary: {e}")
        return {"error": str(e)}

def list_advertised_prefixes(db_core: BIC_DB, peer_id: str, **kwargs) -> list:
    """Lists all advertised prefixes for a given BGP peer.

    Args:
        db_core: An instance of the BIC_DB database core.
        peer_id: The UUID of the peer whose prefixes to list.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents an advertised prefix.
    """
    log.info(f"Fetching advertised prefixes for peer {peer_id}")
    return db_core.find_all("bgp_advertisements", {"peer_id": peer_id})

BIRD_PREFIXES_CONF = "mock_etc/bird/prefixes.conf"

def _regenerate_bird_prefixes_config(db_core: BIC_DB):
    """(Re)generates the BIRD prefixes configuration file and reconfigures BIRD.

    This internal function reads all prefix advertisements from the database,
    builds the `prefixes.conf` file, and then runs `birdc reconfigure`
    to apply the changes.

    On non-Linux systems, this function does nothing.

    Args:
        db_core: An instance of the BIC_DB database core.
    """
    if platform.system() != "Linux":
        log.warning("Skipping BIRD config regeneration on non-Linux system.")
        return

    advertisements = db_core.query_to_dict("SELECT prefix, blackholed FROM bgp_advertisements")
    
    with open(BIRD_PREFIXES_CONF, "w") as f:
        f.write("# This file is managed by the BGP in Cloud application.\n")
        f.write("# Do not edit this file manually.\n")
        for ad in advertisements:
            blackhole_keyword = " blackhole" if ad['blackholed'] else ""
            f.write(f"route {ad['prefix']}{blackhole_keyword};\n")

    try:
        subprocess.run(["sudo", "birdc", "reconfigure"], check=True)
        log.info("Successfully reconfigured BIRD.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.error(f"Failed to reconfigure BIRD: {e}")

def add_advertised_prefix(db_core: BIC_DB, peer_id: str, prefix: str, user: dict = None, **kwargs):
    """Adds a new prefix to be advertised by a BGP peer.

    This function adds the prefix to the database and then calls
    `_regenerate_bird_prefixes_config` to update the live routing configuration.

    Args:
        db_core: An instance of the BIC_DB database core.
        peer_id: The UUID of the peer that will advertise the prefix.
        prefix: The network prefix to advertise (e.g., "192.0.2.0/24").
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    log.info(f"Adding prefix {prefix} to peer {peer_id}")
    
    advertisement_data = {
        "id": str(uuid.uuid4()),
        "peer_id": peer_id,
        "prefix": prefix,
    }
    
    ad_id = db_core.insert("bgp_advertisements", advertisement_data)

    _regenerate_bird_prefixes_config(db_core)

    if ad_id:
        from .user_management import add_audit_log
        actor_id = user['id'] if user else None
        add_audit_log(db_core, user_id=actor_id, action="add_bgp_prefix", details=f"Added prefix {prefix} to peer {peer_id}")
        return {"success": True}

def delete_advertised_prefix(db_core: BIC_DB, id: str, user: dict = None, **kwargs):
    """Deletes an advertised prefix.

    This function removes the prefix from the database and then calls
    `_regenerate_bird_prefixes_config` to withdraw the route announcement.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the prefix advertisement to delete.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    advertisement = db_core.find_one("bgp_advertisements", {"id": id})
    if not advertisement:
        log.error(f"Cannot delete non-existent advertisement with ID: {id}")
        return

    log.warning(f"Deleting advertisement {id} ({advertisement['prefix']})")
    db_core.delete("bgp_advertisements", id)

    _regenerate_bird_prefixes_config(db_core)

    from .user_management import add_audit_log
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="delete_bgp_prefix", details=f"Deleted prefix {advertisement['prefix']} from peer {advertisement['peer_id']}")
    return {"success": True}

def toggle_blackhole_prefix(db_core: BIC_DB, id: str, user: dict = None, **kwargs):
    """Toggles the blackhole status of an advertised prefix.

    This function updates the prefix's `blackholed` status in the database
    and then calls `_regenerate_bird_prefixes_config` to update the live
    routing configuration, either adding or removing the `blackhole` keyword
    from the route announcement.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the prefix advertisement to modify.
        user: The user performing the action, for audit logging.
        **kwargs: Catches any unused arguments.
    """
    advertisement = db_core.find_one("bgp_advertisements", {"id": id})
    if not advertisement:
        log.error(f"Cannot toggle blackhole on non-existent advertisement with ID: {id}")
        return

    new_status = not advertisement['blackholed']
    db_core.update("bgp_advertisements", id, {"blackholed": 1 if new_status else 0})
    log.info(f"Toggled blackhole status for {advertisement['prefix']} to {new_status}")

    _regenerate_bird_prefixes_config(db_core)

    from .user_management import add_audit_log
    actor_id = user['id'] if user else None
    add_audit_log(db_core, user_id=actor_id, action="toggle_bgp_blackhole", details=f"Set blackhole to {new_status} for {advertisement['prefix']}")
    return {"success": True}


def list_all_advertised_prefixes(db_core: BIC_DB, **kwargs) -> list:
    """Lists all advertised prefixes from all peers.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents an
        advertised prefix, including the name of the peer advertising it.
    """
    log.info("Fetching all advertised prefixes.")
    query = """
        SELECT
            a.id,
            a.prefix,
            a.blackholed,
            a.created_at,
            p.name as peer_name
        FROM bgp_advertisements a
        JOIN bgp_peers p ON a.peer_id = p.id
        ORDER BY p.name, a.prefix
    """
    return db_core.query_to_dict(query)




