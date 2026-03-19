import ipaddress
import subprocess
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import client_management, wireguard_management

console = Console()

# --- Constants for BIRD file paths ---
BIRD_PREFIXES_FILE_V4 = "/etc/bird/bic_prefixes_v4.conf"
BIRD_PREFIXES_FILE_V6 = "/etc/bird/bic_prefixes_v6.conf"
BIRD_FILTER_FILE_V4 = "/etc/bird/bic_filter_v4.conf"
BIRD_FILTER_FILE_V6 = "/etc/bird/bic_filter_v6.conf"

# --- Master BIRD Configuration Function ---

def update_bird_configs(db_core: BIC_DB):
    # ... (function content as before)
    pass

# --- Helper functions for file generation ---

def _write_bird_prefix_file(filepath, cidrs, version):
    # ... (function content as before)
    pass

def _write_bird_filter_file(filepath, version):
    # ... (function content as before)
    pass

# --- Pool Management Functions ---

def add_pool(db_core: BIC_DB, name: str, cidr: str, description: str):
    # ... (function content as before)
    pass

def delete_pool(db_core: BIC_DB, pool_id: int):
    # ... (function content as before)
    pass

def swap_pool_prefix(db_core: BIC_DB, pool_id: int, new_cidr: str):
    """Orchestrates the migration of an IP pool to a new CIDR block."""
    console.print(f"\n[bold cyan]Initiating IP Pool Swap for Pool ID: {pool_id}...[/bold cyan]")

    # 1. Validation
    try:
        new_network = ipaddress.ip_network(new_cidr)
    except ValueError:
        return {"success": False, "message": "Invalid new CIDR notation."}

    pool = db_core.find_one('ip_pools', {'id': pool_id})
    if not pool:
        return {"success": False, "message": "Pool not found."}

    old_network = ipaddress.ip_network(pool['cidr'])
    if old_network.num_addresses != new_network.num_addresses:
        return {"success": False, "message": "Prefix swap is only supported between networks of the same size."}

    # 2. Remap IP Allocations
    allocations = db_core.find_all_by('ip_allocations', {'pool_id': pool_id})
    affected_client_ids = set()
    console.print(f"  -> Remapping {len(allocations)} IP addresses from {old_network} to {new_network}...")
    for alloc in allocations:
        old_ip = ipaddress.ip_address(alloc['ip_address'])
        offset = int(old_ip) - int(old_network.network_address)
        new_ip = new_network.network_address + offset
        db_core.update('ip_allocations', alloc['id'], {'ip_address': str(new_ip)})
        if alloc['client_id']:
            affected_client_ids.add(alloc['client_id'])

    # 3. Update the Pool's CIDR in the DB
    db_core.update('ip_pools', pool_id, {'cidr': new_cidr})
    console.print("  -> Updated pool CIDR in database.")

    # 4. Regenerate Configs for all Affected Clients
    console.print(f"  -> Regenerating configurations for {len(affected_client_ids)} affected client(s)...")
    for client_id in affected_client_ids:
        client_management.regenerate_client_configs(db_core, client_id)

    # 5. Update Server-Side Services
    console.print("  -> Updating server-side daemon configurations...")
    update_bird_configs(db_core)
    
    # Find all interfaces and rewrite their configs to update peer AllowedIPs
    interfaces = db_core.find_all('wireguard_interfaces')
    for iface in interfaces:
        wireguard_management.write_server_config_from_db(db_core, iface['id'])

    console.print(f"[bold green]✅ Pool swap completed successfully.[/bold green]")
    return {"success": True, "message": f"Successfully swapped prefix for pool '{pool['name']}'."}

# --- Allocation logic and other functions omitted for brevity --- 
