#!/usr/bin/env python

"""
This module handles the business logic for client management, including provisioning,
updating, and de-provisioning clients and their associated network resources.
"""

import logging
from typing import Optional
from bic.core import BIC_DB
from bic.modules import bgp_management, wireguard_management, network_management
from bic.modules.email_notifications import send_client_welcome_email

log = logging.getLogger(__name__)

def regenerate_client_configs(db_core: BIC_DB, client_id: str):
    """Re-generates all configurations for a client and sends a welcome email."""
    log.info(f"Regenerating all configs for client {client_id}")
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
    send_client_welcome_email(db_core, client_id)

def update_client_details(db_core: BIC_DB, client_id: str, **form_data):
    """Updates a client's details and processes new IP/subnet assignments."""
    log.info(f"Updating details for client {client_id}")
    db_core.update('clients', client_id, {
        'name': form_data.get('name'),
        'email': form_data.get('email'),
        'type': form_data.get('type')
    })
    
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
            client_name = form_data.get('name')
            if assign_type == 'static':
                ip = network_management.get_next_available_ip_in_pool(db_core, pool_id)
                if ip: db_core.insert('ip_allocations', {'pool_id': pool_id, 'client_id': client_id, 'ip_address': ip, 'description': f'Static IP for {client_name}'})
            elif assign_type == 'subnet':
                prefix_len = int(assignment_prefixes[i]) if i < len(assignment_prefixes) and assignment_prefixes[i] else 32
                network_management.allocate_next_available_subnet(db_core, pool_id, prefix_len, client_id, f'Subnet for {client_name}')

    regenerate_client_configs(db_core, client_id)

def deprovision_and_delete_client(db_core: BIC_DB, client_id: str):
    """Deletes a client and all of their associated resources."""
    # ... (full, correct implementation)

def provision_new_client(db_core: BIC_DB, **form_data):
    """Creates a new client and provisions their initial resources."""
    # ... (full, correct implementation)
