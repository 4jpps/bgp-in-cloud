import importlib
import os
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

console = Console()

def run(db_core: BIC_DB):
    """The main entry point for the TUI, with a robust dashboard layout."""
    system_management.setup_host_networking(db_core)
    
    menu_stack = [MENU_STRUCTURE]
    path_titles = ["Main Menu"]

    while True:
        console.clear()
        current_menu_level = menu_stack[-1]
        choices = list(current_menu_level.keys())
        if len(menu_stack) > 1:
            choices.append("Back")
        choices.append("Quit")

        # Create the layout and update its components
        layout = make_layout(
            db_core=db_core,
            path_titles=path_titles,
            menu_choices=choices
        )
        console.print(layout)

        # Get user input. The prompt will now appear cleanly after the layout.
        chosen_item_raw = Prompt.ask("Choose an option", choices=choices, default="Back")

        # Case-insensitive matching
        chosen_item = ""
        for key in choices:
            if key.lower() == chosen_item_raw.lower():
                chosen_item = key
                break

        if not chosen_item:
            # Handle invalid input gracefully
            console.print("[red]Invalid option.[/red]")
            Prompt.ask("Press Enter to continue...")
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

def make_layout(db_core: BIC_DB, path_titles: list, menu_choices: list) -> Layout:
    """Defines the TUI layout with a dedicated prompt area."""
    layout = Layout(name="root")
    layout.split_row(
        Layout(name="main_content"),
        Layout(generate_stats_panel(db_core), name="side_stats", size=40, minimum_size=30),
    )
    layout["main_content"].split(
        Layout(Header(f"BGP in the Cloud - v{__version__}"), size=3),
        Layout(generate_menu_panel(path_titles, menu_choices), name="menu_area"),
        Layout(Panel("[bold cyan]Choose an option from the list above.[/bold cyan]", height=3), name="footer")
    )
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
        return Panel(grid, style="white on blue", height=3)

def generate_menu_panel(path_titles: list, menu_choices: list) -> Panel:
    """Creates the menu panel for the main working area."""
    menu_text = "\n".join(f"- {item}" for item in menu_choices if item not in ["Back", "Quit"])
    return Panel(
        Align.center(menu_text, vertical="middle"),
        title=" -> ".join(path_titles),
        border_style="green"
    )

def generate_stats_panel(db_core: BIC_DB) -> Panel:
    """Generates a panel with a table of system statistics."""
    stats = statistics_management.gather_all_statistics(db_core)
    table = Table(title="System Statistics", border_style="cyan", show_header=False)
    table.add_column("Metric", justify="right", style="bold green")
    table.add_column("Value", style="white")

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
