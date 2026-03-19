from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Vertical

from bic.core import BIC_DB

class AddClientScreen(Screen):
    """Screen to add a new client."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Add New Client", classes="title")
        with Vertical(id="form-container"):
            yield Input(placeholder="Client Name", id="name")
            yield Input(placeholder="Client Email", id="email")
            yield Input(placeholder="ASN (optional)", id="asn")
            yield Button("Save Client", id="save_client", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_client":
            name = self.query_one("#name", Input).value
            email = self.query_one("#email", Input).value
            asn_str = self.query_one("#asn", Input).value
            asn = int(asn_str) if asn_str else None

            if name:
                self.db_core.insert("clients", {
                    "name": name,
                    "email": email,
                    "asn": asn,
                    "allow_smtp": False # Default value
                })
                self.app.pop_screen() # Go back to the client list
            else:
                # Basic validation feedback
                self.query_one(".title").update("Add New Client [bold red](Name is required)[/]")
