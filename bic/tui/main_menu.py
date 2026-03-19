import datetime
import os

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Header, Static

from bic.core import BIC_DB
from bic.modules import statistics_management
from bic.ui import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIAction, UIView
from bic.tui.generic_screens import GenericListScreen, GenericFormScreen
from bic.tui.provision_client_screen import ProvisionClientScreen
from bic.__version__ import __version__


class MainMenuScreen(Screen):
    """The main menu screen for the TUI."""

    BINDINGS = [
        Binding("b", "app.pop_screen", "Back", show=False), # Initially hidden
    ]

    def __init__(self, db_core: BIC_DB, menu_data: UIMenu = menu_structure, is_root=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.menu_data = menu_data
        self.is_root = is_root

    def compose(self) -> ComposeResult:
        year = datetime.date.today().year
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="main-menu-container"):
                yield Static(self.menu_data.name, id="menu-title")
                with Vertical(id="menu-container"):
                    for item in self.menu_data.items:
                        if not item.hidden:
                            yield Button(item.name, id=item.path.replace('/', '-').lstrip('-'))
            if self.is_root:
                with Vertical(id="stats-pane"):
                    yield Static("📊 Statistics", classes="title")
                    yield Static(id="stats-display")
        yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="copyright")

    def on_mount(self) -> None:
        # Show back button if not the root menu
        self.get_binding("b").show = not self.is_root
        
        if self.is_root:
            self.update_stats()
            self.set_interval(30, self.update_stats)
        
        try:
            self.query_one("Button").focus()
        except:
            pass

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)
        stats_text = (
            f"[bold]Clients:[/bold] {stats['total_clients']}\n"
            f"[bold]IP Pools:[/bold] {stats['total_pools']}\n"
            f"[bold]Allocated IPs:[/bold] {stats['total_allocations']}\n"
            f"[bold]Allocated Subnets:[/bold] {stats['total_subnets']}\n\n"
            f"[bold]Pool Usage:[/bold]\n"
        )
        for pool_stat in stats['pool_stats']:
            stats_text += f"  - {pool_stat['name']}: {pool_stat['usage']:.2f}%\n"
        
        self.query_one("#stats-display", Static).update(stats_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        # Find the menu item that corresponds to the sanitized button ID
        selected_menu_item = next((item for item in self.menu_data.items if item.path.replace('/', '-').lstrip('-') == button_id), None)
        
        if not selected_menu_item:
            return

        # Handle the special case for provisioning first
        if selected_menu_item.path == "/clients/provision/new":
            self.app.push_screen(ProvisionClientScreen(self.db_core))
            return

        item_action = selected_menu_item.item
        if isinstance(item_action, UIMenu):
            self.app.push_screen(MainMenuScreen(self.db_core, menu_data=item_action, is_root=False))
        elif isinstance(item_action, UIView):
            self.app.push_screen(GenericListScreen(self.db_core, item_action))
        elif isinstance(item_action, UIAction):
            self.app.push_screen(GenericFormScreen(self.db_core, item_action))

class BIC_TUI(App):
    """The main Textual application."""

    CSS_PATH = "main_menu.css"

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def on_mount(self) -> None:
        brand_name = self.db_core.get_setting('branding_company_name', 'BGP in the Cloud')
        self.title = f"{brand_name} - BGP in the Cloud"
        self.push_screen(MainMenuScreen(self.db_core, is_root=True))

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    app = BIC_TUI(db_core=db)
    app.run()
