from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.layout import Layout

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
    BINDINGS = [Binding("any", "app.pop_screen", "Back to Main Menu")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.layout = self._make_layout()

    def _make_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
        layout["side"].split(Layout(name="ipam_stats"), Layout(name="system_stats"))
        return layout

    def compose(self) -> None:
        yield Header(show_clock=True)
        yield Static(self.layout)
        yield Footer()

    def on_mount(self) -> None:
        self.update_stats()
        self.set_interval(2, self.update_stats)

    def update_stats(self) -> None:
        stats = statistics_management.gather_all_statistics(self.db_core)

        header_text = Align.center("[bold]BIC IPAM - System Dashboard[/bold]", vertical="middle")
        self.layout["header"].update(Panel(header_text, border_style="green"))

        self.layout["ipam_stats"].update(StatsPanel("IPAM Stats", stats["database"]))
        self.layout["system_stats"].update(StatsPanel("System Stats", stats["system"]))

        body_content = Layout()
        body_content.split(
            StatsPanel(f"WAN Interface ({stats.get('wan_interface', 'N/A')})", stats["network"]['wan']),
            Panel("Future Traffic Graph", title="Traffic", border_style="blue")
        )
        self.layout["body"].update(body_content)

        footer_text = Align.center("Live updating... Press any key to return to the main menu.", vertical="middle")
        self.layout["footer"].update(Panel(footer_text))

        # We need to refresh the Static widget that holds the layout
        self.query_one(Static).refresh()
