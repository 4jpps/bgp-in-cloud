import psutil
import shutil
import subprocess
import os
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
        'database': {'clients': 'N/A', 'ip_pools': 'N/A', 'ip_allocations': 'N/A', 'ip_subnets': 'N/A'}
    }

    # System Stats
    try:
        stats['system']['cpu_load'] = psutil.cpu_percent(interval=0.5)
        stats['system']['cpu_cores'] = psutil.cpu_count(logical=False)
        stats['system']['mem_percent'] = psutil.virtual_memory().percent
        try:
            stats['system']['disk_percent'] = shutil.disk_usage("/").percent
        except (FileNotFoundError, PermissionError):
            # Fallback for environments where root isn't accessible or doesn't exist (e.g., some containers)
            try:
                df_output = subprocess.check_output(['df', '/'], text=True)
                usage_percent = df_output.splitlines()[1].split()[-2].replace('%', '')
                stats['system']['disk_percent'] = float(usage_percent)
            except (subprocess.CalledProcessError, IndexError, ValueError):
                stats['system']['disk_percent'] = 'N/A'
    except Exception:
        pass # Defaults will be used

    # Network Stats
    try:
        wan_interface = _get_wan_interface()
        if wan_interface and os.path.exists(f"/sys/class/net/{wan_interface}"):
            net_io = psutil.net_io_counters(pernic=True).get(wan_interface)
            if net_io:
                stats['network']['wan']['bytes_sent'] = f"{net_io.bytes_sent / 1e9:.2f} GB"
                stats['network']['wan']['bytes_recv'] = f"{net_io.bytes_recv / 1e9:.2f} GB"
    except Exception:
        pass # Defaults will be used

    # Database Stats
    try:
        conn = db_core.get_connection()
        stats['database']['clients'] = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        stats['database']['ip_pools'] = conn.execute("SELECT COUNT(*) FROM ip_pools").fetchone()[0]
        stats['database']['ip_allocations'] = conn.execute("SELECT COUNT(*) FROM ip_allocations").fetchone()[0]
        stats['database']['ip_subnets'] = conn.execute("SELECT COUNT(*) FROM ip_subnets").fetchone()[0]
    except Exception:
        pass # Defaults will be used

    return stats
