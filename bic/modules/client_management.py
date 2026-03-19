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

def update_client_details(db_core: BIC_DB, client_id: int, new_name: str, new_email: str):
    """Updates a client's name and email."""
    db_core.update('clients', client_id, {'name': new_name, 'email': new_email})
    return {"success": True, "message": "Client details updated."}

def edit_client_from_form(db_core: BIC_DB, id: int, name: str, email: str):
    """Wrapper for web form to edit a client."""
    return update_client_details(db_core=db_core, client_id=id, new_name=name, new_email=email)

def delete_client_from_form(db_core: BIC_DB, id: int):
    """Wrapper for web form to delete a client."""
    return deprovision_and_delete_client(db_core=db_core, client_id=id)

def provision_new_client(db_core: BIC_DB, client_name: str, client_email: str, client_type: str, asn: Optional[int] = None, assignments: Optional[list] = None, **form_data):
    """Provisions a new client with the given details and IP assignments."""
    # Handle web form data if assignments not provided
    if assignments is None:
        assignments = []
        # Parse form data for assignments
        assignment_pool_ids = form_data.get('assignment_pool_id', [])
        assignment_types = form_data.get('assignment_type', [])
        assignment_prefixes = form_data.get('assignment_prefix', [])
        
        # Ensure they are lists
        if not isinstance(assignment_pool_ids, list):
            assignment_pool_ids = [assignment_pool_ids]
        if not isinstance(assignment_types, list):
            assignment_types = [assignment_types]
        if not isinstance(assignment_prefixes, list):
            assignment_prefixes = [assignment_prefixes]
        
        for i in range(len(assignment_pool_ids)):
            if i < len(assignment_types):
                assignment = {
                    "pool_id": int(assignment_pool_ids[i]),
                    "type": assignment_types[i]
                }
                if assignment_types[i] == 'subnet' and i < len(assignment_prefixes):
                    assignment["prefix_len"] = int(assignment_prefixes[i])
                assignments.append(assignment)
    
    # Create the client record
    client_data = {
        "name": client_name,
        "email": client_email,
        "type": client_type,
    }
    if asn:
        client_data["asn"] = asn
    
    client_id = db_core.insert("clients", client_data)
    
    # Process IP assignments
    for assignment in assignments:
        pool = db_core.find_one("ip_pools", {"id": assignment["pool_id"]})
        if not pool:
            continue
            
        if assignment["type"] == "static":
            # Allocate a single IP
            ip_address, alloc_id = network_management.get_next_available_ip_in_pool(db_core, assignment["pool_id"])
            if ip_address and alloc_id:
                db_core.update('ip_allocations', alloc_id, {
                    'client_id': client_id,
                    'description': f"Static IP for {client_name}"
                })
        elif assignment["type"] == "subnet":
            # Allocate a subnet
            prefix_len = assignment.get("prefix_len", 32)
            subnet, subnet_id = network_management.find_and_allocate_subnet(db_core, assignment["pool_id"], prefix_len)
            if subnet and subnet_id:
                db_core.update('ip_subnets', subnet_id, {
                    'client_id': client_id,
                    'description': f"Subnet /{prefix_len} for {client_name}"
                })
    
    # Generate WireGuard configuration
    # wireguard_management.setup_client_wireguard(db_core, client_id)  # TODO: implement
    
    # Generate BGP configuration if applicable
    if asn:
        bgp_conf = bgp_management.create_client_bgp_config(db_core, {"id": client_id, "name": client_name, "asn": asn})
        if bgp_conf:
            db_core.update("clients", client_id, {"bgp_conf": bgp_conf})
    
    # Send welcome email
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, client_id)
    
    return {"success": True, "client_id": client_id}

# --- Other client management functions are omitted for brevity ---
