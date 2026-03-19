from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management, email_notifications, firewall_management

def deprovision_and_delete_client(db_core: BIC_DB, client_id: int):
    """Fully deprovisions all resources for a client and then deletes them."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        return {"success": False, "message": "Client not found."}

    logs = []

    # De-provision BGP session
    if client.get('asn'):
        bgp_management.delete_client_bgp_config(client)
        logs.append("BGP session configuration removed.")

    # Deallocate all assigned subnets
    subnets = db_core.find_all_by('ip_subnets', {'client_id': client['id']})
    for sub in subnets:
        db_core.delete('ip_subnets', sub['id'])
    if subnets:
        logs.append(f"Deallocated {len(subnets)} IP subnet(s).")

    # Deallocate all assigned single IPs
    allocations = db_core.find_all_by('ip_allocations', {'client_id': client['id']})
    for alloc in allocations:
        db_core.delete('ip_allocations', alloc['id'])
    if allocations:
        logs.append(f"Deallocated {len(allocations)} single IP address(es).")

    # Delete WireGuard peer and rewrite server config
    peer = db_core.find_one("wireguard_peers", {"client_id": client['id']})
    if peer:
        wireguard_management.remove_peer_from_interface(db_core, peer['id'])
        logs.append("WireGuard peer configuration removed.")

    # Finally, delete the client
    db_core.delete('clients', client['id'])
    logs.append(f"Client '{client['name']}' has been successfully deleted.")

    return {"success": True, "logs": logs}

def update_client_details(db_core: BIC_DB, client_id: int, new_name: str, new_email: str):
    """Updates a client's name and email."""
    db_core.update('clients', client_id, {'name': new_name, 'email': new_email})
    return {"success": True, "message": "Client details updated."}

def toggle_client_smtp_access(db_core: BIC_DB, client_id: int):
    """Toggles a client's allow_smtp status and syncs firewall rules."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        return {"success": False, "message": "Client not found."}

    new_status = not client.get('allow_smtp', False)
    db_core.update('clients', client_id, {'allow_smtp': int(new_status)})

    # This requires sudo, may fail in a web context
    firewall_management.synchronize_firewall_rules(db_core)

    return {"success": True, "message": f"SMTP access for {client['name']} set to {new_status}."}

def add_subnet_to_client(db_core: BIC_DB, client_id: int, pool_id: int, prefix_len: int):
    """Allocates a new subnet to a client and updates their WireGuard config."""
    subnet_str, subnet_id = network_management.find_and_allocate_subnet(db_core, pool_id, prefix_len)

    if not subnet_str:
        return {"success": False, "message": f"Could not find an available /{prefix_len} in the selected pool."}

    db_core.update('ip_subnets', subnet_id, {'client_id': client_id})
    
    # After changing a client's subnets, we must update their AllowedIPs in WireGuard
    result = wireguard_management.rebuild_and_update_peer_allowed_ips(db_core, client_id)

    if result["success"]:
        return {"success": True, "message": f"Assigned {subnet_str} to client and updated WireGuard."}
    else:
        # The subnet is assigned, but WG failed. The message should reflect this.
        return {"success": False, "message": f"Assigned {subnet_str}, but failed to update WireGuard: {result['message']}"}




def provision_new_client(db_core: BIC_DB, client_name: str, client_email: str, client_type: str, asn: Optional[int] = None, assignments: list = []):
    """Orchestrates the creation of a new client and all associated resources."""
    # 1. Ensure server interface exists
    server_interface = wireguard_management.ensure_server_interface(db_core)
    if not server_interface:
        return {"success": False, "message": "Could not ensure WireGuard server interface."}

    # 2. Create Client DB Record
    client_id = db_core.insert("clients", {"name": client_name, "email": client_email, "asn": asn})
    new_client_data = db_core.find_one("clients", {"id": client_id})

    client_tunnel_ips = []
    server_allowed_ips = []

    # 3. Assign Transit IPs for BGP clients
    if client_type == "BGP":
        v4_transit_ip, v4_alloc_id = network_management.get_next_available_ip_in_pool_by_name(db_core, "BGP Transit IPv4")
        if v4_transit_ip:
            db_core.update('ip_allocations', v4_alloc_id, {'client_id': client_id, 'description': f'{client_name} BGP Peer'})
            client_tunnel_ips.append(f"{v4_transit_ip}/31")
            server_allowed_ips.append(f"{v4_transit_ip}/32")
        
        v6_transit_ip, v6_alloc_id = network_management.get_next_available_ip_in_pool_by_name(db_core, "BGP Transit IPv6")
        if v6_transit_ip:
            db_core.update('ip_allocations', v6_alloc_id, {'client_id': client_id, 'description': f'{client_name} BGP Peer'})
            client_tunnel_ips.append(f"{v6_transit_ip}/127")
            server_allowed_ips.append(f"{v6_transit_ip}/128")

    # 4. Process requested IP and Subnet assignments
    for assign in assignments:
        if assign['type'] == 'static':
            ip_address, alloc_id = network_management.get_next_available_ip_in_pool(db_core, assign['pool_id'])
            if ip_address:
                db_core.update('ip_allocations', alloc_id, {'client_id': client_id})
                client_tunnel_ips.append(f"{ip_address}/32")
                server_allowed_ips.append(f"{ip_address}/32")
        
        elif assign['type'] == 'subnet':
            subnet_str, subnet_id = network_management.find_and_allocate_subnet(db_core, assign['pool_id'], assign['prefix_len'])
            if subnet_str:
                db_core.update('ip_subnets', subnet_id, {'client_id': client_id})
                server_allowed_ips.append(subnet_str)

    # 5. Finalize WireGuard Peer
    wg_keys = wireguard_management.generate_keys()
    client_conf_path, peer_id = wireguard_management.add_peer_to_interface(
        db_core=db_core,
        server_interface_id=server_interface['id'],
        client_id=client_id,
        peer_name=client_name,
        peer_public_key=wg_keys['public_key'],
        peer_allowed_ips=",".join(server_allowed_ips),
        client_private_key=wg_keys['private_key'],
        client_address=",".join(client_tunnel_ips)
    )

    # 6. Create BGP Config if needed
    if client_type == "BGP":
        bgp_management.create_client_bgp_config(db_core, new_client_data)

    return {"success": True, "client_id": client_id, "conf_path": client_conf_path}

