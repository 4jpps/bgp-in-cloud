
import smtplib
import os
from email.message import EmailMessage
from rich.console import Console
from bic.core import BIC_DB

console = Console()

def send_welcome_email(db_core: BIC_DB, client_id: int, client_conf_path: str):
    """
    Constructs and sends a welcome email to a new client with their
    WireGuard configuration and logs the email to the database.
    """
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        console.print(f"[red]Cannot send email: No client found with ID {client_id}[/red]")
        return

    settings_rows = db_core.find_all('settings')
    settings = {s['key']: s['value'] for s in settings_rows}
    
    smtp_server = settings.get('smtp_server')
    smtp_port = settings.get('smtp_port')
    smtp_user = settings.get('smtp_user')
    smtp_password = settings.get('smtp_password')
    smtp_sender = settings.get('smtp_sender')

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, smtp_sender]):
        console.print("[bold red]Email cannot be sent. SMTP settings are incomplete.[/bold red]")
        console.print("Please configure them in the 'Email Settings' menu.")
        return

    try:
        with open(client_conf_path, 'r') as f:
            wg_config_content = f.read()
    except Exception as e:
        console.print(f"[red]Failed to read WireGuard config file {client_conf_path}: {e}[/red]")
        return

    client_name = client.get('name', 'New Client')
    client_email = client.get('email')

    subject = f"Your BGP in the Cloud service is ready, {client_name}!"
    body = f"""
Hi {client_name},

Welcome to BGP in the Cloud!

Your WireGuard peer has been configured and is attached to this email.

To get started, please import the attached .conf file into your WireGuard client.

Thank you,
The BGP in the Cloud Team
"""

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = smtp_sender
    msg['To'] = client_email
    msg.add_attachment(wg_config_content, filename=f"{client_name.replace(' ', '_')}_wg.conf")

    log_data = {
        "client_id": client_id,
        "subject": subject,
        "body": body,
        "attachment_name": f"{client_name.replace(' ', '_')}_wg.conf",
        "attachment_content": wg_config_content
    }

    try:
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        console.print(f"[blue]✉️  Welcome email successfully sent to {client_email}[/blue]")
        db_core.insert('email_log', log_data)
        
    except Exception as e:
        console.print(f"[bold red]Failed to send email: {e}[/bold red]")

def resend_welcome_email(db_core: BIC_DB, client_id: int):
    """Finds a client's config file and re-sends their welcome email."""
    client = db_core.find_one("clients", {"id": client_id})
    if not client:
        console.print(f"[red]Cannot resend email: No client found with ID {client_id}[/red]")
        return

    # Construct the expected path to the client's config file
    conf_dir = os.path.join(os.path.expanduser("~"), ".bic", "client_confs")
    client_conf_path = os.path.join(conf_dir, f"{client['name']}.conf")

    if not os.path.exists(client_conf_path):
        console.print(f"[red]Could not find config file at {client_conf_path}. Cannot resend.[/red]")
        return

    # Call the main send function
    send_welcome_email(db_core, client_id, client_conf_path)

