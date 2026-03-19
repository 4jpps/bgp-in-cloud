
from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import client_management, email_notifications, bgp_management
from bic.menus.clients.helpers import display_client_dossier, get_pool_choices

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Edit Client[/bold underline]")

    clients = db_core.find_all("clients")
    if not clients:
        console.print("[yellow]No clients to edit.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return

    client_map = {c['name']: c for c in clients}
    client_name = Prompt.ask("Choose a client to edit", choices=list(client_map.keys()))
    client_id = client_map[client_name]['id']

    while True:
        client = db_core.find_one('clients', {'id': client_id})
        if not client:
            console.print("[red]Client not found.[/red]")
            break

        display_client_dossier(db_core, client)
        
        action_choices = ["Modify Name/Email", "Add Service Subnet"]
        if client.get('asn'):
            action_choices.append("Manage BGP Session")
        action_choices.extend(["Manage SMTP Access", "View Email Log", "Resend Welcome Kit", "Back to main menu"])

        action = Prompt.ask("\nChoose an action", choices=action_choices, default="Back to main menu")

        if action == "Modify Name/Email":
            new_name = Prompt.ask("Enter new name", default=client['name'])
            new_email = Prompt.ask("Enter new email", default=client['email'])
            result = client_management.update_client_details(db_core, client_id, new_name, new_email)
            console.print(f"[green]{result['message']}[/green]")

        elif action == "Add Service Subnet":
            _add_service_subnet_tui(db_core, client_id)

        elif action == "Manage BGP Session":
            _manage_bgp_session_tui(db_core, client)

        elif action == "Manage SMTP Access":
            result = client_management.toggle_client_smtp_access(db_core, client_id)
            console.print(f"[green]{result['message']}[/green]")
            Prompt.ask("\nPress Enter to continue...")

        elif action == "View Email Log":
            _view_email_log_tui(db_core, client)

        elif action == "Resend Welcome Kit":
            email_notifications.resend_welcome_email(db_core, client_id)

        elif action == "Back to main menu":
            break

def _add_service_subnet_tui(db_core: BIC_DB, client_id: int):
    console = Console()
    pool_choices, pool_map = get_pool_choices(db_core)
    if not pool_choices:
        console.print("[yellow]No IP pools are defined.[/yellow]")
        return

    chosen_pool_str = Prompt.ask("Choose a pool for the subnet", choices=pool_choices)
    pool_id = pool_map[chosen_pool_str]['id']
    
    prefix_len = Prompt.ask("Enter desired prefix length (e.g., 29 for IPv4, 56 for IPv6)", default="29")
    
    with console.status("[bold cyan]Allocating subnet and updating WireGuard..."):
        result = client_management.add_subnet_to_client(db_core, client_id, pool_id, int(prefix_len))

    if result["success"]:
        console.print(f"[green]✅ {result['message']}[/green]")
    else:
        console.print(f"[red]Error: {result['message']}[/red]")
    Prompt.ask("\nPress Enter to continue...")

def _manage_bgp_session_tui(db_core, client):
    console = Console()
    bgp_action = Prompt.ask("BGP Session Management", choices=["Enable/Recreate Session", "Disable Session"], default="Disable Session")
    if bgp_action == "Enable/Recreate Session":
        if Confirm.ask(f"This will create/overwrite the BGP config for {client['name']}. Proceed?", default=True):
            console.print("[cyan]Creating BGP session configuration...[/cyan]")
            bgp_management.create_client_bgp_config(db_core, client)
    elif bgp_action == "Disable Session":
        if Confirm.ask(f"This will remove the BGP config for {client['name']}. Proceed?", default=True):
            console.print("[cyan]Removing BGP session configuration...[/cyan]")
            bgp_management.delete_client_bgp_config(client)

def _view_email_log_tui(db_core, client):
    console = Console()
    email_log = db_core.find_all_by('email_log', {'client_id': client['id']})
    if not email_log:
        console.print("[yellow]No emails have been logged for this client.[/yellow]")
    else:
        from rich.table import Table
        table = Table(title=f"Email Log for {client['name']}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Subject")
        table.add_column("Attachment")
        for log in email_log:
            table.add_row(log['timestamp'], log['subject'], log['attachment_name'])
        console.print(table)
    Prompt.ask("\nPress Enter to continue...")
