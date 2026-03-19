from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Vertical

from bic.core import BIC_DB

class EditClientScreen(Screen):
    """Screen to edit an existing client."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, client_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.client_id = client_id
        self.client = self.db_core.find_one("clients", {"id": self.client_id})

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(f"Edit Client: {self.client['name']}", classes="title")
        with Vertical(id="form-container"):
            yield Input(value=self.client['name'], id="name")
            yield Input(value=self.client['email'], id="email")
            yield Input(value=str(self.client['asn']), id="asn")
            yield Button("Save Changes", id="save_client", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_client":
            name = self.query_one("#name", Input).value
            email = self.query_one("#email", Input).value
            asn_str = self.query_one("#asn", Input).value
            asn = int(asn_str) if asn_str else None

            if name:
                self.db_core.update("clients", self.client_id, {
                    "name": name,
                    "email": email,
                    "asn": asn,
                })
                self.app.pop_screen() 
            else:
                self.query_one(".title").update("Edit Client [bold red](Name is required)[/]")
