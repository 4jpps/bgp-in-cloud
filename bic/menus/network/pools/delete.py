from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import network_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Delete IP Pool[/bold underline]")

    pools = db_core.find_all('ip_pools')
    if not pools:
        console.print("[yellow]No IP pools to delete.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return

    pool_map = {p['name']: p for p in pools}
    pool_name = Prompt.ask("Choose a pool to delete", choices=list(pool_map.keys()))
    pool = pool_map[pool_name]

    if Confirm.ask(f"\nAre you sure you want to delete the pool [bold red]{pool['name']}[/bold red]? This cannot be undone.", default=False):
        result = network_management.delete_pool(db_core, pool['id'])
        if result["success"]:
            console.print(f"\n[green]{result['message']}[/green]")
        else:
            console.print(f"\n[red]Error: {result['message']}[/red]")
    else:
        console.print("\nDeletion cancelled.")

    Prompt.ask("\nPress Enter to continue...")
