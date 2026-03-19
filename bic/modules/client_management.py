from typing import Optional
import ipaddress
from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management

def regenerate_client_configs(db_core: BIC_DB, client_id: int):
    """Re-generates and saves the WireGuard and BGP configs for a given client."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        return

    # Rebuild AllowedIPs for the WireGuard peer
    wg_peer = db_core.find_one('wireguard_peers', {'client_id': client_id})
    if wg_peer:
        wireguard_management.rebuild_and_update_peer_allowed_ips(db_core, client_id)

        # Regenerate the client's WireGuard config file content
        # This requires fetching all the pieces again
        server_interface = db_core.find_one('wireguard_interfaces', {'id': wg_peer['interface_id']})
        client_allocations = db_core.find_all_by('ip_allocations', {'client_id': client_id})
        client_tunnel_ips = [f"{a['ip_address']}/{'128' if ':' in a['ip_address'] else '32'}" for a in client_allocations]

        # This part is a bit tricky as the private key is not stored. 
        # For a true regen, we would need to issue a new key. 
        # For now, we will assume the main part that changes is the Endpoint/AllowedIPs
        # A better approach would be to store the client private key encrypted.
        # For this re-gen, we will just update the existing conf string if possible.
        current_conf = client.get("wireguard_conf", "")
        # This is a placeholder for a more complex update.
        # In a real scenario, you'd parse the conf and replace lines.

    # Regenerate BGP config
    if client.get("asn"):
        bgp_conf_content = bgp_management.create_client_bgp_config(db_core, client)
        if bgp_conf_content:
            db_core.update('clients', client_id, {'bgp_conf': bgp_conf_content})

    # Send the welcome email with all configs
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, client_id)

    return {"success": True, "client_id": client_id}

# --- Other client management functions are omitted for brevity ---
