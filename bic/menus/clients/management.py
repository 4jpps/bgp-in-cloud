from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Button, Static
from textual.containers import VerticalScroll

from bic.core import BIC_DB
from bic.menus.clients.add import AddClientScreen
from bic.menus.clients.edit import EditClientScreen
from bic.menus.clients.bgp import BGSessionScreen

class ClientSelectScreen(Screen):
    """Screen to select a client and an action to perform."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Client Management", classes="title")
        with VerticalScroll() as vs:
            clients = self.db_core.find_all("clients")
            if not clients:
                yield Static("No clients found.")
            else:
                for client in clients:
                    yield Static(f"[bold]{client['name']}[/bold] (ID: {client['id']})")
                    yield Button("Edit Details", id=f"edit_{client['id']}")
                    yield Button("Manage BGP Session", id=f"bgp_{client['id']}", disabled=True) # Future feature
                    yield Button("Delete Client", id=f"delete_{client['id']}")
                    yield Static("---") # Separator
        yield Button("Add New Client", id="add_client", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        # Re-compose the screen every time it's mounted to get fresh data
        self.query(VerticalScroll).first().remove()
        self.mount(self.compose_clients())

    def compose_clients(self) -> VerticalScroll:
        vs = VerticalScroll()
        clients = self.db_core.find_all("clients")
        if not clients:
            vs.mount(Static("No clients found."))
        else:
            for client in clients:
                vs.mount(Static(f"[bold]{client['name']}[/bold] (ID: {client['id']})"))
                vs.mount(Button("Edit Details", id=f"edit_{client['id']}"))
                vs.mount(Button("Manage BGP Session", id=f"bgp_{client['id']}"))
                vs.mount(Button("Delete Client", id=f"delete_{client['id']}"))
                vs.mount(Static("---"))
        return vs

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_client":
            self.app.push_screen(AddClientScreen(self.db_core))
        elif event.button.id and event.button.id.startswith("edit_"):
            client_id = int(event.button.id.split("_")[1])
            self.app.push_screen(EditClientScreen(self.db_core, client_id))
        elif event.button.id and event.button.id.startswith("bgp_"):
            client_id = int(event.button.id.split("_")[1])
            self.app.push_screen(BGSessionScreen(self.db_core, client_id))
        elif event.button.id and event.button.id.startswith("delete_"):
            client_id = int(event.button.id.split("_")[1])
            # In a real app, you would ask for confirmation here
            self.db_core.delete("clients", client_id)
            self.on_mount() # Refresh the list
