import importlib
import os
import time
from datetime import datetime

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from bic.core import BIC_DB
from bic.menus.menu_structure import MENU_STRUCTURE
from bic.modules import system_management, statistics_management
from bic.__version__ import __version__


def run(db_core: BIC_DB):
    """The main entry point for the TUI, featuring a dashboard layout."""
    
    console = Console()
    system_management.setup_host_networking(db_core)
    
    menu_stack = [MENU_STRUCTURE]
    path_titles = ["Main Menu"]

    while menu_stack:
        console.clear()
        layout = make_layout()

        # Update layout with current information
        layout["header"].update(Header(f"BGP in the Cloud - v{__version__}"))
        layout["side_menu"].update(generate_menu_panel(path_titles, menu_stack[-1]))
        layout["main_content"].update(generate_stats_table(db_core))

        console.print(layout)

        # Build choices for the interactive prompt
        current_menu_level = menu_stack[-1]
        choices = list(current_menu_level.keys())
        if len(menu_stack) > 1:
            choices.append("Back")
        choices.append("Quit")

        # Get user input
        chosen_item = Prompt.ask("\nChoose an option", choices=choices, default="Back")

        if chosen_item == "Quit":
            break
        elif chosen_item == "Back":
            if len(menu_stack) > 1:
                menu_stack.pop()
                path_titles.pop()
            continue

        selected_item = current_menu_level[chosen_item]
        
        if selected_item['type'] == 'submenu':
            menu_stack.append(selected_item['handler'])
            path_titles.append(chosen_item)
        elif selected_item['type'] == 'action':
            run_action(db_core, selected_item['handler'], console)


def make_layout() -> Layout:
    """Defines the TUI layout."""
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
    )
    layout["main"].split_row(Layout(name="side_menu"), Layout(name="main_content", ratio=2))
    return layout


class Header:
    """Display header with clock."""
    def __init__(self, title: str):
        self.title = title

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            f"[b]{self.title}[/b]",
            datetime.now().ctime(),  # Correctly display time without formatting errors
        )
        return Panel(grid, style="white on blue")


def generate_menu_panel(path_titles: list, menu_level: dict) -> Panel:
    """Creates the menu panel for the sidebar."""
    menu_items = list(menu_level.keys())
    # Use a simple list for menu items
    menu_text = "\n".join(f"- {item}" for item in menu_items)

    return Panel(
        Align.left(menu_text, vertical="top"),
        title=" -> ".join(path_titles),
        border_style="green",
        padding=(1, 2)
    )


def generate_stats_table(db_core: BIC_DB) -> Table:
    """Generates a table of system statistics."""
    stats = statistics_management.gather_all_statistics(db_core)
    
    table = Table(title="System Statistics (Refreshed on action)", border_style="cyan")
    table.add_column("Metric", justify="right", style="bold")
    table.add_column("Value")

    system_stats = stats.get('system', {})
    network_stats = stats.get('network', {})
    db_stats = stats.get('database', {})

    # System Stats
    table.add_row("CPU Load", f"{system_stats.get('cpu_load', 'N/A')}% / {system_stats.get('cpu_cores', 'N/A')} cores")
    table.add_row("Memory", f"{system_stats.get('mem_percent', 'N/A')}% used")
    table.add_row("Disk Usage", f"{system_stats.get('disk_percent', 'N/A')}% used")
    table.add_row("WAN Traffic", f"Sent: {network_stats.get('bytes_sent', 'N/A')} | Recv: {network_stats.get('bytes_recv', 'N/A')}")

    # Database Stats
    table.add_section()
    table.add_row("DB Clients", str(db_stats.get('clients', 'N/A')))
    table.add_row("DB IP Pools", str(db_stats.get('ip_pools', 'N/A')))
    table.add_row("DB Allocations", str(db_stats.get('ip_allocations', 'N/A')))
    table.add_row("DB Subnets", str(db_stats.get('ip_subnets', 'N/A')))

    return table


def run_action(db_core: BIC_DB, handler_path: str, console: Console):
    """Runs a selected action module."""
    try:
        action_module = importlib.import_module(handler_path)
        console.clear()
        action_module.run(db_core)
        Prompt.ask("\nPress Enter to return to the menu...")
    except ImportError as e:
        console.print(f"[bold red]Error loading module:[/bold red] {e}")
        Prompt.ask("\nPress Enter to continue...")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        console.print_exception(show_locals=True)
        Prompt.ask("\nPress Enter to continue...")


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    run(db)
