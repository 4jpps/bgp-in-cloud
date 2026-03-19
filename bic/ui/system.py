from bic.ui.schema import UIMenu, UIMenuItem, UIAction, FormField
from bic.modules import system_management
from bic.modules import statistics_management

# Define Views
view_statistics = UIView(
    name="System Statistics",
    handler=lambda db: [statistics_management.gather_all_statistics(db)],  # Wrap in list for UIView
    columns=[
        {"key": "total_clients", "label": "Total Clients"},
        {"key": "total_pools", "label": "Total Pools"},
        {"key": "total_allocations", "label": "Total Allocations"},
        {"key": "total_subnets", "label": "Total Subnets"},
        {"key": "cpu_load", "label": "CPU Load"},
        {"key": "mem_percent", "label": "Memory %"},
        {"key": "disk_percent", "label": "Disk %"},
        {"key": "bytes_sent", "label": "Bytes Sent"},
        {"key": "bytes_recv", "label": "Bytes Received"},
    ]
)

# Define Actions
edit_settings = UIAction(
    name="Edit System Settings",
    handler=system_management.save_all_settings,
    loader=system_management.get_all_settings, # Add this line
    form_fields=[
        FormField(name="smtp_server", label="SMTP Server"),
        FormField(name="smtp_port", label="SMTP Port", type="number"),
        FormField(name="smtp_user", label="SMTP User"),
        FormField(name="smtp_password", label="SMTP Password", type="password"),
        FormField(name="smtp_sender", label="Sender Address", type="email"),
        FormField(name="dns_server_ipv4", label="DNS Server (IPv4)"),
        FormField(name="dns_server_ipv6", label="DNS Server (IPv6)"),
        FormField(name="wg_server_endpoint", label="WireGuard Server Endpoint"),
        FormField(name="branding_company_name", label="Company Name"),
        FormField(name="branding_email_from_name", label="Email From Name"),
    ]
)

# Define the menu
system_menu = UIMenu(
    name="System",
    items=[
        UIMenuItem(name="System Statistics", path="/system/statistics", item=view_statistics),
        UIMenuItem(name="Settings", path="/system/settings", item=edit_settings),
    ]
)
