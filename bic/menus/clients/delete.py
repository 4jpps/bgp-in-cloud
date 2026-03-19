from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.menus.clients.helpers import display_client_dossier
from bic.modules import client_management

def run(db_core: BIC_DB):
    """TUI for deleting a client."""
    console = Console()
    console.print("\n[bold underline]Delete Client[/bold underline]")

    clients = db_core.find_all("clients")
    if not clients:
        console.print("[yellow]No clients to delete.[/yellow]")
        return

    client_map = {c['name']: c for c in clients}
    client_name = Prompt.ask("Choose a client to delete", choices=list(client_map.keys()))
    client = client_map[client_name]

    display_client_dossier(db_core, client, title_prefix="Deletion Candidate")

    if Confirm.ask(f"\nAre you sure you want to permanently delete [bold red]{client['name']}[/bold red]? This is irreversible.", default=False):
        with console.status("[bold cyan]Deprovisioning services...") as status:
            result = client_management.deprovision_and_delete_client(db_core, client['id'])
            
            if result["success"]:
                for log in result["logs"]:
                    console.print(f"  -> {log}")
                console.print(f"\n[green]✅ Client '{client['name']}' has been successfully deleted.[/green]")
            else:
                console.print(f"[bold red]Error:[/bold red] {result['message']}")
    else:
        console.print("\nDeletion cancelled.")
