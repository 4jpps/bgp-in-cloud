from rich.prompt import Prompt
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import settings_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]General Settings[/bold underline]")

    current_settings = settings_management.get_all_settings(db_core)

    app_display_name = Prompt.ask("Application Display Name", default=current_settings.get('app_display_name', 'BIC IPAM'))
    wg_server_endpoint = Prompt.ask("WireGuard Server Endpoint", default=current_settings.get('wg_server_endpoint'))
    bgp_local_asn = Prompt.ask("BGP Local ASN", default=str(current_settings.get('bgp_local_asn')))

    new_settings = {
        'app_display_name': app_display_name,
        'wg_server_endpoint': wg_server_endpoint,
        'bgp_local_asn': bgp_local_asn,
    }

    result = settings_management.update_settings(db_core, new_settings)

    if result["success"]:
        console.print(f"\n[green]{result['message']}[/green]")
    else:
        console.print(f"\n[red]Error: {result['message']}[/red]")
