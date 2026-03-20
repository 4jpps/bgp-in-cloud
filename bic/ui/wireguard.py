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

# Define the menu
wireguard_menu = UIMenu(
    name="WireGuard Management",
    items=[
        UIMenuItem(name="List Interfaces", path="/wireguard/interfaces/list", item=view_wg_interfaces),
    ]
)
