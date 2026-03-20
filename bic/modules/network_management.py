#!/usr/bin/env python

"""
This module handles the business logic for network management, including IP address
and subnet allocation from defined pools.
"""

import logging
import ipaddress
from bic.core import BIC_DB

log = logging.getLogger(__name__)

def get_next_available_ip_in_pool(db_core: BIC_DB, pool_id: str):
    """Finds and returns the next available IP address from a given pool."""
    pool = db_core.find_one("ip_pools", {"id": pool_id})
    if not pool:
        log.error(f"Cannot find IP: Pool {pool_id} not found.")
        return None

    network = ipaddress.ip_network(pool['cidr'])
    allocated_ips = {ipaddress.ip_address(a['ip_address']) for a in db_core.find_all_by("ip_allocations", {"pool_id": pool_id})}

    for ip in network.hosts():
        if ip not in allocated_ips:
            log.info(f"Found next available IP {ip} in pool {pool['name']}")
            return str(ip)
    
    log.warning(f"No available IPs in pool {pool['name']}")
    return None

def allocate_next_available_subnet(db_core: BIC_DB, pool_id: str, prefix_len: int, client_id: str, description: str):
    """Finds and allocates the next available subnet from a given pool."""
    pool = db_core.find_one("ip_pools", {"id": pool_id})
    if not pool:
        log.error(f"Cannot allocate subnet: Pool {pool_id} not found.")
        return None

    parent_network = ipaddress.ip_network(pool['cidr'])
    allocated_subnets = {ipaddress.ip_network(s['subnet']) for s in db_core.find_all_by("ip_subnets", {"pool_id": pool_id})}

    for subnet in parent_network.subnets(new_prefix=prefix_len):
        if not any(subnet.overlaps(allocated) for allocated in allocated_subnets):
            log.info(f"Allocating next available subnet {subnet} from pool {pool['name']}")
            return db_core.insert("ip_subnets", {
                "pool_id": pool_id,
                "client_id": client_id,
                "subnet": str(subnet),
                "description": description
            })

    log.warning(f"No available /%s subnets in pool {pool['name']}", prefix_len)
    return None
