"""
This file defines the master structure for the application's menus.
It is a dictionary-based hierarchy that can be consumed by any UI (TUI, Web, etc.)
to dynamically generate navigation.

Structure:
- Keys are the display names of the menu items.
- The value is a dictionary containing:
    - 'type': 'submenu' or 'action'.
    - 'handler': If 'submenu', it's another dictionary of menu items.
                 If 'action', it's the path to the TUI module to run.
    - 'web_handler': The path to the backend module function for the web UI.
    - 'web_form': A description of the form for the web UI.
"""

MENU_STRUCTURE = {
    "Dashboard": {
        "type": "action",
        "handler": "bic.menus.system.statistics",
        "nav_path": "/"
    },
    "Client Management": {
        "type": "submenu",
        "nav_path": "/clients",
        "handler": {
            "List Clients": {
                "type": "action",
                "handler": "bic.menus.clients.list"
            },
            "Add New Client": {
                "type": "action",
                "handler": "bic.menus.clients.add",
                "web_handler": "bic.modules.client_management.provision_new_client",
                "web_form": [
                    {"label": "Client Name", "name": "client_name", "type": "text", "required": True},
                    {"label": "Client Email", "name": "client_email", "type": "email", "required": True},
                    {"label": "Client Type", "name": "client_type", "type": "select", "required": True, "options": ["Direct Assignment", "BGP"]},
                    {"label": "ASN (if BGP)", "name": "asn", "type": "number", "required": False}
                ]
            },
            "Manage BGP Session": {
                "type": "action",
                "handler": "bic.menus.clients.edit",
                "web_handler": "bic.modules.bgp_management.manage_client_bgp_session",
                "web_form": [
                    {"label": "Client ID", "name": "client_id", "type": "hidden"},
                    {"label": "Action", "name": "bgp_action", "type": "hidden"}
                ]
            },
            "Resend Welcome Kit": {
                "type": "action",
                "handler": "bic.menus.clients.edit",
                "web_handler": "bic.modules.email_notifications.resend_welcome_email",
                "web_form": [
                    {"label": "Client ID", "name": "client_id", "type": "hidden"}
                ]
            },
            "Delete Client": {
                "type": "action",
                "handler": "bic.menus.clients.delete",
                "web_handler": "bic.modules.client_management.deprovision_and_delete_client",
                "web_form": [
                    {"label": "Client to Delete", "name": "client_id", "type": "select_from_db", "required": True, "source": "clients", "display_key": "name"}
                ]
            },
        }
    },
    "Network Management": {
        "type": "submenu",
        "nav_path": "/network/pools",
        "handler": {
            "Manage IP Pools": {
                "type": "submenu",
                "handler": {
                    "List Pools": {
                        "type": "action",
                        "handler": "bic.menus.network.pools.list"
                    },
                    "Add New Pool": {
                        "type": "action",
                        "handler": "bic.menus.network.pools.add",
                        "web_handler": "bic.modules.network_management.add_pool",
                        "web_form": [
                            {"label": "Pool Name", "name": "name", "type": "text", "required": True},
                            {"label": "CIDR", "name": "cidr", "type": "text", "required": True},
                            {"label": "Description", "name": "description", "type": "text", "required": False}
                        ]
                    },
                    "Edit Pool Description": {
                        "type": "action",
                        "handler": "bic.menus.network.pools.edit"
                    },
                    "Delete Pool": {
                        "type": "action",
                        "handler": "bic.menus.network.pools.delete",
                        "web_handler": "bic.modules.network_management.delete_pool",
                        "web_form": [
                            {"label": "Pool to Delete", "name": "pool_id", "type": "select_from_db", "required": True, "source": "ip_pools", "display_key": "name"}
                        ]
                    },
                    "Swap Pool Prefix": {
                        "type": "action",
                        "handler": "bic.menus.network.pools.swap",
                        "web_handler": "bic.modules.network_management.swap_pool_prefix",
                        "web_form": [
                            {"label": "Pool to Modify", "name": "pool_id", "type": "select_from_db", "required": True, "source": "ip_pools", "display_key": "name"},
                            {"label": "New CIDR", "name": "new_cidr", "type": "text", "required": True}
                        ]
                    },
                }
            },
        }
    },
    "System Dashboard": {
        "type": "action",
        "handler": "bic.menus.system.statistics"
    },
    "System Settings": {
        "type": "submenu",
        "nav_path": "/action/system-settings/email-settings",
        "handler": {
            "Email Settings": {
                "type": "action",
                "handler": "bic.menus.system.email_settings",
                "web_handler": "bic.modules.settings_management.update_settings",
                "web_form": [
                    {"label": "SMTP Server", "name": "smtp_server", "type": "text"},
                    {"label": "SMTP Port", "name": "smtp_port", "type": "number"},
                    {"label": "SMTP User", "name": "smtp_user", "type": "text"},
                    {"label": "SMTP Password", "name": "smtp_password", "type": "password"},
                    {"label": "Sender Address", "name": "smtp_sender", "type": "email"}
                ]
            },
            "General Settings": {
                "type": "action",
                "handler": "bic.menus.system.general_settings",
                "web_handler": "bic.modules.settings_management.update_settings",
                "web_form": [
                    {"label": "Application Display Name", "name": "app_display_name", "type": "text"},
                    {"label": "WireGuard Server Endpoint", "name": "wg_server_endpoint", "type": "text"},
                    {"label": "BGP Local ASN", "name": "bgp_local_asn", "type": "number"}
                ]
            }
        }
    },
}

