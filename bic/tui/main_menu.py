import datetime
import os

from textual.app import App, ComposeResult
from textual.screen import Screen
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

    def __init__(self, db_core: BIC_DB, menu_data: UIMenu = menu_structure, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.menu_data = menu_data

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
            # Only show stats pane on the root menu
            if self.menu_data.name == "Main Menu":
                with Vertical(id="stats-pane"):
                    yield Static("📊 Statistics", classes="title")
                    yield Static(id="stats-display")
        yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="copyright")

    def on_mount(self) -> None:
        # Only manage stats on the main menu
        if self.menu_data.name == "Main Menu":
            self.update_stats()
            self.set_interval(30, self.update_stats)

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)
        display = f"""Pools: {stats['total_pools']}
Clients: {stats['total_clients']}
Allocated IPs: {stats['total_allocations']}
Allocated Subnets: {stats['total_subnets']}"""
        self.query_one("#stats-display", Static).update(display)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        for item in self.menu_data.items:
            sanitized_path = item.path.replace('/', '-').lstrip('-')
            if sanitized_path == button_id:
                if isinstance(item.item, UIMenu):
                    self.app.push_screen(MainMenuScreen(self.db_core, item.item))
                elif isinstance(item.item, UIView):
                    self.app.push_screen(GenericListScreen(self.db_core, item.item))
                elif isinstance(item.item, UIAction):
                    if item.path == "/clients/provision/new":
                        self.app.push_screen(ProvisionClientScreen(self.db_core))
                    else:
                        self.app.push_screen(GenericFormScreen(self.db_core, item.item))
                break
        stats_text = (
            f"[bold]Clients:[/bold] {stats['total_clients']}\n"
            f"[bold]IP Pools:[/bold] {stats['total_pools']}\n"
            f"[bold]Allocated IPs:[/bold] {stats['total_allocations']}\n"
            f"[bold]Allocated Subnets:[/bold] {stats['total_subnets']}\n\n"
            f"[bold]Pool Usage:[/bold]\n"
        )
        for pool_stat in stats['pool_stats']:
            stats_text += f"  - {pool_stat['name']}: {pool_stat['usage']:.2f}%\n"
        
        self.query_one("#stats-display").update(stats_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        selected_menu_item = None
        for item in self.menu_data.items:
            if item.path == event.button.id:
                selected_menu_item = item
                break
        
        if selected_menu_item:
            item_action = selected_menu_item.item
            if isinstance(item_action, UIMenu):
                self.app.push_screen(MainMenuScreen(self.db_core, menu_data=item_action))
            elif selected_menu_item.path == "/clients/provision/new":
                self.app.push_screen(ProvisionClientScreen(self.db_core))
            elif isinstance(item_action, UIAction):
                self.app.push_screen(GenericFormScreen(self.db_core, item_action))
            elif isinstance(item_action, UIView):
                self.app.push_screen(GenericListScreen(self.db_core, item_action))

class BIC_TUI(App):
    """The main Textual application."""

    CSS_PATH = "main_menu.css"

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def on_mount(self) -> None:
        brand_name = self.db_core.get_setting('branding_company_name', 'BGP in the Cloud')
        self.title = f"{brand_name} - BGP in the Cloud"
        self.push_screen(MainMenuScreen(self.db_core))

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    app = BIC_TUI(db_core=db)
    app.run()
