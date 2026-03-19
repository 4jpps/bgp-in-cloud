from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import network_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Swap IP Pool Prefix[/bold underline]")

    pools = db_core.find_all('ip_pools')
    if not pools:
        console.print("[yellow]No IP pools to modify.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return

    pool_map = {p['name']: p for p in pools}
    pool_name = Prompt.ask("Choose a pool to swap the prefix for", choices=list(pool_map.keys()))
    pool = pool_map[pool_name]

    console.print(f"\nThe current CIDR for '{pool['name']}' is [bold cyan]{pool['cidr']}[/bold cyan].")
    new_cidr = Prompt.ask("Enter the new CIDR for this pool")

    if Confirm.ask(f"\nThis will remap all IPs in the pool from {pool['cidr']} to {new_cidr}. This can affect live services. Proceed?", default=False):
        result = network_management.swap_pool_prefix(db_core, pool['id'], new_cidr)
        if result["success"]:
            console.print(f"\n[green]{result['message']}[/green]")
        else:
            console.print(f"\n[red]Error: {result['message']}[/red]")
    else:
        console.print("\nSwap cancelled.")

    Prompt.ask("\nPress Enter to continue...")
