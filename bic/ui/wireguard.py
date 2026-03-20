from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, TableColumn
from bic.modules import wireguard_management

# --- Define Actions and Views ---

view_wireguard_peers = UIView(
    name="List WireGuard Peers",
    template="generic_list.html",
    handler=wireguard_management.list_wireguard_peers,
    context_name="peers",
    table_columns=[
        TableColumn(name="client_name", label="Client"),
        TableColumn(name="client_public_key", label="Public Key"),
        TableColumn(name="allowed_ips", label="Allowed IPs"),
    ]
)

view_server_config = UIView(
    name="View WireGuard Server Config",
    template="generic_preformatted.html",
    handler=wireguard_management.get_server_wireguard_config,
    context_name="data",
)

force_reload_action = UIAction(
    name="Force WireGuard Reload",
    template="generic_form.html",
    handler=wireguard_management.force_reload_wireguard_server,
    redirect_to="/page/wireguard/list",
    form_fields=[],
)

# --- Define the Menu ---

wireguard_menu = UIMenu(
    name="WireGuard Management",
    items=[
        UIMenuItem(name="List Peers", path="list", item=view_wireguard_peers),
        UIMenuItem(name="View Server Config", path="server-config", item=view_server_config),
        UIMenuItem(name="Force Reload Server", path="force-reload", item=force_reload_action),
    ]
)
