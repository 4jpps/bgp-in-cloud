from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import wireguard_management
from bic.core import BIC_DB

# Define Actions and Views
view_wg_interfaces = UIView(
    name="List WireGuard Interfaces",
    handler=lambda db: db.find_all("wireguard_interfaces"),
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "listen_port", "label": "Port"},
        {"key": "address", "label": "Address"},
    ]
)

view_wg_peers = UIView(
    name="List WireGuard Peers",
    handler=wireguard_management.list_peers_joined,
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Peer Name"},
        {"key": "client_name", "label": "Client"},
        {"key": "public_key", "label": "Public Key"},
        {"key": "allowed_ips", "label": "Allowed IPs"},
        {"key": "interface_name", "label": "Interface"},
    ]
)

# Define the menu
wireguard_menu = UIMenu(
    name="WireGuard Management",
    items=[
        UIMenuItem(name="List Interfaces", path="/wireguard/interfaces/list", item=view_wg_interfaces),
        UIMenuItem(name="List Peers", path="/wireguard/peers/list", item=view_wg_peers),
    ]
)
