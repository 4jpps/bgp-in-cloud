import subprocess
from rich.console import Console
from bic.core import BIC_DB

PEERS_CONF_FILE = "/etc/bird/peers.conf"
CONSOLE = Console()

def create_client_bgp_config(db_core: BIC_DB, client: dict):
    """Generates a BGP session config for a client and adds it to peers.conf."""
    if not client.get("asn"):
        return  # Not a BGP client

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]
    client_name = client["name"].replace(" ", "_").lower()

    # Find the client's v4 and v6 transit IPs
    allocs = db_core.find_all_by("ip_allocations", {"client_id": client["id"]})
    v4_transit_ip = None
    v6_transit_ip = None
    for alloc in allocs:
        pool = db_core.find_one("ip_pools", {"id": alloc["pool_id"]})
        if "Transit_v4" in pool["name"]:
            v4_transit_ip = alloc["ip_address"]
        elif "Transit_v6" in pool["name"]:
            v6_transit_ip = alloc["ip_address"]

    if not v4_transit_ip or not v6_transit_ip:
        CONSOLE.print(f"[yellow]Warning: Could not find transit IPs for {client['name']}. Skipping BGP config.[/yellow]")
        return

    config_stanza = f"""
# Managed by BIC IPAM - Peer: {client['name']} (ASN {client_asn})
protocol bgp from t_customer '{client_name}_v4' {{
     neighbor {v4_transit_ip} as {client_asn};
     ipv4 {{ import all; export all; }};
     ipv6 {{ import none; export none; }};
}}
protocol bgp from t_customer '{client_name}_v6' {{
     neighbor {v6_transit_ip} as {client_asn};
     ipv4 {{ import none; export none; }};
     ipv6 {{ import all; export all; }};
}}
"""
    _append_to_peers_conf(config_stanza)
    _reload_bird()

def delete_client_bgp_config(client: dict):
    """Removes a client's BGP session config from peers.conf."""
    if not client.get("asn"):
        return

    client_name = client["name"].replace(" ", "_").lower()
    _remove_stanza_from_peers_conf(f"protocol bgp from t_customer '{client_name}_v4'")
    _remove_stanza_from_peers_conf(f"protocol bgp from t_customer '{client_name}_v6'")
    _reload_bird()

def _append_to_peers_conf(stanza: str):
    """Appends a client's BGP config to the main peers file."""
    try:
        # Use a temporary file and sudo to append
        with open("/tmp/bic_bgp_append.tmp", "w") as f:
            f.write(stanza)
        subprocess.run(
            f"sudo bash -c 'cat /tmp/bic_bgp_append.tmp >> {PEERS_CONF_FILE}'",
            shell=True, check=True
        )
    except Exception as e:
        CONSOLE.print(f"[bold red]Failed to append to {PEERS_CONF_FILE}: {e}[/bold red]")

def _remove_stanza_from_peers_conf(start_line: str):
    """Removes a multi-line stanza from the peers file."""
    try:
        # This sed command finds the starting line and deletes until the closing brace '}'
        subprocess.run(
            f"sudo sed -i '/^{start_line}/, /}}/d' {PEERS_CONF_FILE}",
            shell=True, check=True
        )
    except Exception as e:
        CONSOLE.print(f"[bold red]Failed to remove stanza from {PEERS_CONF_FILE}: {e}[/bold red]")

def manage_client_bgp_session(db_core: BIC_DB, client_id: int, bgp_action: str):
    """Web handler to enable or disable a client's BGP session."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        return {"success": False, "message": "Client not found."}

    if bgp_action == "enable":
        create_client_bgp_config(db_core, client)
        return {"success": True, "message": "BGP session enabled."}
    elif bgp_action == "disable":
        delete_client_bgp_config(client)
        return {"success": True, "message": "BGP session disabled."}
    else:
        return {"success": False, "message": "Invalid BGP action."}

def _reload_bird():
    """Reloads the BIRD daemon to apply new configurations."""
    try:
        CONSOLE.print("  -> Reloading BIRD daemon...")
        subprocess.run(["sudo", "birdc", "configure"], check=True, capture_output=True, text=True)
        CONSOLE.print("[green]✅ BIRD configuration reloaded.[/green]")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        CONSOLE.print(f"[bold red]Error reloading BIRD: {e}[/bold red]")
