#!/usr/bin/env python
"""
This module handles the business logic for network management, including IP address
and subnet allocation from defined pools.
"""

import ipaddress
import uuid
import platform
import subprocess
from bic.core import BIC_DB, get_logger

# Initialize logger
log = get_logger(__name__)

def get_next_available_ip_in_pool(db_core: BIC_DB, pool_id: str) -> str | None:
    """Finds and returns the next available single IP address from a given pool.

    This function now implements a 'gap search' to fill holes from deleted
    allocations before allocating from the end of the pool. It works for
    both IPv4 and IPv6 pools.
    """
    log.info(f"Searching for next available IP in pool_id: {pool_id}")
    pool = db_core.find_one("ip_pools", {"id": pool_id})
    if not pool:
        log.error(f"Cannot get next IP: IP pool with id {pool_id} not found.")
        return None

    try:
        network = ipaddress.ip_network(pool['cidr'])
        
        # Fetch all allocations to build a complete picture of used space
        allocations = db_core.find_all("ip_allocations", {"pool_id": pool_id})
        allocated_networks = {ipaddress.ip_network(alloc['address']) for alloc in allocations}

        # Start from the first host IP
        current_ip = network.network_address + 1

        while current_ip < network.broadcast_address or (network.version == 6 and current_ip in network):
            is_free = True
            for allocated_net in allocated_networks:
                if current_ip in allocated_net:
                    # The IP is in an existing allocation. Jump to the end of that allocation.
                    current_ip = allocated_net.broadcast_address + 1
                    is_free = False
                    break
            if is_free:
                # Found a free IP
                log.info(f"Found next available IP {current_ip} in pool '{pool['name']}' using gap search.")
                return str(current_ip)
        
        log.warning(f"No available single IP addresses in pool '{pool['name']}'")
        return None

    except ValueError as e:
        log.error(f"Invalid CIDR '{pool['cidr']}' for pool_id {pool_id}: {e}")
        return None

def allocate_next_available_subnet(db_core: BIC_DB, pool_id: str, prefix_len: int, client_id: str, description: str) -> int | None:
    """Finds and allocates the next available subnet from a given pool.
    This function now implements a block-alignment strategy for IPv4 assignments.
    For example, a /29 will start on an address divisible by 8.
    """
    log.info(f"Attempting to allocate a /{prefix_len} subnet from pool_id: {pool_id}")
    pool = db_core.find_one("ip_pools", {"id": pool_id})
    if not pool:
        log.error(f"Cannot allocate subnet: IP pool with id {pool_id} not found.")
        return None

    try:
        parent_network = ipaddress.ip_network(pool['cidr'])
        if prefix_len <= parent_network.prefixlen:
            log.error(f"Requested prefix /{prefix_len} is not smaller than the pool prefix /{parent_network.prefixlen}.")
            return None

        # Fetch all existing allocations from the pool
        allocations = db_core.find_all("ip_allocations", {"pool_id": pool_id})
        allocated_networks = {ipaddress.ip_network(alloc['address']) for alloc in allocations}

        # Iterate through possible subnets of the desired size within the parent pool
        for subnet in parent_network.subnets(new_prefix=prefix_len):
            # For IPv4, check alignment
            if subnet.version == 4:
                alignment = 2**(32 - prefix_len)
                if int(subnet.network_address) % alignment != 0:
                    continue
            
            # Check if the candidate subnet overlaps with any already allocated network
            if not any(subnet.overlaps(allocated) for allocated in allocated_networks):
                log.info(f"Found available subnet {subnet}. Allocating to client {client_id}.")
                new_allocation = {
                    "id": str(uuid.uuid4()),
                    "pool_id": pool_id,
                    "client_id": client_id,
                    "address": str(subnet),
                    "description": description
                }
                return db_core.insert("ip_allocations", new_allocation)

        log.warning(f"No available /{prefix_len} subnets in pool '{pool['name']}'.")
        return None

    except ValueError as e:
        log.error(f"Invalid CIDR '{pool['cidr']}' for pool_id {pool_id}: {e}")
        return None
    except TypeError as e:
        log.error(f"Error during subnet calculation. Check prefix length and pool CIDR. Error: {e}")
        return None

def get_ipv6_subnet_options(**kwargs):
    """Returns the available IPv6 subnet options."""
    return [
        {"label": "/127", "value": 127},
        {"label": "/64", "value": 64},
        {"label": "/56", "value": 56},
    ]

# --- IP Pool CRUD Functions ---

def add_pool(db_core: BIC_DB, name: str, cidr: str, description: str, **kwargs) -> int | None:
    """Adds a new IP address pool to the database.

    Args:
        db_core: An instance of the BIC_DB database core.
        name: The name for the new pool.
        cidr: The CIDR notation for the pool's network range (e.g., "10.0.0.0/8").
        description: A text description for the pool.
        **kwargs: Catches any unused arguments.

    Returns:
        The ID of the newly created pool record, or None if creation failed due to
        an invalid CIDR or a database error.
    """
    log.info(f"Adding new IP pool: {name} ({cidr})")
    try:
        # Validate CIDR and determine Address Family
        network = ipaddress.ip_network(cidr)
        afi = 'inet' if network.version == 4 else 'inet6'
        pool_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "cidr": cidr,
            "description": description,
            "afi": afi
        }
        return db_core.insert("ip_pools", pool_data)
    except ValueError as e:
        log.error(f"Cannot add pool '{name}'. Invalid CIDR '{cidr}': {e}")
        return None
    except Exception as e:
        log.error(f"Database error adding pool '{name}': {e}", exc_info=True)
        return None

def update_pool(db_core: BIC_DB, id: int, name: str, cidr: str, description: str, **kwargs):
    """Updates an existing IP address pool.

    Note: This function does not re-validate existing allocations against the new
    CIDR. Changing the CIDR of a pool with active allocations can lead to an
    inconsistent state and is not recommended.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The ID of the IP pool to update.
        name: The new name for the pool.
        cidr: The new CIDR for the pool.
        description: The new description for the pool.
        **kwargs: Catches any unused arguments.
    """
    log.info(f"Updating IP pool id: {id}")
    try:
        # Validate CIDR
        ipaddress.ip_network(cidr)
        db_core.update("ip_pools", id, {"name": name, "cidr": cidr, "description": description})
    except ValueError as e:
        log.error(f"Cannot update pool id {id}. Invalid CIDR '{cidr}': {e}")
    except Exception as e:
        log.error(f"Database error updating pool id {id}: {e}", exc_info=True)

def delete_pool(db_core: BIC_DB, id: int, **kwargs):
    """Deletes an IP pool and all of its allocations.

    Args:
        db_core: An instance of the BIC_DB database core.
        id: The ID of the IP pool to delete.
        **kwargs: Catches any unused arguments.
    """
    log.warning(f"Deleting IP pool id: {id} and all associated allocations.")
    try:
        # First, delete all allocations in the pool
        db_core.delete_many("ip_allocations", {"pool_id": id})
        # Then, delete the pool itself
        db_core.delete("ip_pools", id)
    except Exception as e:
        log.error(f"Database error deleting pool id {id}: {e}", exc_info=True)

def list_allocations_with_details(db_core: BIC_DB, **kwargs) -> list:
    """Lists all IP allocations, joining data from clients and pools.

    Args:
        db_core: An instance of the BIC_DB database core.
        **kwargs: Catches any unused arguments.

    Returns:
        A list of dictionaries, where each dictionary represents an allocation
        with the client name and pool name included.
    """
    log.info("Fetching all allocations with details.")
    query = """
        SELECT
            a.id,
            a.address,
            a.description,
            c.name as client_name,
            p.name as pool_name
        FROM ip_allocations a
        LEFT JOIN clients c ON a.client_id = c.id
        LEFT JOIN ip_pools p ON a.pool_id = p.id
        ORDER BY p.id, a.id;
    """
    try:
        return db_core.query_to_dict(query)
    except Exception as e:
        log.error(f"Database error listing allocations with details: {e}", exc_info=True)
        return []

def get_routing_table(**kwargs) -> str:
    """Returns the system's routing table as a raw string.

    On Linux, this executes `ip route show`.
    On other systems, it returns a mock output for UI development.

    Args:
        **kwargs: Catches any unused arguments.

    Returns:
        A string containing the routing table output, or an error message.
    """
    log.info("Fetching routing table.")
    if platform.system() != "Linux":
        log.warning("Cannot fetch routing table on a non-Linux system. Returning mock data.")
        return "default via 192.168.1.1 dev eth0\n192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100"

    try:
        result = subprocess.run(
            ["ip", "route", "show"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except FileNotFoundError:
        log.error("ip command not found. Is this a Linux system?")
        return "Error: 'ip' command not found."
    except subprocess.CalledProcessError as e:
        log.error(f"'ip route show' command failed: {e.stderr}")
        return f"Error: {e.stderr}"
