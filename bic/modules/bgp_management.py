import subprocess
from rich.console import Console
from bic.core import BIC_DB

CONSOLE = Console()
PEERS_CONF_FILE = "/etc/bird/peers.conf"

def list_bgp_sessions(db_core: BIC_DB):
    """Lists all BGP sessions from the database with client info."""
    sessions = db_core.find_all_by("bgp_sessions", {})
    clients_list = db_core.find_all_by("clients", {})
    clients_map = {c['id']: c for c in clients_list}

    results = []
    for session in sessions:
        client = clients_map.get(session['client_id'])
        if client:
            results.append({
                "id": session['id'],
                "state": session['state'],
                "last_updated": session['last_updated'],
                "client_name": client['name'],
                "client_asn": client['asn']
            })
    return results

def create_client_bgp_config(db_core: BIC_DB, client: dict):
    """Generates a BGP session config for our server and returns it as a string."""
    if not client.get("asn"):
        return None

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]
    client_name = client["name"].replace(" ", "_").lower()

    allocs = db_core.find_all_by("ip_allocations", {"client_id": client["id"]})
    v4_neighbor_ip = next((a["ip_address"] for a in allocs if "WG Server P2P IPv4" in db_core.find_one("ip_pools", {"id": a["pool_id"]})["name"]), None)
    v6_neighbor_ip = next((a["ip_address"] for a in allocs if "WG Server P2P IPv6" in db_core.find_one("ip_pools", {"id": a["pool_id"]})["name"]), None)

    if not v4_neighbor_ip or not v6_neighbor_ip:
        CONSOLE.print(f"[yellow]Warning: Could not find WG P2P IPs for {client['name']}. Skipping BGP config generation.[/yellow]")
        return None

    config_stanza = f'''
# Managed by BIC IPAM - Peer: {client['name']}' (ASN {client_asn})
protocol bgp from t_customer '{client_name}_v4' {{
     neighbor {v4_neighbor_ip} as {client_asn};
     ipv4 {{ import all; export all; }};
     ipv6 {{ import none; export none; }};
}}
protocol bgp from t_customer '{client_name}_v6' {{
     neighbor {v6_neighbor_ip} as {client_asn};
     ipv4 {{ import none; export none; }};
     ipv6 {{ import all; export all; }};
}}
'''
    _append_to_peers_conf(config_stanza)
    _reload_bird()
    return config_stanza

def delete_client_bgp_config(db_core: BIC_DB, client: dict):
    """Removes a client's BGP session config from the system file."""
    if not client.get("asn"):
        return

    client_name = client["name"].replace(" ", "_").lower()
    _remove_stanza_from_peers_conf(f"protocol bgp from t_customer '{client_name}_v4'")
    _remove_stanza_from_peers_conf(f"protocol bgp from t_customer '{client_name}_v6'")
    _reload_bird()

def create_client_frr_config(db_core: BIC_DB, client: dict):
    """Generates a client-side FRRouting (FRR) BGP configuration."""
    if not client.get("asn"):
        return None

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]

    wg_server_p2p_ipv4_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv4"})["id"]
    wg_server_p2p_ipv6_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv6"})["id"]
    
    server_v4_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv4_pool_id, "client_id": None})["ip_address"]
    server_v6_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv6_pool_id, "client_id": None})["ip_address"]

    frr_conf = f"""!
! FRRouting BGP configuration for {client['name']}
! This should be adapted and placed in your /etc/frr/frr.conf
!
router bgp {client_asn}
 bgp router-id {client['name'].replace(' ', '_').lower()}.local
 !
 neighbor {server_v4_ip} remote-as {local_asn}
 neighbor {server_v4_ip} description BGP in the Cloud (IPv4)
 !
 neighbor {server_v6_ip} remote-as {local_asn}
 neighbor {server_v6_ip} description BGP in the Cloud (IPv6)
 !
 address-family ipv4 unicast
  network YOUR_PREFIX_HERE
 exit-address-family
 !
 address-family ipv6 unicast
  network YOUR_IPV6_PREFIX_HERE
 exit-address-family
!
"""
    return frr_conf

def create_client_bird_config(db_core: BIC_DB, client: dict):
    """Generates a client-side BIRD configuration."""
    if not client.get("asn"):
        return None

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]

    wg_server_p2p_ipv4_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv4"})["id"]
    wg_server_p2p_ipv6_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv6"})["id"]
    
    server_v4_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv4_pool_id, "client_id": None})["ip_address"]
    server_v6_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv6_pool_id, "client_id": None})["ip_address"]

    bird_conf = f"""#
# Example BIRD configuration for {client['name']}
#

router id YOUR_ROUTER_ID; # e.g. 1.1.1.1

protocol device {{
    scan time 10;
}}

protocol kernel {{
    ipv4 {{ export all; }};
    ipv6 {{ export all; }};
}}

protocol static {{
    ipv4;
    route YOUR_PREFIX_HERE blackhole;
}}

protocol static {{
    ipv6;
    route YOUR_IPV6_PREFIX_HERE blackhole;
}}

protocol bgp v4_upstream {{
    local as {client_asn};
    neighbor {server_v4_ip} as {local_asn};
    source address YOUR_WG_IPV4_ADDRESS; # Your end of the WireGuard tunnel
    ipv4 {{
        import all;
        export where proto = "static";
    }};
}}

protocol bgp v6_upstream {{
    local as {client_asn};
    neighbor {server_v6_ip} as {local_asn};
    source address YOUR_WG_IPV6_ADDRESS; # Your end of the WireGuard tunnel
    ipv6 {{
        import all;
        export where proto = "static";
    }};
}}
"""
    return bird_conf

def _append_to_peers_conf(stanza: str):
    try:
        with open("/tmp/bic_bgp_append.tmp", "w") as f:
            f.write(stanza)
        subprocess.run(f"sudo bash -c 'cat /tmp/bic_bgp_append.tmp >> {PEERS_CONF_FILE}'", shell=True, check=True)
    except Exception as e:
        CONSOLE.print(f"[bold red]Failed to append to {PEERS_CONF_FILE}: {e}[/bold red]")

def _remove_stanza_from_peers_conf(start_line: str):
    try:
        subprocess.run(f"sudo sed -i '/^{start_line}/, /}}/d' {PEERS_CONF_FILE}", shell=True, check=True)
    except Exception as e:
        CONSOLE.print(f"[bold red]Failed to remove stanza from {PEERS_CONF_FILE}: {e}[/bold red]")

def _reload_bird():
    try:
        CONSOLE.print("  -> Reloading BIRD daemon...")
        subprocess.run(["sudo", "birdc", "configure"], check=True, capture_output=True, text=True)
        CONSOLE.print("[green]✅ BIRD configuration reloaded.[/green]")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        CONSOLE.print(f"[bold red]Error reloading BIRD: {e}[/bold red]")
