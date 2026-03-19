from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Input
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.modules import network_management

# --- Screens ---

class PoolSelectScreen(Screen):
    """Screen to select a pool to edit."""

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


class EditDescriptionScreen(Screen):
    """Screen to edit the description of a selected pool."""

    def __init__(self, db_core: BIC_DB, pool_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.pool_id = pool_id
        self.pool = self.db_core.find('ip_pools', self.pool_id)

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
                self.app.exit(result) # Exit the app with a success message
            else:
                self.query_one("#status-message").update(f"[red]Error: {result['message']}[/red]")
        elif event.button.id == "cancel-button":
            self.app.exit() # Exit the app with no message


# --- App ---

class EditPoolApp(App):
    """A textual app to edit an IP Pool's description."""
    CSS = """
    .title {
        content-align: center middle;
        width: 100%;
        padding: 1;
        background: $primary;
    }
    #pool-list {
        padding: 1;
    }
    #pool-list > Button {
        width: 100%;
        margin-bottom: 1;
    }
    #description-input {
        margin: 1 0;
    }
    """

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def on_mount(self) -> None:
        self.push_screen(PoolSelectScreen(self.db_core))


def run(db_core: BIC_DB):
    """Main entry point to run the Edit Pool TUI app."""
    app = EditPoolApp(db_core)
    result = app.run()
    
    # After the app exits, print the result message in the parent console
    from rich.console import Console
    console = Console()
    if result and result.get("success"):
        console.print(f"\n[green]{result['message']}[/green]")
    else:
        # Provides feedback even on a cancel/exit without save
        console.print("\nReturning to main menu.")
