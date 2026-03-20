#!/usr/bin/env python

"""
This module handles all client and system email notifications.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from bic.core import BIC_DB

log = logging.getLogger(__name__)

def send_client_welcome_email(db_core: BIC_DB, client_id: str):
    """Sends a fully-configured welcome email to a new client."""
    client = db_core.find_one('clients', {'id': client_id})
    if not client or not client.get('email'):
        log.warning(f"Cannot send welcome email: Client {client_id} has no email address.")
        return

    # Fetch SMTP settings from the database
    smtp_host = db_core.get_setting('smtp_host')
    smtp_port = int(db_core.get_setting('smtp_port', 587))
    smtp_user = db_core.get_setting('smtp_user')
    smtp_pass = db_core.get_setting('smtp_pass')
    from_email = db_core.get_setting('smtp_from_email', smtp_user)
    email_signature = db_core.get_setting('email_signature', 'Your Network Team')

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, from_email]):
        log.error("SMTP settings are incomplete. Cannot send welcome email.")
        return

    subject = f"Welcome to BGP in the Cloud - Your VPN and BGP Configuration"
    body = f"""Hello {client['name']},

Welcome!

Attached you will find your configuration files for WireGuard and BGP.

{email_signature}
"""

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = client['email']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach configuration files
    configs = {
        "wireguard.conf": client.get('wireguard_conf'),
        "frr.conf": client.get('bgp_frr_conf'),
        "client_bird.conf": client.get('bgp_bird_conf')
    }

    for filename, content in configs.items():
        if content:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content.encode('utf-8'))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
    
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            log.info(f"Successfully sent welcome email to {client['name']} ({client['email']})")
            db_core.insert('email_log', {'client_id': client_id, 'subject': subject})
    except Exception as e:
        log.error(f"Failed to send welcome email to {client['email']}: {e}")
