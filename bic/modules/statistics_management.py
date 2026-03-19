import subprocess
import os
import psutil
import shutil
from rich.console import Console
from bic.core import BIC_DB

CONSOLE = Console()

def get_wan_interface():
    """Determines the primary public-facing network interface."""
    try:
        # Get the route to a public IP
        route_cmd = "ip route get 8.8.8.8"
        proc = subprocess.run(route_cmd, shell=True, check=True, capture_output=True, text=True)
        # The interface name is the 5th word in the output
        return proc.stdout.split()[4]
    except (subprocess.CalledProcessError, IndexError):
        return None

def get_network_stats(interface: str):
    """Gets network statistics for a given interface."""
    if not interface or not os.path.exists(f"/sys/class/net/{interface}"):
        return {"rx_bytes": "N/A", "tx_bytes": "N/A"}
    
    try:
        with open(f"/sys/class/net/{interface}/statistics/rx_bytes", "r") as f:
            rx_bytes = int(f.read().strip())
        with open(f"/sys/class/net/{interface}/statistics/tx_bytes", "r") as f:
            tx_bytes = int(f.read().strip())
        return {"rx_bytes": rx_bytes, "tx_bytes": tx_bytes}
    except (IOError, ValueError):
        return {"rx_bytes": "Error", "tx_bytes": "Error"}

def get_system_stats():
    """Gathers general system statistics like load, memory, and disk usage."""
    try:
        load_avg = psutil.getloadavg()
        mem_info = psutil.virtual_memory()
        disk_info = shutil.disk_usage("/")
        return {
            "load_avg": f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}",
            "memory_percent": mem_info.percent,
            "disk_percent": disk_info.percent,
        }
    except Exception:
        return {"load_avg": "N/A", "memory_percent": "N/A", "disk_percent": "N/A"}

def get_ipam_stats(db_core: BIC_DB):
    """Gathers statistics from the IPAM database."""
    try:
        num_clients = db_core.get_connection().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        num_pools = db_core.get_connection().execute("SELECT COUNT(*) FROM ip_pools").fetchone()[0]
        num_allocations = db_core.get_connection().execute("SELECT COUNT(*) FROM ip_allocations").fetchone()[0]
        num_subnets = db_core.get_connection().execute("SELECT COUNT(*) FROM ip_subnets").fetchone()[0]
        return {
            "clients": num_clients,
            "pools": num_pools,
            "single_ips_allocated": num_allocations,
            "subnets_allocated": num_subnets
        }
    except Exception:
        return {"clients": "N/A", "pools": "N/A", "single_ips_allocated": "N/A", "subnets_allocated": "N/A"}

def gather_all_statistics(db_core: BIC_DB):
    """A master function to collect and return all system statistics."""
    wan_interface = get_wan_interface()
    network_stats = get_network_stats(wan_interface)
    system_stats = get_system_stats()
    ipam_stats = get_ipam_stats(db_core)

    return {
        "wan_interface": wan_interface or "Not Found",
        "network": network_stats,
        "system": system_stats,
        "ipam": ipam_stats,
    }
