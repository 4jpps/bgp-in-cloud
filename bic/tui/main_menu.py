import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Header, Static
from textual.css.query import NoMatches

from bic.core import BIC_DB
from bic.modules import statistics_management
from bic.ui.main import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIAction, UIView
from bic.tui.generic_screens import GenericListScreen, GenericFormScreen
from bic.tui.utils import find_ui_item_by_path
from bic.__version__ import __version__

class MainMenuScreen(Screen):
    """The main menu screen for the TUI."""

    BINDINGS = [
        Binding("b", "app.pop_screen", "Back", show=False),
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
                            yield Button(item.name, id=item.path)
            if self.is_root:
                with Vertical(id="stats-pane"):
                    yield Static("📊 Statistics", classes="title")
                    yield Static(id="stats-display")
        yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="copyright")

    def on_mount(self) -> None:
        self.get_binding("b").show = not self.is_root
        if self.is_root:
            self.update_stats()
            self.set_interval(30, self.update_stats)
        try:
            self.query_one("Button").focus()
        except NoMatches:
            pass # No buttons on this screen

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)
        stats_text = (
            f"[bold]Clients:[/bold] {stats.get('total_clients', 'N/A')}\n"
            f"[bold]IP Pools:[/bold] {stats.get('total_pools', 'N/A')}\n"
            f"[bold]Allocations:[/bold] {stats.get('total_allocations', 'N/A')}\n"
        )
        pool_details = stats.get('pool_details', [])
        if pool_details:
            stats_text += "\n[bold]Pool Usage:[/bold]\n"
            for pool_stat in pool_details:
                stats_text += f"  - {pool_stat['name']}: {pool_stat['usage']}\n"
        
        try:
            self.query_one("#stats-display", Static).update(stats_text)
        except NoMatches:
            pass # Stats pane might not exist

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_path = event.button.id
        item = find_ui_item_by_path(button_path)

        if not item:
            return

        if isinstance(item, UIMenu):
            # This is tricky because the UIMenu itself doesn't know its name or path.
            # We need to find the UIMenuItem that contains it.
            menu_item_container = next((i for i in self.menu_data.items if i.path == button_path), None)
            if menu_item_container:
                self.app.push_screen(MainMenuScreen(self.db_core, menu_data=item, is_root=False))
        elif isinstance(item, UIView):
            self.app.push_screen(GenericListScreen(self.db_core, item))
        elif isinstance(item, UIAction):
            self.app.push_screen(GenericFormScreen(self.db_core, item))
