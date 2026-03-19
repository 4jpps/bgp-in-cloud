import ipaddress
import subprocess
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import client_management, wireguard_management, system_management

def get_pool_usage(db_core: BIC_DB, pool_id: int):
    """Calculates the usage percentage of a given IP pool."""
    pool = db_core.find_one('ip_pools', {'id': pool_id})
    if not pool:
        return {"name": "Unknown", "usage": 0}

    try:
        network = ipaddress.ip_network(pool['cidr'])
        total_ips = network.num_addresses
        allocated_ips = db_core.conn.execute(
            "SELECT COUNT(*) FROM ip_allocations WHERE pool_id = ?", (pool_id,)
        ).fetchone()[0]
        
        usage = (allocated_ips / total_ips) * 100 if total_ips > 0 else 0
        return {"name": pool['name'], "usage": usage}
    except Exception as e:
        print(f"Error calculating usage for pool {pool_id}: {e}")
        return {"name": pool.get('name', 'Unknown'), "usage": 0}
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

def get_next_available_ip_in_pool(db_core: BIC_DB, pool_id: int):
    """Finds the next available IP address in a pool without allocating it."""
    pool = db_core.find_one('ip_pools', {'id': pool_id})
    if not pool:
        return None

    network = ipaddress.ip_network(pool['cidr'])
    allocated_ips = {
        ipaddress.ip_address(row['ip_address'])
        for row in db_core.find_all_by('ip_allocations', {'pool_id': pool_id})
    }

    for ip in network.hosts():
        if ip not in allocated_ips:
            return str(ip) # Return the first free IP

    return None

def find_and_allocate_subnet(db_core: BIC_DB, pool_id: int, prefix_len: int):
    """
    Finds and allocates the next available subnet of a given prefix length within a pool.
    """
    pool = db_core.find_one('ip_pools', {'id': pool_id})
    if not pool:
        return None, None

    parent_network = ipaddress.ip_network(pool['cidr'])
    if prefix_len <= parent_network.prefixlen:
        return None, None # Requested subnet is larger than or equal to the pool

    # Get all existing subnets in this pool
    existing_subnets = [
        ipaddress.ip_network(s['subnet'])
        for s in db_core.find_all_by('ip_subnets', {'pool_id': pool_id})
    ]

    # Iterate through possible subnets
    for subnet in parent_network.subnets(new_prefix=prefix_len):
        is_available = True
        for existing in existing_subnets:
            if subnet.overlaps(existing):
                is_available = False
                break
        
        if is_available:
            # Found an available subnet, allocate it
            new_subnet_data = {
                'subnet': str(subnet),
                'pool_id': pool_id,
                'client_id': None,
                'description': f'Allocated subnet from pool {pool["name"]}'
            }
            subnet_id = db_core.insert('ip_subnets', new_subnet_data)
            return str(subnet), subnet_id

    return None, None

def find_and_allocate_subnet_from_form(db_core: BIC_DB, pool_id: int, prefix_len: int, client_id: int = None):
    """Wrapper for UI form to find and allocate a subnet."""
    subnet, subnet_id = find_and_allocate_subnet(db_core, int(pool_id), int(prefix_len))
    if subnet and client_id:
        db_core.update('ip_subnets', subnet_id, {'client_id': int(client_id)})
    return {"success": bool(subnet), "message": f"Allocated {subnet}" if subnet else "Failed to allocate subnet."}

def get_next_available_ip_from_form(db_core: BIC_DB, pool_id: int, client_id: int = None):
    """Wrapper for UI form to get the next available IP."""
    ip = get_next_available_ip_in_pool(db_core, int(pool_id))
    if ip and client_id:
        db_core.insert('ip_allocations', {
            'pool_id': int(pool_id),
            'client_id': int(client_id),
            'ip_address': ip,
            'description': f'Static IP for client #{client_id}'
        })
    return {"success": bool(ip), "message": f"Allocated {ip}" if ip else "Failed to allocate IP."}

def edit_pool_from_form(db_core: BIC_DB, id: int, name: str, cidr: str, description: str):
    """Wrapper for UI form to edit a pool."""
    # This is a placeholder for a more complex update logic if needed
    db_core.update('ip_pools', id, {'name': name, 'cidr': cidr, 'description': description})
    update_bird_configs(db_core)
    return {"success": True, "message": "Pool updated successfully."}

def delete_pool_from_form(db_core: BIC_DB, id: int):
    """Wrapper for UI form to delete a pool."""
    return delete_pool(db_core=db_core, pool_id=int(id))

    return [dict(row) for row in rows]

def allocate_next_available_subnet(db_core: BIC_DB, pool_id: int, prefix_len: int, client_id: int, description: str):
    """Finds the next available subnet and allocates it to a client."""
    pool = db_core.find_one("ip_pools", {"id": pool_id})
    if not pool:
        return None, "Pool not found."
    
    parent_network = ipaddress.ip_network(pool['cidr'])
    existing_subnets = [ipaddress.ip_network(s['subnet']) for s in db_core.find_all_by('ip_subnets', {'pool_id': pool_id})]

    for candidate_subnet in parent_network.subnets(new_prefix=prefix_len):
        is_available = True
        for existing in existing_subnets:
            if candidate_subnet.overlaps(existing):
                is_available = False
                break
        if is_available:
            # Found a free subnet, allocate it
            new_subnet = {
                'pool_id': pool_id,
                'client_id': client_id,
                'subnet': str(candidate_subnet),
                'description': description
            }
            db_core.insert('ip_subnets', new_subnet)
            return str(candidate_subnet), "Subnet allocated successfully."

    return None, "No available subnets of the requested size."

def deallocate_and_remove(db_core: BIC_DB, assignment_type: str, assignment_id: int):
    """Deallocates an IP or subnet and removes it from the database."""
    if assignment_type == 'ip':
        db_core.delete('ip_allocations', assignment_id)
        return {"success": True, "message": "IP allocation removed."}
    elif assignment_type == 'subnet':
        db_core.delete('ip_subnets', assignment_id)
        return {"success": True, "message": "Subnet allocation removed."}
    return {"success": False, "message": "Invalid assignment type."}

def find_free_ip_for_web(db_core: BIC_DB, pool_id: int):
    """Web UI wrapper to find the next available IP and return a result."""
    ip = get_next_available_ip_in_pool(db_core, int(pool_id))
    return {"success": bool(ip), "message": f"Found free IP: {ip}" if ip else "No free IPs available."}

def list_all_allocations_joined(db_core: BIC_DB):
    """Lists all IP allocations and joins them with pool and client info."""
    query = '''
        SELECT
            a.id, a.ip_address, a.description,
            p.name as pool_name,
            c.name as client_name
        FROM ip_allocations a
        LEFT JOIN ip_pools p ON a.pool_id = p.id
        LEFT JOIN clients c ON a.client_id = c.id
    '''
    rows = db_core.conn.execute(query).fetchall()
    return [dict(row) for row in rows]
# --- Allocation logic and other functions omitted for brevity --- 
