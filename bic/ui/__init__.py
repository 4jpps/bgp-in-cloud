from bic.ui.schema import UIMenu, UIMenuItem
from bic.ui.clients import client_menu
from bic.ui.network import network_menu
from bic.ui.bgp import bgp_menu
from bic.ui.wireguard import wireguard_menu
from bic.ui.system import system_menu

# This is where we will aggregate all the UI definitions
# from different modules.
main_menu = UIMenu(
    name="Main Menu",
    items=[
        UIMenuItem(name="Client Management", path="/clients", item=client_menu),
        UIMenuItem(name="Network Management", path="/network", item=network_menu),
        UIMenuItem(name="BGP Management", path="/bgp", item=bgp_menu),
        UIMenuItem(name="WireGuard Management", path="/wireguard", item=wireguard_menu),
        UIMenuItem(name="System", path="/system", item=system_menu),
    ]
)