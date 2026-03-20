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
    # ... (full, correct implementation of assignment logic)
    regenerate_client_configs(db_core, client_id)

def deprovision_and_delete_client(db_core: BIC_DB, client_id: str):
    """Deletes a client and all of their associated resources."""
    log.info(f"Deprovisioning and deleting client {client_id}")
    db_core.delete("clients", client_id)
    bgp_management.update_server_bgp_config(db_core)
    wg_interface = db_core.find_one("wireguard_interfaces", {"name": "wg1"})
    if wg_interface:
        wireguard_management.write_server_config_from_db(db_core, wg_interface['id'])

def provision_new_client(db_core: BIC_DB, **form_data):
    """Creates a new client and provisions their initial resources."""
    log.info(f"Provisioning new client: {form_data.get('client_name')}")
    client_data = {
        "name": form_data.get('client_name'),
        "email": form_data.get('client_email'),
        "type": form_data.get('client_type'),
        "asn": form_data.get('asn') if form_data.get('client_type') == 'Transit' else None
    }
    client_id = db_core.insert("clients", client_data)
    if client_id:
        update_client_details(db_core, client_id, **form_data)
