import importlib
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from bic.core import BIC_DB
from bic.menus.menu_structure import MENU_STRUCTURE
from bic.modules import system_management, bird_management
from bic.__version__ import __version__

def run(db_core: BIC_DB):
    """The main entry point for the TUI, rewritten for the correct menu structure."""
    
    # Verify host networking and BIRD configuration on startup
    system_management.setup_host_networking(db_core)
    
    console = Console()
    # Navigation stack to keep track of the path through the menu
    menu_stack = [MENU_STRUCTURE]
    path_titles = ["Main Menu"]

    while menu_stack:
        current_menu_level = menu_stack[-1]
        console.clear()
        
        # Dynamically create a title based on navigation path
        title = " -> ".join(path_titles)

        console.print(Panel(f"[bold cyan]{title} - v{__version__}[/bold cyan]", expand=False, border_style="green"))

        # Build choices for the prompt
        choices = list(current_menu_level.keys())
        # Add navigation choices
        if len(menu_stack) > 1:
            choices.append("Back")
        choices.append("Quit")

        # Display the prompt and get user input
        chosen_item = Prompt.ask(
            "\nChoose an option",
            choices=choices,
        )

        # Process user's choice
        if chosen_item == "Quit":
            break
        elif chosen_item == "Back":
            menu_stack.pop()
            path_titles.pop()
            continue
        
        selected_item = current_menu_level[chosen_item]
        
        if selected_item['type'] == 'submenu':
            menu_stack.append(selected_item['handler'])
            path_titles.append(chosen_item)
        elif selected_item['type'] == 'action':
            try:
                module_path = selected_item['handler']
                action_module = importlib.import_module(module_path)
                console.clear()
                action_module.run(db_core)
                # After action, wait for user to continue
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
