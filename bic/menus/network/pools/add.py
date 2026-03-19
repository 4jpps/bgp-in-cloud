from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Vertical

from bic.core import BIC_DB

class AddPoolScreen(Screen):
    """Screen to add a new IP pool."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Add New IP Pool", classes="title")
        with Vertical(id="form-container"):
            yield Input(placeholder="Pool Name", id="name")
            yield Input(placeholder="CIDR (e.g., 192.168.1.0/24)", id="cidr")
            yield Input(placeholder="Address Family (ipv4 or ipv6)", id="afi")
            yield Input(placeholder="Description (optional)", id="description")
            yield Button("Save Pool", id="save_pool", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_pool":
            name = self.query_one("#name", Input).value
            cidr = self.query_one("#cidr", Input).value
            afi = self.query_one("#afi", Input).value
            description = self.query_one("#description", Input).value

            if name and cidr and afi:
                self.db_core.insert("ip_pools", {
                    "name": name,
                    "cidr": cidr,
                    "afi": afi,
                    "description": description
                })
                self.app.pop_screen() # Go back to the pool list
            else:
                self.query_one(".title").update("Add New IP Pool [bold red](Name, CIDR, and AFI are required)[/]")
