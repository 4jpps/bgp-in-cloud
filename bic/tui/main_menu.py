import importlib
import os
from datetime import datetime

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from bic.core import BIC_DB
from bic.menus.menu_structure import MENU_STRUCTURE
from bic.modules import system_management, statistics_management
from bic.__version__ import __version__

# Global console object
console = Console()

class ClickablePanel(Panel):
    """A Panel that can be clicked."""
    def __init__(self, *args, on_click=None, item_name="", **kwargs):
        super().__init__(*args, **kwargs)
        self.on_click = on_click
        self.item_name = item_name

def run(db_core: BIC_DB):
    """The main entry point for the TUI, featuring a dashboard layout."""
    system_management.setup_host_networking(db_core)
    
    menu_stack = [MENU_STRUCTURE]
    path_titles = ["Main Menu"]

    while True:
        console.clear()
        layout = make_layout(db_core, path_titles, menu_stack[-1])
        console.print(layout)

        current_menu_level = menu_stack[-1]
        choices = list(current_menu_level.keys())
        if len(menu_stack) > 1:
            choices.append("Back")
        choices.append("Quit")

        # Get user input
        chosen_item_raw = Prompt.ask("\nChoose an option", choices=choices, default="Back")

        # Find the actual menu item with a case-insensitive search
        chosen_item = ""
        for key in choices:
            if key.lower() == chosen_item_raw.lower():
                chosen_item = key
                break

        if not chosen_item:
            # If no match was found (e.g., user typed something random)
            continue

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
            run_action(db_core, selected_item['handler'])

def make_layout(db_core: BIC_DB, path_titles: list, menu_level: dict) -> Layout:
    """Defines the TUI layout."""
    layout = Layout(name="root")
    layout.split_row(
        Layout(name="main_content"),
        Layout(name="side_stats", size=40, minimum_size=30),
    )
    layout["main_content"].split(
        Layout(Header(f"BGP in the Cloud - v{__version__}"), size=3),
        Layout(name="menu_area"),
    )

    layout["menu_area"].update(generate_menu_panel(path_titles, menu_level))
    layout["side_stats"].update(generate_stats_panel(db_core))
    return layout

class Header:
    """Display header with clock."""
    def __init__(self, title: str):
        self.title = title

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(f"[b]{self.title}[/b]", datetime.now().ctime())
        return Panel(grid, style="white on blue")

def generate_menu_panel(path_titles: list, menu_level: dict) -> Panel:
    """Creates the menu panel for the main working area."""
    menu_items = list(menu_level.keys())
    
    # Using Text objects to make them potentially clickable in a more advanced setup
    clickable_items = [Text(item, style="bold magenta") for item in menu_items]
    menu_text = Text("\n").join(clickable_items)

    return Panel(
        Align.center(menu_text, vertical="middle"),
        title=" -> ".join(path_titles),
        border_style="green",
        padding=(2, 4)
    )

def generate_stats_panel(db_core: BIC_DB) -> Panel:
    """Generates a panel with a table of system statistics."""
    stats = statistics_management.gather_all_statistics(db_core)
    
    table = Table(title="Live System Statistics", border_style="cyan", show_header=False)
    table.add_column("Metric", justify="right", style="bold green")
    table.add_column("Value", style="white")

    # Using .get() for robust data access
    system_stats = stats.get('system', {})
    network_stats = stats.get('network', {})
    db_stats = stats.get('database', {})

    table.add_row("CPU Load", f"{system_stats.get('cpu_load', 'N/A')}% / {system_stats.get('cpu_cores', 'N/A')} cores")
    table.add_row("Memory", f"{system_stats.get('mem_percent', 'N/A')}% used")
    table.add_row("Disk Usage", f"{system_stats.get('disk_percent', 'N/A')}% used")
    
    wan_stats = network_stats.get('wan', {})
    table.add_row("WAN Traffic", f"Sent: {wan_stats.get('bytes_sent', 'N/A')} | Recv: {wan_stats.get('bytes_recv', 'N/A')}")

    table.add_section()
    table.add_row("DB Clients", str(db_stats.get('clients', 'N/A')))
    table.add_row("DB IP Pools", str(db_stats.get('ip_pools', 'N/A')))
    table.add_row("DB Allocations", str(db_stats.get('ip_allocations', 'N/A')))
    table.add_row("DB Subnets", str(db_stats.get('ip_subnets', 'N/A')))
    
    return Panel(table, border_style="blue")

def run_action(db_core: BIC_DB, handler_path: str):
    """Runs a selected action module."""
    try:
        action_module = importlib.import_module(handler_path)
        console.clear()
        action_module.run(db_core)
        Prompt.ask("\nPress Enter to return to the menu...")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        console.print_exception(show_locals=True)
        Prompt.ask("\nPress Enter to continue...")

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db = BIC_DB(base_dir=BASE_DIR)
    run(db)
