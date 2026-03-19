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

    # --- System and Network stats are secondary ---
    stats['system'] = {'cpu_load': 'N/A', 'mem_percent': 'N/A'}
    try:
        stats['system']['cpu_load'] = psutil.cpu_percent(interval=0.5)
        stats['system']['mem_percent'] = psutil.virtual_memory().percent
    except Exception as e:
        print(f"Could not get system stats: {e}", file=sys.stderr)

    return stats
