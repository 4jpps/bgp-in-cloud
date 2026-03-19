from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.binding import Binding
from datetime import datetime
import os

from bic.core import BIC_DB
from bic.menus.menu_structure import MENU_STRUCTURE
from bic.menus.system.statistics import SystemDashboardScreen
from bic.modules import statistics_management, system_management
from bic.__version__ import __version__
from bic.menus.network.pools.edit import PoolSelectScreen

MENU_STACK = [MENU_STRUCTURE]
PATH_TITLES = ["Main Menu"]

class StatsTable(DataTable):
    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.zebra_stripes = True

    def on_mount(self) -> None:
        self.add_column("Metric", width=12)
        self.add_column("Value")
        self.update_stats()
        self.set_interval(5, self.update_stats)

    def update_stats(self) -> None:
        self.clear()
        stats = statistics_management.gather_all_statistics(self.db_core)
        system_stats = stats.get('system', {})
        network_stats = stats.get('network', {})
        db_stats = stats.get('database', {})
        self.add_row("[bold green]CPU Load[/]", f"{system_stats.get('cpu_load', 'N/A')}% / {system_stats.get('cpu_cores', 'N/A')}c")
        self.add_row("[bold green]Memory[/]", f"{system_stats.get('mem_percent', 'N/A')}% used")
        self.add_row("[bold green]Disk[/]", f"{system_stats.get('disk_percent', 'N/A')}% used")
        wan_stats = network_stats.get('wan', {})
        self.add_row("[bold green]WAN Out[/]", f"{wan_stats.get('bytes_sent', 'N/A')}")
        self.add_row("[bold green]WAN In[/]", f"{wan_stats.get('bytes_recv', 'N/A')}")
        self.add_row("", "")
        self.add_row("[bold blue]Clients[/]", str(db_stats.get('clients', 'N/A')))
        self.add_row("[bold blue]IP Pools[/]", str(db_stats.get('ip_pools', 'N/A')))
        self.add_row("[bold blue]Subnets[/]", str(db_stats.get('ip_subnets', 'N/A')))

class Menu(Static):
    def on_mount(self) -> None:
        self.update_menu()

    def update_menu(self) -> None:
        current_menu_level = MENU_STACK[-1]
        self.remove_children()
        buttons = []
        for item in current_menu_level.keys():
            sanitized_id = item.replace(" ", "_").lower()
            buttons.append(Button(item, id=sanitized_id, variant="success"))
        self.mount_all(buttons)

class TuiApp(App):
    TITLE = "BGP in the Cloud"
    CSS_PATH = "main_menu.css"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        year = datetime.now().year
        yield Header(show_clock=True)
        with Container(id="app-grid"):
            with Vertical(id="menu-pane"):
                yield Static("Main Menu", id="menu-title")
                yield Menu()
                yield Button("Back", id="back-button", variant="default", disabled=True)
            yield StatsTable(self.db_core, id="stats-pane")
        with Vertical(id="footer-container"):
            yield Static(f"Copyright {year} Jeff Parrish PC Services - v{__version__}", id="version-footer")
            yield Footer()

    def update_menu_view(self) -> None:
        menu_title = " -> ".join(PATH_TITLES)
        self.query_one("#menu-title").update(menu_title)
        self.query_one(Menu).update_menu()
        self.query_one("#back-button").disabled = len(MENU_STACK) <= 1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back-button":
            if len(MENU_STACK) > 1:
                MENU_STACK.pop()
                PATH_TITLES.pop()
                self.update_menu_view()
            return
        current_menu_level = MENU_STACK[-1]
        original_item_label = ""
        for key in current_menu_level.keys():
            if key.replace(" ", "_").lower() == button_id:
                original_item_label = key
                break
        if original_item_label in current_menu_level:
            selected_item = current_menu_level[original_item_label]
            if selected_item['type'] == 'submenu':
                MENU_STACK.append(selected_item['handler'])
                PATH_TITLES.append(original_item_label)
                self.update_menu_view()
            elif selected_item['handler'] == 'bic.menus.network.pools.edit':
                self.push_screen(PoolSelectScreen(self.db_core))
            elif selected_item['handler'] == 'bic.menus.system.statistics':
                self.push_screen(SystemDashboardScreen(self.db_core))

def run(db_core: BIC_DB):
    system_management.setup_host_networking(db_core)
    app = TuiApp(db_core)
    app.run()

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    run(db)
