#!/usr/bin/env python
"""
This module provides functions for gathering and summarizing various system,
network, and application statistics.
"""

import psutil
import shutil
import ipaddress
from bic.core import BIC_DB, get_logger, get_wan_interface

# Initialize logger
log = get_logger(__name__)

def _format_bytes(byte_count: int | None) -> str:
    """Formats a byte count into a human-readable string (B, KB, MB, GB, TB).

    Args:
        byte_count: The number of bytes to format.

    Returns:
        A formatted string with the appropriate unit, or "N/A" if input is None.
    """
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}"

def _get_database_stats(db_core: BIC_DB) -> dict:
    """Collects statistics related to the database."""
    log.info("Gathering database statistics.")
    # Use the thread-safe count method from the core
    total_clients = db_core.count("clients")
    total_pools = db_core.count("ip_pools")
    total_allocations = db_core.count("ip_allocations")
    # Count subnets by looking for allocations containing a '/'
    total_subnets = db_core.count("ip_allocations", where_clause="address LIKE ?", params=('%/%',))

    return {
        'total_clients': total_clients,
        'total_pools': total_pools,
        'total_allocations': total_allocations,
        'total_subnets': total_subnets,
    }

def _get_pool_stats(db_core: BIC_DB) -> list:
    """Collects usage statistics for each IP pool."""
    log.info("Gathering IP pool statistics.")
    pool_details = []
    pools = db_core.find_all('ip_pools')
    for pool in pools:
        try:
            network = ipaddress.ip_network(pool['cidr'])
            total_ips = network.num_addresses

            # Get all allocations for this pool
            allocations = db_core.find_all("ip_allocations", {"pool_id": pool['id']})
            
            allocated_ips_count = 0
            for alloc in allocations:
                try:
                    allocated_network = ipaddress.ip_network(alloc['address'])
                    allocated_ips_count += allocated_network.num_addresses
                except ValueError:
                    log.warning(f"Invalid address '{alloc['address']}' in pool {pool['id']} allocations.")

            usage_percentage = (allocated_ips_count / total_ips) * 100 if total_ips > 0 else 0

            pool_details.append({
                'id': pool['id'],
                'name': pool['name'],
                'cidr': pool['cidr'],
                'total_ips': total_ips,
                'allocated_ips': allocated_ips_count,
                'usage': f"{usage_percentage:.2f}%"
            })
        except Exception as e:
            log.error(f"Could not process pool {pool['id']} ({pool['name']}): {e}", exc_info=True)
            continue
    return pool_details

def _get_system_stats() -> dict:
    """Collects general system statistics like CPU, memory, and disk usage."""
    log.info("Gathering system statistics.")
    return {
        'cpu_load': psutil.cpu_percent(interval=0.1),
        'mem_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }

def _get_network_stats() -> dict:
    """Collects network I/O statistics for the primary WAN interface."""
    log.info("Gathering network statistics.")
    wan_interface = get_wan_interface()
    if wan_interface:
        net_io = psutil.net_io_counters(pernic=True).get(wan_interface)
        if net_io:
            return {
                'bytes_sent': _format_bytes(net_io.bytes_sent),
                'bytes_recv': _format_bytes(net_io.bytes_recv),
                'wan_interface': wan_interface
            }
    log.warning("Could not retrieve network statistics.")
    return {'bytes_sent': 'N/A', 'bytes_recv': 'N/A', 'wan_interface': 'N/A'}

def gather_all_statistics(db_core: BIC_DB) -> dict:
    """A master function to collect and return all system statistics.

    This function acts as an orchestrator, calling various private helper
    functions to gather different categories of statistics (database, IP pools,
    system load, network I/O). Each helper call is wrapped in its own
    try...except block to ensure that a failure in one area does not prevent
    the others from being reported.

    Args:
        db_core: An instance of the BIC_DB database core.

    Returns:
        A dictionary containing all gathered statistics. Keys for failed sections
        will have a value of 'N/A' or an empty list.
    """
    log.info("--- Starting statistics gathering run ---")
    stats = {}

    # --- Database Stats ---
    try:
        stats.update(_get_database_stats(db_core))
    except Exception as e:
        log.error(f"Could not get database stats: {e}", exc_info=True)
        stats.update({'total_clients': 'N/A', 'total_pools': 'N/A', 'total_allocations': 'N/A', 'total_subnets': 'N/A'})

    # --- Pool Usage Stats ---
    try:
        stats['pool_details'] = _get_pool_stats(db_core)
    except Exception as e:
        log.error(f"Could not get pool stats: {e}", exc_info=True)
        stats['pool_details'] = []

    # --- System Stats ---
    try:
        stats.update(_get_system_stats())
    except Exception as e:
        log.error(f"Could not get system stats: {e}", exc_info=True)
        stats.update({'cpu_load': 'N/A', 'mem_percent': 'N/A', 'disk_percent': 'N/A'})

    # --- Network Stats ---
    try:
        stats.update(_get_network_stats())
    except Exception as e:
        log.error(f"Could not get network stats: {e}", exc_info=True)
        stats.update({'bytes_sent': 'N/A', 'bytes_recv': 'N/A', 'wan_interface': 'N/A'})
    
    log.info("--- Finished statistics gathering run ---")
    return stats
