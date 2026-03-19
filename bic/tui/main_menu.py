from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from datetime import datetime
import os

from bic.core import BIC_DB
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction
from bic.tui.generic_screens import GenericListScreen, GenericFormScreen
from bic.tui.provision_client_screen import ProvisionClientScreen
from bic.__version__ import __version__

class TuiApp(App):
    TITLE = "BGP in the Cloud"
    CSS_PATH = "main_menu.css"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.menu_stack = [menu_structure]

    def on_mount(self) -> None:
        self.title = self.db_core.get_setting("branding_company_name", self.TITLE)

    @property
    def current_menu(self):
        return self.menu_stack[-1]

    def compose(self) -> ComposeResult:
        year = datetime.now().year
        yield Header(show_clock=True)
        with Vertical(id="app-grid"):
            yield Static(self.current_menu.name, id="menu-title")
            with Vertical(id="menu-container"):
                for item in self.current_menu.items:
                    yield Button(item.name, id=item.path)
            yield Button("Back", id="back-button", variant="default", disabled=True)
        with Vertical(id="footer-container"):
            yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="version-footer")
            yield Footer()

    def update_menu_view(self) -> None:
        menu_title = self.current_menu.name
        self.query_one("#menu-title").update(menu_title)
        
        menu_container = self.query_one("#menu-container")
        menu_container.remove_children()
        for item in self.current_menu.items:
            menu_container.mount(Button(item.name, id=item.path))

        self.query_one("#back-button").disabled = len(self.menu_stack) <= 1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "back-button":
            if len(self.menu_stack) > 1:
                self.menu_stack.pop()
                self.update_menu_view()
            return
        
        # Find the pressed menu item
        selected_menu_item = None
        for item in self.current_menu.items:
            if item.path == button_id:
                selected_menu_item = item
                break
        
        if not selected_menu_item:
            return

        if isinstance(selected_menu_item.item, UIMenu):
            self.menu_stack.append(selected_menu_item.item)
            self.update_menu_view()
        elif isinstance(selected_menu_item.item, UIView):
            self.push_screen(GenericListScreen(self.db_core, selected_menu_item.item))
        # Special case for the complex provisioning workflow
            if selected_menu_item.path == "/clients/provision/new":
                self.push_screen(ProvisionClientScreen(self.db_core))
            elif isinstance(selected_menu_item.item, UIAction):
                self.push_screen(GenericFormScreen(self.db_core, selected_menu_item.item))


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    app = TuiApp(db)
    app.run()
