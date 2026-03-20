from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, TableColumn
from bic.modules import system_management, statistics_management

# --- Define Views ---

view_statistics = UIView(
    name="System Statistics",
    template="system_statistics.html",
    handler=statistics_management.gather_all_statistics,
    context_name="stats",
    table_columns=[
        # Columns are defined but not used in this custom template
    ]
)

view_live_log = UIView(
    name="Live System Log",
    template="live_view.html",
    # This view is just a template with a WebSocket connection, no handler needed
)

# --- Define Actions ---

edit_settings = UIAction(
    name="Edit System Settings",
    handler=system_management.save_all_settings,
    redirect_to="/page/system/settings",
    loader=system_management.get_all_settings,
    form_fields=[
        FormField(name="smtp_host", label="SMTP Host"),
        FormField(name="smtp_port", label="SMTP Port", type="number", default=587),
        FormField(name="smtp_user", label="SMTP User"),
        FormField(name="smtp_pass", label="SMTP Password", type="password"),
        FormField(name="smtp_from_email", label="Sender Address", type="email"),
        FormField(name="dns_servers", label="DNS Servers (comma-separated)"),
        FormField(name="nat_private_ranges", label="NAT Private Ranges (comma-separated)"),
        FormField(name="branding_company_name", label="Company Name", default="BGP in Cloud"),
        FormField(name="email_signature", label="Email Signature", default="Your Network Team"),
        FormField(name="wireguard_endpoint", label="WireGuard Endpoint", placeholder="e.g., my.vpn.server.com", required=True),
        FormField(name="branding_logo", label="Company Logo", type="file"),
        FormField(name="branding_color_primary", label="Primary Color", type="color", default="#3b82f6"),
        FormField(name="branding_color_secondary", label="Secondary Color", type="color", default="#10b981"),
    ]
)

# --- Define the Menu ---

from .users import users_menu

view_audit_log = UIView(
    name="Audit Log",
    template="audit_log.html",
    handler=system_management.get_audit_logs,
    table_columns=[
        TableColumn(name="timestamp", label="Timestamp"),
        TableColumn(name="username", label="User"),
        TableColumn(name="action", label="Action"),
        TableColumn(name="details", label="Details"),
    ]
)

# --- Backup Actions and Views ---

view_backups = UIView(
    name="Database Backups",
    template="backups.html",
    handler=system_management.list_backups,
    table_columns=[
        TableColumn(name="filename", label="Filename"),
        TableColumn(name="created_at", label="Created At"),
        TableColumn(name="size", label="Size"),
    ]
)

create_backup_action = UIAction(
    name="Create Backup",
    handler=system_management.create_backup,
    redirect_to="/page/system/backups",
    form_fields=[]
)

restore_backup_action = UIAction(
    name="Restore Backup",
    handler=system_management.restore_backup,
    redirect_to="/page/system/backups",
    form_fields=[
        FormField(name="filename", label="Filename", type="hidden"),
    ]
)

delete_backup_action = UIAction(
    name="Delete Backup",
    handler=system_management.delete_backup,
    redirect_to="/page/system/backups",
    form_fields=[
        FormField(name="filename", label="Filename", type="hidden"),
    ]
)

system_menu = UIMenu(
    name="System",
    items=[
        UIMenuItem(name="General Settings", path="settings", item=edit_settings),
        UIMenuItem(name="User Management", path="users", item=users_menu),
        UIMenuItem(name="Audit Log", path="audit", item=view_audit_log),
        UIMenuItem(name="Backups", path="backups", item=view_backups),
        UIMenuItem(name="View Logs", path="logs", item=UIView(name="Live System View", template="live_view.html")),
        UIMenuItem(name="Check for Updates", path="updates", item=UIView(name="Check for Updates", template="updates.html")),
        UIMenuItem(name="Create Backup", path="backups/create", item=create_backup_action, hidden=True),
        UIMenuItem(name="Restore Backup", path="backups/restore/{filename}", item=restore_backup_action, hidden=True),
        UIMenuItem(name="Delete Backup", path="backups/delete/{filename}", item=delete_backup_action, hidden=True),
    ]
)

