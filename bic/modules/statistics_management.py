import psutil
import shutil
import subprocess
import os
import sys
import ipaddress
from bic.core import BIC_DB
from bic.modules.network_management import get_pool_usage

def _get_wan_interface():
    """Determines the primary public-facing network interface."""
    try:
        route_cmd = "ip route get 8.8.8.8"
        proc = subprocess.run(route_cmd, shell=True, check=True, capture_output=True, text=True)
        return proc.stdout.split()[4]
    except Exception:
        return None

def _format_bytes(byte_count):
    """Formats bytes into a human-readable string (KB, MB, GB)."""
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels):
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}B"

def gather_all_statistics(db_core: BIC_DB) -> dict:
    """A master function to collect and return all system statistics robustly."""
    stats = {}

    # --- Database Stats ---
    try:
        stats['total_clients'] = db_core.conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        stats['total_pools'] = db_core.conn.execute("SELECT COUNT(*) FROM ip_pools").fetchone()[0]
        stats['total_allocations'] = db_core.conn.execute("SELECT COUNT(*) FROM ip_allocations").fetchone()[0]
        stats['total_subnets'] = db_core.conn.execute("SELECT COUNT(*) FROM ip_subnets").fetchone()[0]
    except Exception as e:
        print(f"Could not get database stats: {e}", file=sys.stderr)
        stats.update({'total_clients': 'N/A', 'total_pools': 'N/A', 'total_allocations': 'N/A', 'total_subnets': 'N/A'})

    # --- Pool Usage and Availability Stats ---
    stats['pool_details'] = []
    try:
        pools = db_core.find_all('ip_pools')
        for pool in pools:
            pool_detail = get_pool_usage(db_core, pool['id'])
            try:
                network = ipaddress.ip_network(pool['cidr'])
                total_ips = network.num_addresses
                
                # Count allocated single IPs
                allocated_single_ips = db_core.conn.execute(
                    "SELECT COUNT(*) FROM ip_allocations WHERE pool_id = ?", (pool['id'],)
                ).fetchone()[0]
                pool_detail['available_single_ips'] = total_ips - allocated_single_ips

                # Count available subnets of common sizes
                allocated_subnets = [
                    ipaddress.ip_network(s['subnet'])
                    for s in db_core.find_all_by('ip_subnets', {'pool_id': pool['id']})
                ]
                
                available_subnets = {}
                prefix_key = 'ipv6_prefix_sizes' if network.version == 6 else 'ipv4_prefix_sizes'
                # Use some common defaults if not defined
                common_prefixes = {
                    'ipv4_prefix_sizes': [29, 27],
                    'ipv6_prefix_sizes': [64, 56]
                }
                for prefix_len in common_prefixes.get(prefix_key, []):
                    count = 0
                    for subnet in network.subnets(new_prefix=prefix_len):
                        is_available = True
                        for existing in allocated_subnets:
                            if subnet.overlaps(existing):
                                is_available = False
                                break
                        if is_available:
                            count += 1
                    available_subnets[f"/{prefix_len}"] = count
                pool_detail['available_subnets'] = available_subnets

            except Exception as e:
                print(f"Could not calculate availability for pool {pool['id']}: {e}", file=sys.stderr)
                pool_detail['available_single_ips'] = 'N/A'
                pool_detail['available_subnets'] = {}

            stats['pool_details'].append(pool_detail)

    except Exception as e:
        print(f"Could not get pool stats: {e}", file=sys.stderr)

    # --- System Stats ---
    try:
        stats['cpu_load'] = psutil.cpu_percent(interval=0.5)
        stats['mem_percent'] = psutil.virtual_memory().percent
        disk_usage = shutil.disk_usage("/")
        stats['disk_percent'] = (disk_usage.used / disk_usage.total) * 100
    except Exception as e:
        print(f"Could not get system stats: {e}", file=sys.stderr)
        stats.update({'cpu_load': 'N/A', 'mem_percent': 'N/A', 'disk_percent': 'N/A'})

    # --- Network Stats ---
    try:
        wan_interface = _get_wan_interface()
        if wan_interface:
            net_io = psutil.net_io_counters(pernic=True).get(wan_interface)
            stats['bytes_sent'] = _format_bytes(net_io.bytes_sent)
            stats['bytes_recv'] = _format_bytes(net_io.bytes_recv)
        else:
            stats.update({'bytes_sent': 'N/A', 'bytes_recv': 'N/A'})
    except Exception as e:
        print(f"Could not get network stats: {e}", file=sys.stderr)
        stats.update({'bytes_sent': 'N/A', 'bytes_recv': 'N/A'})

    return stats
