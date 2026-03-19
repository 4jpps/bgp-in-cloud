from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.containers import Container, Vertical
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
    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> None:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="side-pane"):
                yield StatsPanel("IPAM Stats", {}, id="ipam-stats")
                yield StatsPanel("System Stats", {}, id="system-stats")
            with Vertical(id="body-pane"):
                yield StatsPanel("WAN Interface", {}, id="wan-stats")
                yield Static(Panel("Future Traffic Graph", title="Traffic", border_style="blue"))
        yield Footer()

    def on_mount(self) -> None:
        self.update_stats()
        self.set_interval(2, self.update_stats)

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)
        
        ipam_panel = self.query_one("#ipam-stats", StatsPanel)
        ipam_panel.stats_dict = stats["database"]
        ipam_panel.refresh()

        system_panel = self.query_one("#system-stats", StatsPanel)
        system_panel.stats_dict = stats["system"]
        system_panel.refresh()

        wan_panel = self.query_one("#wan-stats", StatsPanel)
        wan_panel.title = f"WAN Interface ({stats.get('wan_interface', 'N/A')})"
        wan_panel.stats_dict = stats["network"]['wan']
        wan_panel.refresh()
