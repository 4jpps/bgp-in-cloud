from rich.prompt import Prompt
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import network_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Add New IP Pool[/bold underline]")

    pool_name = Prompt.ask("Enter a name for the new pool (e.g., 'Public Service Block 1')")
    cidr = Prompt.ask("Enter the network CIDR (e.g., 192.168.1.0/24)")
    description = Prompt.ask("Enter a description for the pool")

    result = network_management.add_pool(db_core, pool_name, cidr, description)

    if result["success"]:
        console.print(f"\n[green]{result['message']}[/green]")
    else:
        console.print(f"\n[red]Error: {result['message']}[/red]")

    Prompt.ask("\nPress Enter to continue...")
