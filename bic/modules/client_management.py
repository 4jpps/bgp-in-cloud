from typing import Optional
import ipaddress
from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management

def regenerate_client_configs(db_core: BIC_DB, client_id: str):
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

def update_client_details(db_core: BIC_DB, client_id: str, new_name: str, new_email: str, new_type: str, **form_data):
    """Updates a client's details and processes new IP assignments."""
    db_core.update('clients', client_id, {'name': new_name, 'email': new_email, 'type': new_type})
    
    assignment_pool_ids = form_data.get('assignment_pool_id[]', [])
    assignment_types = form_data.get('assignment_type[]', [])
    assignment_prefixes = form_data.get('assignment_prefix[]', [])

    if not isinstance(assignment_pool_ids, list): assignment_pool_ids = [assignment_pool_ids]
    if not isinstance(assignment_types, list): assignment_types = [assignment_types]
    if not isinstance(assignment_prefixes, list): assignment_prefixes = [assignment_prefixes]

    for i, pool_val in enumerate(assignment_pool_ids):
        if i < len(assignment_types) and pool_val:
            pool_id = pool_val.split('_')[0]
            assign_type = assignment_types[i]
            if assign_type == 'static':
                ip = network_management.get_next_available_ip_in_pool(db_core, pool_id)
                if ip: db_core.insert('ip_allocations', {'pool_id': pool_id, 'client_id': client_id, 'ip_address': ip, 'description': f'Static IP for {new_name}'})
            elif assign_type == 'subnet':
                prefix_len = int(assignment_prefixes[i]) if i < len(assignment_prefixes) and assignment_prefixes[i] else 32
                network_management.allocate_next_available_subnet(db_core, pool_id, prefix_len, client_id, f'Subnet for {new_name}')

    regenerate_client_configs(db_core, client_id)
    return {"success": True, "message": "Client details updated."}

def edit_client_from_form(db_core: BIC_DB, id: str, name: str, email: str, type: str, **kwargs):
    return update_client_details(db_core=db_core, client_id=id, new_name=name, new_email=email, new_type=type, **kwargs)

def deprovision_and_delete_client(db_core: BIC_DB, client_id: str):
    # This is a cascading delete, so we only need to delete the client
    db_core.delete("clients", client_id)
    bgp_management.update_server_bgp_config(db_core)
    wireguard_management.write_server_config_from_db(db_core, 1) # Assuming wg1 is always interface 1
    return {"success": True, "message": "Client and all associated resources have been deleted."}

def delete_client_from_form(db_core: BIC_DB, id: str, **kwargs):
    return deprovision_and_delete_client(db_core=db_core, client_id=id)

def provision_new_client(db_core: BIC_DB, client_name: str, client_email: str, client_type: str, asn: Optional[int] = None, **form_data):
    client_data = {"name": client_name, "email": client_email, "type": client_type}
    if asn: client_data["asn"] = asn
    
    client_id = db_core.insert("clients", client_data)
    
    # ... (rest of the logic is the same as update_client_details, so it's omitted for brevity) ...
    update_client_details(db_core, client_id, client_name, client_email, client_type, **form_data)
    return {"success": True, "client_id": client_id}
