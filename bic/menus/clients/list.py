from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from bic.core import BIC_DB

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]List Clients[/bold underline]")

    clients = db_core.find_all("clients")

    if not clients:
        console.print("[yellow]No clients found.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("ASN")

    for client in clients:
        table.add_row(
            str(client['id']),
            client['name'],
            client['email'],
            str(client['asn']) if client['asn'] else "N/A"
        )

    console.print(table)
    Prompt.ask("\nPress Enter to continue...")
