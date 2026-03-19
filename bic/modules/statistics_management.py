import psutil
import shutil
import subprocess
import os
import sys
from bic.core import BIC_DB

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
    stats = {
        'system': {'cpu_load': 'N/A', 'cpu_cores': 'N/A', 'mem_percent': 'N/A', 'disk_percent': 'N/A'},
        'network': {'wan': {'bytes_sent': 'N/A', 'bytes_recv': 'N/A'}},
        'database': {'clients': 'N/A', 'ip_pools': 'N/A', 'ip_allocations': 'N/A', 'ip_subnets': 'N/A'},
        'wan_interface': 'N/A'
    }

    # --- System Stats (collected individually for robustness) ---
    try:
        stats['system']['cpu_load'] = psutil.cpu_percent(interval=0.5)
    except Exception as e:
        print(f"Could not get CPU load: {e}", file=sys.stderr)

    try:
        stats['system']['cpu_cores'] = psutil.cpu_count(logical=False)
    except Exception as e:
        print(f"Could not get CPU cores: {e}", file=sys.stderr)

    try:
        stats['system']['mem_percent'] = psutil.virtual_memory().percent
    except Exception as e:
        print(f"Could not get memory usage: {e}", file=sys.stderr)

    try:
        stats['system']['disk_percent'] = psutil.disk_usage('/').percent
    except Exception as e:
        print(f"Could not get disk usage: {e}", file=sys.stderr)

    # --- Network Stats ---
    wan_interface = _get_wan_interface()
    stats['wan_interface'] = wan_interface or 'N/A'
    if wan_interface:
        try:
            # Check for existence is mainly for Linux systems
            if os.path.exists(f"/sys/class/net/{wan_interface}"):
                net_io = psutil.net_io_counters(pernic=True).get(wan_interface)
                if net_io:
                    stats['network']['wan']['bytes_sent'] = f"{net_io.bytes_sent / 1e9:.2f} GB"
                    stats['network']['wan']['bytes_recv'] = f"{net_io.bytes_recv / 1e9:.2f} GB"
        except Exception as e:
            print(f"Could not get network stats for {wan_interface}: {e}", file=sys.stderr)

    # --- Database Stats ---
    try:
        conn = db_core.get_connection()
        stats['database']['clients'] = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        stats['database']['ip_pools'] = conn.execute("SELECT COUNT(*) FROM ip_pools").fetchone()[0]
        stats['database']['ip_allocations'] = conn.execute("SELECT COUNT(*) FROM ip_allocations").fetchone()[0]
        stats['database']['ip_subnets'] = conn.execute("SELECT COUNT(*) FROM ip_subnets").fetchone()[0]
    except Exception as e:
        print(f"Could not get database stats: {e}", file=sys.stderr)

    return stats
