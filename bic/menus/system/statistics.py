from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from rich.panel import Panel
from rich.table import Table

from bic.core import BIC_DB
from bic.modules import statistics_management

class StatsPanel(Static):
    """A panel showing a specific category of statistics."""
    def __init__(self, title: str, stats_dict: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.stats_dict = stats_dict

    def render(self) -> Panel:
        table = Table(show_header=False, expand=True, box=None)
        table.add_column(style="cyan")
        table.add_column(justify="right")
        for key, value in self.stats_dict.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        return Panel(table, title=self.title, border_style="blue")

class SystemDashboardScreen(Screen):
    CSS = """
    #main-container {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 2fr;
    }
    """
    BINDINGS = [Binding("any", "app.pop_screen", "Back to Main Menu")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> None:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="side-pane"):
                yield Static(id="ipam-stats")
                yield Static(id="system-stats")
            with Vertical(id="body-pane"):
                yield Static(id="wan-stats")
                yield Static(Panel("Future Traffic Graph", title="Traffic", border_style="blue"))
        yield Footer()

    def on_mount(self) -> None:
        self.update_stats()
        self.set_interval(2, self.update_stats)

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)
        self.query_one("#ipam-stats").update(StatsPanel("IPAM Stats", stats["database"]))
        self.query_one("#system-stats").update(StatsPanel("System Stats", stats["system"]))
        self.query_one("#wan-stats").update(StatsPanel(f"WAN Interface ({stats.get('wan_interface', 'N/A')})", stats["network"]['wan']))
