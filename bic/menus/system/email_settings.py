from rich.prompt import Prompt
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import settings_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Email Settings[/bold underline]")

    # Get current settings to use as defaults in prompts
    current_settings = settings_management.get_all_settings(db_core)

    console.print("\nEnter the new SMTP details. Press Enter to keep the current value.")

    smtp_server = Prompt.ask("SMTP Server", default=current_settings.get('smtp_server'))
    smtp_port = Prompt.ask("SMTP Port", default=str(current_settings.get('smtp_port', 587)))
    smtp_user = Prompt.ask("SMTP User", default=current_settings.get('smtp_user'))
    smtp_password = Prompt.ask("SMTP Password", default=current_settings.get('smtp_password'), password=True)
    smtp_sender = Prompt.ask("Sender Address", default=current_settings.get('smtp_sender'))

    new_settings = {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'smtp_sender': smtp_sender,
    }

    result = settings_management.update_settings(db_core, new_settings)

    if result["success"]:
        console.print(f"\n[green]{result['message']}[/green]")
    else:
        console.print(f"\n[red]Error: {result['message']}[/red]")
