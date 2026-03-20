#!/usr/bin/env python
"""
This module handles the business logic for client management, including provisioning,
updating, and de-provisioning clients and their associated network resources.
"""

import uuid
from bic.core import BIC_DB, get_logger
from bic.modules import bgp_management, wireguard_management, network_management
from bic.modules.email_notifications import send_client_welcome_email

# --- Constants for WireGuard IPs ---
SERVER_WG_IPV4 = "172.31.0.1"
SERVER_WG_IPV6 = "fd31::1"
CLIENT_WG_IPV4_POOL = "172.31.0.0/24"
CLIENT_WG_IPV6_POOL = "fd31::/64"

# Initialize logger
log = get_logger(__name__)

def regenerate_client_configs(db_core: BIC_DB, client_id: str):
    """Re-generates all configurations for a single client.

    This function orchestrates the regeneration of all network configurations
    for a specific client, including WireGuard and BGP. It then triggers a
    welcome email to the client with their updated configuration details.

    Args:
        db_core: An instance of the BIC_DB database core.
        client_id: The UUID of the client to regenerate configs for.
    """
    log.info(f"Regenerating all configs for client_id: {client_id}")

    # Regenerate WireGuard config first, using the new IP logic
    client_ipv4 = network_management.get_next_available_ip_in_pool(db_core, CLIENT_WG_IPV4_POOL)
    client_ipv6 = network_management.get_next_available_ip_in_pool(db_core, CLIENT_WG_IPV6_POOL)

    if not client_ipv4 or not client_ipv6:
        log.error(f"Could not allocate WireGuard IPs for client {client_id}. Aborting config generation.")
        return

    # Get all assigned subnets for the client to include in AllowedIPs
    allocations = db_core.find_all('ip_allocations', {'client_id': client_id})
    allowed_ips = [f"{client_ipv4}/32", f"{client_ipv6}/128"] + [alloc['address'] for alloc in allocations]

    wireguard_management.update_wireguard_config_for_client(
        db_core,
        client_id,
        client_ipv4=client_ipv4,
        client_ipv6=client_ipv6,
        server_ipv4=SERVER_WG_IPV4,
        server_ipv6=SERVER_WG_IPV6,
        allowed_ips=allowed_ips,
    )

    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        log.error(f"Cannot regenerate configs for non-existent client_id: {client_id}")
        return

    # If the client has an ASN, handle BGP configurations
    if client.get("asn") and client.get("bgp_session_enabled"):
        log.info(f"Client {client_id} has BGP enabled. Generating BGP configs.")
        bgp_configs = bgp_management.create_client_bgp_config(db_core, client_id)
        if bgp_configs:
            log.debug(f"Generated BGP configs for client {client_id}: {bgp_configs}")
            db_core.update('clients', client_id, {
                'bgp_frr_conf': bgp_configs.get('frr'),
                'bgp_bird_conf': bgp_configs.get('bird')
            })
        # After updating a single client's BGP, the server config must be rebuilt
        bgp_management.update_server_bgp_config(db_core)
    else:
        log.info(f"Client {client_id} does not have BGP enabled. Skipping BGP config generation.")

    # After updating a client, always regenerate the server config
    wireguard_management.update_server_wireguard_config(db_core, server_ipv4=SERVER_WG_IPV4, server_ipv6=SERVER_WG_IPV6)

    # Send the welcome email with updated configs
    send_client_welcome_email(db_core, client_id)
    log.info(f"Successfully regenerated configs for client {client_id}.")

def update_client_details(db_core: BIC_DB, client_id: str, **form_data):
    """Updates a client's core details and handles IP/subnet assignments.

    This function is typically called after a client is first created or when
    their details are edited. It updates the client's name, email, and type,
    and then processes any new IP or subnet assignments requested in the form data.

    Args:
        db_core: An instance of the BIC_DB database core.
        client_id: The UUID of the client being updated.
        **form_data: A dictionary of form data from the client provisioning/edit form.
    """
    log.info(f"Updating details for client_id: {client_id}")
    log.debug(f"Form data received: {form_data}")

    db_core.update('clients', client_id, {
        'name': form_data.get('name'),
        'email': form_data.get('email'),
        'type': form_data.get('type')
    })

    assignment_pool_ids = form_data.get('assignment_pool_id[]', [])
    assignment_types = form_data.get('assignment_type[]', [])
    assignment_prefixes = form_data.get('assignment_prefix[]', [])

    # Ensure form data is list-like for consistent processing
    if not isinstance(assignment_pool_ids, list): assignment_pool_ids = [assignment_pool_ids]
    if not isinstance(assignment_types, list): assignment_types = [assignment_types]
    if not isinstance(assignment_prefixes, list): assignment_prefixes = [assignment_prefixes]

    for i, pool_val in enumerate(assignment_pool_ids):
        if i < len(assignment_types) and pool_val:
            # This relies on the HTML value being formatted as "pool_id_some_other_info"
            pool_id = pool_val.split('_')[0]
            assign_type = assignment_types[i]
            client_name = form_data.get('name', 'Unknown')

            if assign_type == 'static':
                log.info(f"Assigning a new static IP to client {client_id} from pool {pool_id}")
                ip = network_management.get_next_available_ip_in_pool(db_core, pool_id)
                if ip:
                    db_core.insert('ip_allocations', {'id': str(uuid.uuid4()), 'pool_id': pool_id, 'client_id': client_id, 'address': ip, 'description': f'Static IP for {client_name}'})
                    log.info(f"Assigned IP {ip} to client {client_id}")
                else:
                    log.warning(f"No available IP in pool {pool_id} for client {client_id}")
            elif assign_type == 'subnet':
                prefix_len_str = assignment_prefixes[i] if i < len(assignment_prefixes) and assignment_prefixes[i] else '32'
                try:
                    prefix_len = int(prefix_len_str)
                    log.info(f"Allocating a new / {prefix_len} subnet to client {client_id} from pool {pool_id}")
                    network_management.allocate_next_available_subnet(db_core, pool_id, prefix_len, client_id, f'Subnet for {client_name}')
                except (ValueError, TypeError):
                    log.error(f"Invalid prefix length provided: {prefix_len_str}")

    # After all updates, regenerate the client's configurations
    regenerate_client_configs(db_core, client_id)

def deprovision_and_delete_client(db_core: BIC_DB, id: str, **kwargs):
    """De-provisions and deletes a client and all associated resources.

    This function ensures a clean removal of a client from the system. It
    deletes all of their IP allocations, their WireGuard peer, and finally
    the client record itself. After deletion, it triggers a regeneration of
    server-side configs to remove the client's peering information.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The UUID of the client to delete.
        **kwargs: Catches any unused arguments from the UI handler.
    """
    log.info(f"Starting de-provisioning and deletion for client_id: {id}")

    # 1. Delete IP allocations for the client
    allocations = db_core.find_all("ip_allocations", {"client_id": id})
    if allocations:
        log.info(f"Deleting {len(allocations)} IP allocations for client {id}")
        db_core.delete_many("ip_allocations", {"client_id": id})

    # 2. Delete WireGuard peer for the client
    peer = db_core.find_one("wireguard_peers", {"client_id": id})
    if peer:
        log.info(f"Deleting WireGuard peer for client {id}")
        db_core.delete("wireguard_peers", peer['id'])

    # 3. Delete the client record itself
    log.info(f"Deleting client record for client_id: {id}")
    deleted = db_core.delete("clients", id)

    if deleted:
        log.info(f"Successfully deleted client {id}. Now updating server configs.")
        # 4. Update server-side configurations to remove the client
        bgp_management.update_server_bgp_config(db_core)
        wireguard_management.update_server_wireguard_config(db_core, server_ipv4=SERVER_WG_IPV4, server_ipv6=SERVER_WG_IPV6)
    else:
        log.error(f"Failed to delete client record for client_id: {id}. Server configs may be stale.")

def provision_new_client(db_core: BIC_DB, **form_data) -> str | None:
    """Provisions a new client and all their initial resources.

    This function creates a new client record in the database. It validates
    the provided ASN if the client is a 'Transit' type. After creating the
    client, it calls `update_client_details` to handle the assignment of
    IP addresses or subnets and to trigger the initial configuration generation.

    Args:
        db_core: An instance of the BIC_DB database core.
        **form_data: A dictionary of form data from the client provisioning form.

    Returns:
        The UUID of the newly created client, or None if creation failed.
    """
    client_name = form_data.get('name')
    log.info(f"Provisioning new client: {client_name}")

    asn_str = form_data.get('asn')
    asn = None
    if form_data.get('type') == 'Transit' and asn_str:
        try:
            asn = int(asn_str)
            if not (64512 <= asn <= 65534):
                log.error(f"Invalid ASN {asn} for client {client_name}. Must be in the private range 64512-65534.")
                # In a real app, you'd want to return a proper error to the UI
                return None
        except ValueError:
            log.error(f"Invalid ASN format '{asn_str}' for client {client_name}.")
            return None

    client_data = {
        "id": str(uuid.uuid4()),
        "name": client_name,
        "email": form_data.get('email'),
        "type": form_data.get('type'),
        "asn": asn,
        "bgp_session_enabled": 1 if asn else 0
    }

    inserted_id = db_core.insert("clients", client_data)

    if inserted_id:
        log.info(f"Successfully created new client record with client_id: {inserted_id}")
        # Now that the client exists, process their IP/Subnet assignments and generate configs
        update_client_details(db_core, inserted_id, **form_data)
        return inserted_id
    else:
        log.error(f"Failed to insert new client {client_name} into the database.")
        return None

def regenerate_all_client_configs(db_core: BIC_DB):
    """Regenerates configurations for all clients in the system.

    This function is a utility that iterates through every client in the database
    and calls `regenerate_client_configs` for each one. This is useful when a
    global change (like a server IP or DNS setting) requires all client
    configurations to be updated.

    Args:
        db_core: An instance of the BIC_DB database core.
    """
    log.info("--- Starting regeneration of all client configurations ---")
    clients = db_core.find_all("clients")
    for client in clients:
        log.info(f"Regenerating configs for client_id: {client['id']}")
        try:
            regenerate_client_configs(db_core, client['id'])
        except Exception as e:
            log.error(f"Failed to regenerate configs for client {client['id']}: {e}", exc_info=True)
            continue
    wireguard_management.update_server_wireguard_config(db_core, server_ipv4=SERVER_WG_IPV4, server_ipv6=SERVER_WG_IPV6)
    log.info("--- Finished regeneration of all client configurations ---")

