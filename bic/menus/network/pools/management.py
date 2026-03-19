from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Static
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.menus.network.pools.edit import EditDescriptionScreen # Re-use the existing edit screen
from bic.menus.network.pools.add import AddPoolScreen
from bic.menus.network.allocations.list import ListAllocationsScreen
from bic.menus.network.allocations.find import FindFreeIPScreen

class PoolManagementScreen(Screen):
    """Screen to manage IP pools."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def on_mount(self) -> None:
        self.recompose()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("IP Pool Management", classes="title")
        with VerticalScroll() as vs:
            pools = self.db_core.find_all("ip_pools")
            if not pools:
                vs.mount(Static("No IP pools found."))
            else:
                for pool in pools:
                    vs.mount(Static(f"[bold]{pool['name']}[/bold] ({pool['cidr']})"))
                    vs.mount(Button("Edit Description", id=f"edit_{pool['id']}"))
                    vs.mount(Button("Delete Pool", id=f"delete_{pool['id']}"))
                    vs.mount(Static("---"))
        yield Button("Add New Pool", id="add_pool", variant="success")
        yield Button("List All Allocations", id="list_allocations")
        yield Button("Find Free IP", id="find_free_ip")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_pool":
            self.app.push_screen(AddPoolScreen(self.db_core))
        elif event.button.id == "list_allocations":
            self.app.push_screen(ListAllocationsScreen(self.db_core))
        elif event.button.id == "find_free_ip":
            self.app.push_screen(FindFreeIPScreen(self.db_core))
        elif event.button.id and event.button.id.startswith("edit_"):
            pool_id = int(event.button.id.split("_")[1])
            self.app.push_screen(EditDescriptionScreen(self.db_core, pool_id))
        elif event.button.id and event.button.id.startswith("delete_"):
            pool_id = int(event.button.id.split("_")[1])
            self.db_core.delete("ip_pools", pool_id)
            self.recompose() # Refresh the list
