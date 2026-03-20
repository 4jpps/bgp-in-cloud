from typing import Optional
import ipaddress
from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management

def regenerate_client_configs(db_core: BIC_DB, client_id: int):
    """Re-generates and saves the WireGuard and BGP configs for a given client."""
    wireguard_management.update_wireguard_config_for_client(db_core, client_id)
    client = db_core.find_one("clients", {"id": client_id})
    if client and client.get("asn"):
        bgp_conf_content = bgp_management.create_client_bgp_config(db_core, client)
        if bgp_conf_content:
            db_core.update('clients', client_id, {'bgp_conf': bgp_conf_content})
    
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, client_id)
    return {"success": True, "client_id": client_id}

def update_client_details(db_core: BIC_DB, client_id: int, new_name: str, new_email: str, new_type: str):
    """Updates a client's name, email, and type."""
    db_core.update('clients', client_id, {'name': new_name, 'email': new_email, 'type': new_type})
    # After updating details, it's good practice to regenerate configs
    regenerate_client_configs(db_core, client_id)
    return {"success": True, "message": "Client details updated."}

def edit_client_from_form(db_core: BIC_DB, id: int, name: str, email: str, type: str):
    """Wrapper for web form to edit a client."""
    return update_client_details(db_core=db_core, client_id=id, new_name=name, new_email=email, new_type=type)

def deprovision_and_delete_client(db_core: BIC_DB, client_id: int):
    """De-allocates all resources and deletes a client."""
    # Deallocate all IPs
    db_core.conn.execute("DELETE FROM ip_allocations WHERE client_id = ?", (client_id,))
    # Deallocate all subnets
    db_core.conn.execute("DELETE FROM ip_subnets WHERE client_id = ?", (client_id,))
    # Get the peer before deleting it to find the interface
    peer = db_core.find_one('wireguard_peers', {'client_id': client_id})
    if peer:
        db_core.delete('wireguard_peers', peer['id'])
        # Update the server config after removing the peer
        wireguard_management.write_server_config_from_db(db_core, peer['interface_id'])
    # Delete the client
    db_core.delete("clients", client_id)
    db_core.conn.commit()
    return {"success": True, "message": "Client and all associated resources have been deleted."}

def delete_client_from_form(db_core: BIC_DB, id: int, **kwargs):
    """Wrapper for web form to delete a client."""
    return deprovision_and_delete_client(db_core=db_core, client_id=id)

def provision_new_client(db_core: BIC_DB, client_name: str, client_email: str, client_type: str, asn: Optional[int] = None, assignments: Optional[list] = None, **form_data):
    """Provisions a new client with the given details and IP assignments."""
    if assignments is None:
        assignments = []
        # Parse form data for assignments
        assignment_pool_ids = form_data.get('assignment_pool_id', [])
        assignment_types = form_data.get('assignment_type', [])
        assignment_prefixes = form_data.get('assignment_prefix', [])
        
        if not isinstance(assignment_pool_ids, list):
            assignment_pool_ids = [assignment_pool_ids]
        if not isinstance(assignment_types, list):
            assignment_types = [assignment_types]
        if not isinstance(assignment_prefixes, list):
            assignment_prefixes = [assignment_prefixes]
        
        for i in range(len(assignment_pool_ids)):
            if i < len(assignment_types) and assignment_pool_ids[i]:
                assignment = {"pool_id": int(assignment_pool_ids[i]), "type": assignment_types[i]}
                if assignment_types[i] == 'subnet' and i < len(assignment_prefixes):
                    assignment["prefix_len"] = int(assignment_prefixes[i])
                assignments.append(assignment)
    
    client_data = {"name": client_name, "email": client_email, "type": client_type}
    if asn:
        client_data["asn"] = asn
    
    client_id = db_core.insert("clients", client_data)
    
    # Auto-allocate transit IPs
    v4_transit_pool = db_core.find_one('ip_pools', {'name': 'WG Server P2P IPv4'})
    v6_transit_pool = db_core.find_one('ip_pools', {'name': 'WG Server P2P IPv6'})
    if v4_transit_pool:
        ipv4 = network_management.get_next_available_ip_in_pool(db_core, v4_transit_pool['id'])
        if ipv4:
            db_core.insert('ip_allocations', {'pool_id': v4_transit_pool['id'], 'client_id': client_id, 'ip_address': ipv4, 'description': 'Transit P2P IPv4'})
    if v6_transit_pool:
        ipv6 = network_management.get_next_available_ip_in_pool(db_core, v6_transit_pool['id'])
        if ipv6:
            db_core.insert('ip_allocations', {'pool_id': v6_transit_pool['id'], 'client_id': client_id, 'ip_address': ipv6, 'description': 'Transit P2P IPv6'})

    # Process other IP assignments
    for assignment in assignments:
        if assignment["type"] == "static":
            ip_address = network_management.get_next_available_ip_in_pool(db_core, assignment["pool_id"])
            if ip_address:
                db_core.insert('ip_allocations', {'pool_id': assignment["pool_id"], 'client_id': client_id, 'ip_address': ip_address, 'description': f"Static IP for {client_name}"})
        elif assignment["type"] == "subnet":
            prefix_len = assignment.get("prefix_len", 32)
            subnet, msg = network_management.allocate_next_available_subnet(db_core, assignment["pool_id"], prefix_len, client_id, f"Subnet for {client_name}")

    # Generate all configs
    regenerate_client_configs(db_core, client_id)
    
    return {"success": True, "client_id": client_id}
