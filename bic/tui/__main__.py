from textual.app import App
from .main_menu import MainMenuScreen
from bic.core import BIC_DB

if __name__ == "__main__":
    db = BIC_DB()
    app = App()
    app.run(MainMenuScreen(db))