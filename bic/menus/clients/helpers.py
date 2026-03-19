from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from bic.core import BIC_DB

def display_client_dossier(db_core: BIC_DB, client: dict, title_prefix="Client Dossier"):
    """Displays a standardized panel with all of a client's details."""
    console = Console()
    panel_content = f"[bold]Name[/bold]: {client['name']}\n"
    panel_content += f"[bold]Email[/bold]: {client['email']}\n"
    if client.get('asn'):
        panel_content += f"[bold]ASN[/bold]: {client['asn']}\n"

    # IP Allocations (Single)
    allocs = db_core.find_all_by('ip_allocations', {'client_id': client['id']})
    if allocs:
        panel_content += "\n[bold]Assigned IPs[/bold]:\n"
        for alloc in allocs:
            pool = db_core.find_one('ip_pools', {'id': alloc['pool_id']})
            panel_content += f"- {alloc['ip_address']} (from {pool['name']})\n"

    # Subnet Allocations
    subnets = db_core.find_all_by('ip_subnets', {'client_id': client['id']})
    if subnets:
        panel_content += "\n[bold]Assigned Subnets[/bold]:\n"
        for sub in subnets:
            pool = db_core.find_one('ip_pools', {'id': sub['pool_id']})
            panel_content += f"- {sub['subnet']} (from {pool['name']})\n"
    
    # WireGuard Info
    peer = db_core.find_one("wireguard_peers", {"client_id": client['id']})
    if peer:
        panel_content += "\n[bold]WireGuard Peer[/bold]:\n"
        panel_content += f"- Public Key: {peer['public_key']}\n"
        panel_content += f"- AllowedIPs: {peer['allowed_ips']}"

    console.print(Panel(panel_content, title=f"{title_prefix}: {client['name']}", border_style="blue", expand=False))

def get_pool_choices(db_core: BIC_DB):
    """Returns a list of formatted pool choices and a name-to-object map."""
    pools = db_core.find_all("ip_pools")
    if not pools:
        return None, None
    pool_choices = [f"{p['name']} ({p['cidr']})" for p in pools]
    pool_map = {f"{p['name']} ({p['cidr']})": p for p in pools}
    return pool_choices, pool_map
