from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from bic.core import BIC_DB

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]List IP Pools[/bold underline]")

    pools = db_core.find_all("ip_pools")

    if not pools:
        console.print("[yellow]No IP pools found.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("CIDR")
    table.add_column("Description")

    for pool in pools:
        table.add_row(
            str(pool['id']),
            pool['name'],
            pool['cidr'],
            pool['description']
        )

    console.print(table)
    Prompt.ask("\nPress Enter to continue...")
