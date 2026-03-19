import smtplib
from email.message import EmailMessage
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import bgp_management

console = Console()

def send_client_welcome_email(db_core: BIC_DB, client_id: int):
    """
    Constructs and sends a welcome email to a new client with all their
    necessary configuration files attached.
    """
    client = db_core.find_one("clients", {"id": client_id})
    if not client or not client.get('email'):
        console.print(f"[red]Cannot send email: No client or client email found for ID {client_id}[/red]")
        return

    settings = {s['key']: s['value'] for s in db_core.find_all('settings')}
    if not all(k in settings for k in ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_sender']):
        console.print("[bold red]Email cannot be sent. SMTP settings are incomplete.[/bold red]")
        return

    client_name = client['name']
    subject = f"Your BGP in the Cloud service configurations for {client_name}"
    from_name = settings.get('branding_email_from_name', 'The BGP in the Cloud Team')
    body = f"""Hi {client_name},

Welcome to BGP in the Cloud!

Your configuration files are attached to this email. Please find:

- wireguard.conf: For your WireGuard client.
- client_bird.conf: An example BIRD configuration for your BGP session.
- frr.conf: An example FRRouting configuration for your BGP session.

Thank you,
{from_name}
"""

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = settings['smtp_sender']
    msg['To'] = client['email']

    # Attachment 1: WireGuard Config
    wg_conf = client.get('wireguard_conf')
    if wg_conf:
        msg.add_attachment(wg_conf, filename="wireguard.conf")


    
    # Attachment 3: FRR Config (client side)
    frr_conf = bgp_management.create_client_frr_config(db_core, client)
    if frr_conf:
        msg.add_attachment(frr_conf, filename="frr.conf")

    # Attachment 4: Client-side BIRD Config
    client_bird_conf = bgp_management.create_client_bird_config(db_core, client)
    if client_bird_conf:
        msg.add_attachment(client_bird_conf, filename="client_bird.conf")

    try:
        with smtplib.SMTP(settings['smtp_server'], int(settings['smtp_port'])) as server:
            server.starttls()
            server.login(settings['smtp_user'], settings['smtp_password'])
            server.send_message(msg)
        
        console.print(f"[blue]✉️  Welcome email with all configs successfully sent to {client['email']}[/blue]")
        # Optionally log this to the database
        db_core.insert('email_log', {"client_id": client_id, "subject": subject, "body": "Welcome email with configs sent."})        

    except Exception as e:
        console.print(f"[bold red]Failed to send welcome email: {e}[/bold red]")
