import datetime
import os

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Button, Header, Static

from bic.core import BIC_DB
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIAction, UIView
from bic.tui.generic_screens import GenericListScreen, GenericFormScreen
from bic.tui.provision_client_screen import ProvisionClientScreen
from bic.__version__ import __version__

# --- Helper function to sanitize paths for widget IDs ---
def sanitize_for_id(path: str) -> str:
    """Replaces invalid characters in a path to make it a valid CSS ID."""
    return path.replace('/', '_').replace('.', '_')

class MainMenuScreen(Screen):
    """The main menu screen for the TUI."""

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.menu_stack = [menu_structure]

    @property
    def current_menu(self):
        return self.menu_stack[-1]

    def compose(self) -> ComposeResult:
        year = datetime.date.today().year
        yield Header(show_clock=True)
        with Vertical(id="main-menu-container"):
            yield Static(self.current_menu.name, id="menu-title")
            with Vertical(id="menu-container"):
                for item in self.current_menu.items:
                    yield Button(item.name, id=sanitize_for_id(item.path))
            yield Button("Back", id="back-button", variant="default", disabled=True)
        with Vertical(id="footer-container"):
            yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="copyright")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.rebuild_menu()
            return

        selected_menu_item = None
        sanitized_id = event.button.id
        for item in self.current_menu.items:
            if sanitize_for_id(item.path) == sanitized_id:
                selected_menu_item = item
                break
        
        if selected_menu_item:
            if isinstance(selected_menu_item.item, UIMenu):
                self.menu_stack.append(selected_menu_item.item)
                self.rebuild_menu()
            # Special case for the complex provisioning workflow
            elif selected_menu_item.path == "/clients/provision/new":
                self.app.push_screen(ProvisionClientScreen(self.db_core))
            elif isinstance(selected_menu_item.item, UIAction):
                self.app.push_screen(GenericFormScreen(self.db_core, selected_menu_item.item))
            elif isinstance(selected_menu_item.item, UIView):
                self.app.push_screen(GenericListScreen(self.db_core, selected_menu_item.item))

    def rebuild_menu(self):
        menu_container = self.query_one("#menu-container")
        menu_container.remove_children()
        for item in self.current_menu.items:
            menu_container.mount(Button(item.name, id=sanitize_for_id(item.path)))
        self.query_one("#menu-title").update(self.current_menu.name)
        self.query_one("#back-button").disabled = len(self.menu_stack) <= 1

class BIC_TUI(App):
    """The main Textual application."""

    CSS_PATH = "style.css"

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen(self.db_core))

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    app = BIC_TUI(db_core=db)
    app.run()
