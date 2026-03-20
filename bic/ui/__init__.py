from bic.ui.schema import UIMenu
from bic.ui.clients import client_menu
from bic.ui.network import network_menu
from bic.ui.system import system_menu

# The main menu structure for the entire application
main_menu = UIMenu(
    name="Main Menu",
    items=[
        client_menu,
        network_menu,
        system_menu,
    ]
)
