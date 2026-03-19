from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import network_management

def run(db_core: BIC_DB):
    """TUI for editing an IP pool's description."""
    console = Console()

    pools = db_core.find_all('ip_pools')
    if not pools:
        console.print("[yellow]There are no IP pools to edit.[/yellow]")
        return

    pool_choices = {f"{p['name']} ({p['afi']}) - {p['cidr']}": p['id'] for p in pools}
    chosen_pool_str = Prompt.ask("Choose a pool to edit", choices=list(pool_choices.keys()))
    pool_id = pool_choices[chosen_pool_str]
    
    pool = db_core.find('ip_pools', pool_id)
    
    console.print(f"\nCurrent Description: [cyan]{pool['description']}[/cyan]")
    new_description = Prompt.ask("Enter the new description")

    if Confirm.ask(f"\nUpdate description to '[yellow]{new_description}[/yellow]'?"):
        result = network_management.update_pool_description(db_core, pool_id, new_description)
        if result["success"]:
            console.print(f"\n[green]{result['message']}[/green]")
        else:
            console.print(f"\n[red]Error: {result['message']}[/red]")
    else:
        console.print("\n[yellow]Edit cancelled.[/yellow]")
