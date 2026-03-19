from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Vertical

from bic.core import BIC_DB
from bic.modules import bgp_management

class BGSessionScreen(Screen):
    """Screen to manage a BGP session for a client."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, client_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.client_id = client_id
        self.client = self.db_core.find_one("clients", {"id": self.client_id})
        # In a real app, you'd fetch the BGP session status here
        self.session_status = "UNKNOWN"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(f"BGP Session for: {self.client['name']}", classes="title")
        with Vertical(id="bgp-status-container"):
            yield Static(f"Session Status: [bold]{self.session_status}[/bold]")
            yield Button("Enable Session", id="enable_session", variant="success")
            yield Button("Disable Session", id="disable_session", variant="error")
            yield Button("Reset Session", id="reset_session")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # In a real app, these buttons would trigger the corresponding bgp_management functions
        # For now, we'll just show a notification.
        self.app.notify(f"Action '{event.button.id}' triggered for client {self.client_id}")
