from bic.ui.schema import UIMenu, UIMenuItem, UIView
from .auth import auth_menu
from .bgp import bgp_menu
from .clients import client_menu
from .network import network_menu
from .system import system_menu
from .wireguard import wireguard_menu

from .bgp import bgp_menu

main_menu = UIMenu(
    name="Main Menu",
    items=[
        UIMenuItem(name="Dashboard", path="/", item=UIView(name="Dashboard", template="dashboard.html")),
        UIMenuItem(name="Authentication", path="auth", item=auth_menu),
        UIMenuItem(name="Client Management", path="clients", item=client_menu),
        UIMenuItem(name="Network Management", path="network", item=network_menu),
        UIMenuItem(name="BGP Management", path="bgp", item=bgp_menu),
        UIMenuItem(name="WireGuard Management", path="wireguard", item=wireguard_menu),
        UIMenuItem(name="System", path="system", item=system_menu),
    ]
)