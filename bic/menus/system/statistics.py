from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
import time

from bic.core import BIC_DB
from bic.modules import statistics_management

def make_layout() -> Layout:
    """Defines the layout of the dashboard."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=10, name="footer"),
    )

    layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
    layout["side"].split(Layout(name="ipam_stats"), Layout(name="system_stats"))
    return layout

def format_bytes(byte_count):
    """Helper to format bytes into KB, MB, GB, etc."""
    if not isinstance(byte_count, (int, float)):
        return str(byte_count)
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count > power and n < len(power_labels):
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}B"

class StatsPanel:
    """A panel showing a specific category of statistics."""

    def __init__(self, title: str, stats_dict: dict):
        self.title = title
        self.stats = stats_dict

    def __rich__(self) -> Panel:
        table = Table(show_header=False, expand=True, box=None)
        table.add_column(style="cyan")
        table.add_column(justify="right")
        for key, value in self.stats.items():
            # Special formatting for network stats
            if key in ["rx_bytes", "tx_bytes"]:
                value = format_bytes(value)
            table.add_row(key.replace("_", " ").title(), str(value))
        return Panel(table, title=self.title, border_style="blue")

def run(db_core: BIC_DB):
    """The main entry point for the statistics TUI."""
    console = Console()
    layout = make_layout()

    with Live(layout, screen=True, redirect_stderr=False) as live:
        live.console.print("[dim]Press Ctrl+C to exit dashboard...[/dim]")
        try:
            while True:
                stats = statistics_management.gather_all_statistics(db_core)

                header_text = Align.center("[bold]BIC IPAM - System Dashboard[/bold]", vertical="middle")
                layout["header"].update(Panel(header_text, border_style="green"))

                layout["ipam_stats"].update(StatsPanel("IPAM Stats", stats["database"]))
                layout["system_stats"].update(StatsPanel("System Stats", stats["system"]))

                body_content = Layout()
                body_content.split(
                    StatsPanel(f"WAN Interface ({stats.get('wan_interface', 'N/A')})", stats["network"]['wan']),
                    Panel("Future Traffic Graph", title="Traffic", border_style="blue")
                )
                layout["body"].update(body_content)
                
                footer_text = Align.center("Live updating every 2 seconds. Press Ctrl+C to exit.", vertical="middle")
                layout["footer"].update(Panel(footer_text))

                time.sleep(2)
        except KeyboardInterrupt:
            pass # Exit gracefully
