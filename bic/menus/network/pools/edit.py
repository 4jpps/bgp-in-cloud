from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Static, Input
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.modules import network_management

class PoolSelectScreen(Screen):
    """Screen to select a pool to edit."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Select an IP Pool to Edit", classes="title")
        with VerticalScroll(id="pool-list"):
            pools = self.db_core.find_all('ip_pools')
            if not pools:
                yield Static("There are no IP pools to edit.")
            else:
                for pool in pools:
                    label = f"{pool['name']} ({pool['afi']}) - {pool['cidr']}"
                    yield Button(label, id=f"pool_{pool['id']}")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("pool_"):
            pool_id = int(event.button.id.split("_")[1])
            self.app.push_screen(EditDescriptionScreen(self.db_core, pool_id))
        elif event.button.id == "back-button": # Allow going back
            self.app.pop_screen()

class EditDescriptionScreen(Screen):
    """Screen to edit the description of a selected pool."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, pool_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.pool_id = pool_id
        self.pool = self.db_core.find_one('ip_pools', {'id': self.pool_id})

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(f"Editing Pool: [b]{self.pool['name']} ({self.pool['afi']})[/b]", classes="title")
        yield Static(f"\nCurrent Description: [i]{self.pool['description']}[/i]")
        yield Input(self.pool['description'], id="description-input")
        yield Button("Save Changes", id="save-button", variant="primary")
        yield Button("Cancel", id="cancel-button", variant="error")
        yield Static("", id="status-message")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            new_description = self.query_one("#description-input").value
            result = network_management.update_pool_description(self.db_core, self.pool_id, new_description)
            if result["success"]:
                self.app.pop_screen() # Go back to the pool list
        elif event.button.id == "cancel-button":
            self.app.pop_screen()
