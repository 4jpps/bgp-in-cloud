from typing import Optional
import ipaddress
from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management

def regenerate_client_configs(db_core: BIC_DB, client_id: int):
    """Re-generates and saves the WireGuard and BGP configs for a given client."""
    wireguard_management.update_wireguard_config_for_client(db_core, client_id)
    client = db_core.find_one("clients", {"id": client_id})
    if client and client.get("asn"):
        bgp_configs = bgp_management.create_client_bgp_config(db_core, client)
        if bgp_configs:
            db_core.update('clients', client_id, {
                'bgp_frr_conf': bgp_configs.get('frr_conf'),
                'bgp_bird_conf': bgp_configs.get('bird_conf')
            })
        bgp_management.update_server_bgp_config(db_core)
    
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, client_id)
    return {"success": True, "client_id": client_id}

def update_client_details(db_core: BIC_DB, client_id: int, new_name: str, new_email: str, new_type: str, **form_data):
    """Updates a client's details and processes new IP assignments."""
    db_core.update('clients', client_id, {'name': new_name, 'email': new_email, 'type': new_type})
    
    # Process new assignments from the form
    assignment_pool_ids = form_data.get('assignment_pool_id[]', [])
    assignment_types = form_data.get('assignment_type[]', [])
    assignment_prefixes = form_data.get('assignment_prefix[]', [])

    if not isinstance(assignment_pool_ids, list):
        assignment_pool_ids = [assignment_pool_ids]
    if not isinstance(assignment_types, list):
        assignment_types = [assignment_types]
    if not isinstance(assignment_prefixes, list):
        assignment_prefixes = [assignment_prefixes]

    for i in range(len(assignment_pool_ids)):
        if i < len(assignment_types) and assignment_pool_ids[i]:
            pool_id = int(assignment_pool_ids[i])
            assign_type = assignment_types[i]
            if assign_type == 'static':
                ip = network_management.get_next_available_ip_in_pool(db_core, pool_id)
                if ip:
                    db_core.insert('ip_allocations', {'pool_id': pool_id, 'client_id': client_id, 'ip_address': ip, 'description': f'New static IP for {new_name}'})
            elif assign_type == 'subnet':
                prefix_len = int(assignment_prefixes[i]) if i < len(assignment_prefixes) and assignment_prefixes[i] else 32
                network_management.allocate_next_available_subnet(db_core, pool_id, prefix_len, client_id, f'New subnet for {new_name}')

    regenerate_client_configs(db_core, client_id)
    return {"success": True, "message": "Client details updated."}

def edit_client_from_form(db_core: BIC_DB, id: int, name: str, email: str, type: str, **kwargs):
    """Wrapper for web form to edit a client."""
    return update_client_details(db_core=db_core, client_id=id, new_name=name, new_email=email, new_type=type, **kwargs)

def deprovision_and_delete_client(db_core: BIC_DB, client_id: int):
    """De-allocates all resources and deletes a client."""
    db_core.conn.execute("DELETE FROM ip_allocations WHERE client_id = ?", (client_id,))
    db_core.conn.execute("DELETE FROM ip_subnets WHERE client_id = ?", (client_id,))
    peer = db_core.find_one('wireguard_peers', {'client_id': client_id})
    if peer:
        db_core.delete('wireguard_peers', peer['id'])
        wireguard_management.write_server_config_from_db(db_core, peer['interface_id'])
    db_core.delete("clients", client_id)
    db_core.conn.commit()
    return {"success": True, "message": "Client and all associated resources have been deleted."}

def delete_client_from_form(db_core: BIC_DB, id: int, **kwargs):
    """Wrapper for web form to delete a client."""
    return deprovision_and_delete_client(db_core=db_core, client_id=id)

def provision_new_client(db_core: BIC_DB, client_name: str, client_email: str, client_type: str, asn: Optional[int] = None, **form_data):
    """Provisions a new client with the given details and IP assignments."""
    client_data = {"name": client_name, "email": client_email, "type": client_type}
    if asn:
        client_data["asn"] = asn
    
    client_id = db_core.insert("clients", client_data)
    
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

    # Process new assignments from the form
    assignment_pool_ids = form_data.get('assignment_pool_id[]', [])
    assignment_types = form_data.get('assignment_type[]', [])
    assignment_prefixes = form_data.get('assignment_prefix[]', [])

    if not isinstance(assignment_pool_ids, list):
        assignment_pool_ids = [assignment_pool_ids]
    if not isinstance(assignment_types, list):
        assignment_types = [assignment_types]
    if not isinstance(assignment_prefixes, list):
        assignment_prefixes = [assignment_prefixes]

    for i in range(len(assignment_pool_ids)):
        if i < len(assignment_types) and assignment_pool_ids[i]:
            pool_id = int(assignment_pool_ids[i])
            assign_type = assignment_types[i]
            if assign_type == 'static':
                ip = network_management.get_next_available_ip_in_pool(db_core, pool_id)
                if ip:
                    db_core.insert('ip_allocations', {'pool_id': pool_id, 'client_id': client_id, 'ip_address': ip, 'description': f'Static IP for {client_name}'})
            elif assign_type == 'subnet':
                prefix_len = int(assignment_prefixes[i]) if i < len(assignment_prefixes) and assignment_prefixes[i] else 32
                network_management.allocate_next_available_subnet(db_core, pool_id, prefix_len, client_id, f'Subnet for {client_name}')

    regenerate_client_configs(db_core, client_id)
    return {"success": True, "client_id": client_id}
