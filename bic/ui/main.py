from bic.ui.schema import UIMenu, UIMenuItem
from .clients import client_menu
from .network import network_menu
from .system import system_menu

main_menu = UIMenu(
    name="Main Menu",
    items=[
        UIMenuItem(name="Client Management", path="/clients", item=client_menu),
        UIMenuItem(name="Network Management", path="/network", item=network_menu),
        UIMenuItem(name="System", path="/system", item=system_menu),
        UIMenuItem(name="Live View", path="/system/live"),
    ]
)
