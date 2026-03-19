from rich.prompt import Prompt, Confirm
from rich.console import Console
from bic.core import BIC_DB
from bic.menus.clients.helpers import display_client_dossier, get_pool_choices
from bic.modules import client_management, email_notifications

def run(db_core: BIC_DB):
    """TUI for interactively creating a new client."""
    console = Console()
    console.print("\n[bold underline]Add New Client[/bold underline]")

    # 1. Gather basic info
    client_name = Prompt.ask("Enter client name")
    client_email = Prompt.ask("Enter client email")

    console.print("\n[bold]Select Client Type:[/bold]")
    console.print("  [bold]Direct Assignment[/bold]: For clients who need one or more static IPs routed directly to their tunnel.")
    console.print("  [bold]BGP[/bold]: For clients running the Border Gateway Protocol to announce their own IP space.")
    client_type = Prompt.ask("\nSelect type", choices=["Direct Assignment", "BGP"])

    # 2. Gather all IP/Subnet assignment requests
    assignments = []
    if client_type == "Direct Assignment":
        console.print("\n[cyan]Define Static IP Assignments...[/cyan]")
        while True:
            pool_choices, pool_map = get_pool_choices(db_core)
            if not pool_choices:
                console.print("[yellow]No IP pools are defined. Cannot assign IPs.[/yellow]")
                break
            chosen_pool_str = Prompt.ask("Choose a pool for the static IP", choices=pool_choices)
            assignments.append({'type': 'static', 'pool_id': pool_map[chosen_pool_str]['id']})
            if not Confirm.ask("Assign another static IP?", default=False):
                break
    elif client_type == "BGP":
        console.print("\n[cyan]Define BGP Service Subnet Assignments...[/cyan]")
        while Confirm.ask("Assign a service subnet for this BGP client?", default=True):
            pool_choices, pool_map = get_pool_choices(db_core)
            if not pool_choices:
                console.print("[yellow]No IP pools are defined. Cannot assign subnets.[/yellow]")
                break
            chosen_pool_str = Prompt.ask("Choose a pool for the subnet", choices=pool_choices)
            prefix_len = Prompt.ask("Enter desired prefix length (e.g., 29 for IPv4, 56 for IPv6)", default="29")
            assignments.append({
                'type': 'subnet',
                'pool_id': pool_map[chosen_pool_str]['id'],
                'prefix_len': int(prefix_len)
            })

    # 3. Execute the provisioning
    with console.status("[bold cyan]Provisioning new client and all resources...") as status:
        result = client_management.provision_new_client(
            db_core=db_core,
            client_name=client_name,
            client_email=client_email,
            client_type=client_type,
            assignments=assignments
        )

    # 4. Display results
    if result["success"]:
        client_id = result["client_id"]
        client_data = db_core.find_one("clients", {"id": client_id})
        display_client_dossier(db_core, client_data, title_prefix="Client Created Successfully!")
        console.print(f"Client configuration saved to: [cyan]{result['conf_path']}[/cyan]")

        if Confirm.ask("\nSend welcome email to client?", default=True):
            email_notifications.send_welcome_email(
                db_core=db_core,
                client_id=client_id,
                client_conf_path=result['conf_path']
            )
    else:
        console.print(f"[bold red]Error creating client:[/bold red] {result['message']}")
