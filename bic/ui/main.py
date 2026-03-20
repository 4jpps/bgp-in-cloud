from bic.ui.schema import UIMenu, UIMenuItem, UIView
from .bgp import bgp_menu
from .clients import client_menu
from .network import network_menu
from .system import system_menu
from .wireguard import wireguard_menu
from .auth import login_view, two_fa_view, login_action

from .bgp import bgp_menu

main_menu = UIMenu(
    name="Main Menu",
    items=[
        UIMenuItem(name="Dashboard", path="/", item=UIView(name="Dashboard", template="dashboard.html")),
        UIMenuItem(name="Login", path="auth/login", item=login_view, hidden=True),
        UIMenuItem(name="Login Action", path="auth/login", item=login_action, hidden=True),
        UIMenuItem(name="2FA", path="auth/2fa", item=two_fa_view, hidden=True),
        UIMenuItem(name="Client Management", path="clients", item=client_menu),
        UIMenuItem(name="Network Management", path="network", item=network_menu),
        UIMenuItem(name="BGP Management", path="bgp", item=bgp_menu),
        UIMenuItem(name="WireGuard Management", path="wireguard", item=wireguard_menu),
        UIMenuItem(name="System", path="system", item=system_menu),
    ]
)