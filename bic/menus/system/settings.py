from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.modules import settings_management

class SettingsScreen(Screen):
    """Screen to edit system settings."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.settings = settings_management.get_all_settings(self.db_core)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("System Settings", classes="title")
        with VerticalScroll() as vs:
            # Email Settings
            yield Static("[bold]Email Settings[/bold]")
            yield Input(value=self.settings.get('smtp_host', ''), placeholder="SMTP Host", id="smtp_host")
            yield Input(value=str(self.settings.get('smtp_port', '')), placeholder="SMTP Port", id="smtp_port")
            yield Input(value=self.settings.get('smtp_user', ''), placeholder="SMTP User", id="smtp_user")
            yield Input(value=self.settings.get('smtp_pass', ''), placeholder="SMTP Password", password=True, id="smtp_pass")
            yield Input(value=self.settings.get('smtp_from', ''), placeholder="From Address", id="smtp_from")
            yield Static("---")
            # Other settings can be added here

        yield Button("Save Settings", id="save_settings", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings":
            settings_to_save = {
                "smtp_host": self.query_one("#smtp_host", Input).value,
                "smtp_port": self.query_one("#smtp_port", Input).value,
                "smtp_user": self.query_one("#smtp_user", Input).value,
                "smtp_pass": self.query_one("#smtp_pass", Input).value,
                "smtp_from": self.query_one("#smtp_from", Input).value,
            }
            for key, value in settings_to_save.items():
                self.db_core.set_setting(key, value)
            
            self.app.pop_screen()
