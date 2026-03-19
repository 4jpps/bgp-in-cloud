import psutil
import shutil
import subprocess
import os
import sys
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

    # --- Pool Usage Stats ---
    try:
        pools = db_core.find_all('ip_pools')
        stats['pool_stats'] = [get_pool_usage(db_core, pool['id']) for pool in pools]
    except Exception as e:
        print(f"Could not get pool stats: {e}", file=sys.stderr)
        stats['pool_stats'] = []

    # --- System Stats ---
    try:
        stats['cpu_load'] = psutil.cpu_percent(interval=0.5)
        stats['mem_percent'] = psutil.virtual_memory().percent
        disk_usage = shutil.disk_usage("/")
        stats['disk_percent'] = disk_usage.percent
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
