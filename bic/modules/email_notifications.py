#!/usr/bin/env python
"""
This module handles all client and system email notifications.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from bic.core import BIC_DB, get_logger

# Initialize logger
log = get_logger(__name__)

def send_client_welcome_email(db_core: BIC_DB, client_id: str):
    """Sends a fully-configured welcome email to a new or updated client.

    This function retrieves the client's details and their generated network
    configuration files (WireGuard, BGP, etc.) from the database. It then
    constructs a multipart email, attaches the configuration files, and sends
    it to the client's email address using the SMTP settings configured in the
    application.

    If SMTP settings are not fully configured, the email will not be sent and
    an error will be logged.

    Args:
        db_core: An instance of the BIC_DB database core.
        client_id: The UUID of the client to send the email to.
    """
    log.info(f"Preparing to send welcome email for client_id: {client_id}")
    client = db_core.find_one('clients', {'id': client_id})
    if not client or not client.get('email'):
        log.warning(f"Cannot send welcome email: Client {client_id} not found or has no email address.")
        return

    # Fetch SMTP settings from the database
    smtp_host = db_core.get_setting('smtp_host')
    smtp_port_str = db_core.get_setting('smtp_port', '587')
    smtp_user = db_core.get_setting('smtp_user')
    smtp_pass = db_core.get_setting('smtp_pass')
    from_email = db_core.get_setting('smtp_from_email', smtp_user)
    email_signature = db_core.get_setting('email_signature', 'Your Network Team')

    if not all([smtp_host, smtp_port_str, smtp_user, smtp_pass, from_email]):
        log.error("SMTP settings are incomplete in the database. Cannot send welcome email.")
        return

    try:
        smtp_port = int(smtp_port_str)
    except (ValueError, TypeError):
        log.error(f"Invalid SMTP port configured: {smtp_port_str}. Must be an integer.")
        return

    subject = f"Welcome - Your VPN and BGP Configuration"
    body = f"""Hello {client['name']},

Welcome to the network!

Attached you will find your configuration files for WireGuard and BGP (if applicable).

{email_signature}
"""

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = client['email']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Fetch the correct WireGuard config from the peers table
    wireguard_peer = db_core.find_one("wireguard_peers", {"client_id": client_id})
    wireguard_conf = wireguard_peer.get('client_conf') if wireguard_peer else None

    # Attach configuration files
    configs = {
        "wireguard.conf": wireguard_conf,
        "frr.conf": client.get('bgp_frr_conf'),
        "bird.conf": client.get('bgp_bird_conf') # Note: Renamed from client_bird.conf for clarity
    }

    for filename, content in configs.items():
        if content:
            log.debug(f"Attaching {filename} to email for client {client_id}")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content.encode('utf-8'))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)

    try:
        # Using a with statement ensures the connection is automatically closed
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Upgrade the connection to encrypted
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            log.info(f"Successfully sent welcome email to {client['name']} ({client['email']})")
    except smtplib.SMTPAuthenticationError as e:
        log.critical(f"SMTP authentication failed. Please check SMTP username and password. Error: {e}")
    except smtplib.SMTPConnectError as e:
        log.critical(f"Failed to connect to SMTP host '{smtp_host}' on port {smtp_port}. Check host and port. Error: {e}")
    except smtplib.SMTPException as e:
        log.error(f"An SMTP error occurred while sending email to {client['email']}: {e}", exc_info=True)
    except Exception as e:
        log.error(f"An unexpected error occurred while sending email to {client['email']}: {e}", exc_info=True)
