from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Static
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.modules import network_management

class FindFreeIPScreen(Screen):
    """Screen to find the next free IP address in a pool."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Find Free IP: Select a Pool", classes="title")
        with VerticalScroll() as vs:
            pools = self.db_core.find_all("ip_pools")
            if not pools:
                vs.mount(Static("No IP pools found."))
            else:
                for pool in pools:
                    vs.mount(Button(f"{pool['name']} ({pool['cidr']})", id=f"pool_{pool['id']}"))
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("pool_"):
            pool_id = int(event.button.id.split("_")[1])
            free_ip = network_management.find_free_ip(self.db_core, pool_id)
            if free_ip:
                self.query_one(".title").update(f"Next Free IP: [bold green]{free_ip}[/]")
            else:
                self.query_one(".title").update("[bold red]No free IPs in this pool.[/]")
