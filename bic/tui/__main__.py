import os
from pathlib import Path
from textual.app import App

from bic.core import BIC_DB
from bic.tui.main_menu import MainMenuScreen, BIC_TUI

if __name__ == "__main__":
    # Correctly determine the project's base directory, which is two levels up from this file's directory.
    # bic/tui/__main__.py -> bic/ -> ipam/
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Initialize the database with the correct base directory
    db = BIC_DB(base_dir=str(BASE_DIR))
    
    # Initialize and run the Textual application
    app = BIC_TUI(db_core=db)
    app.run()
