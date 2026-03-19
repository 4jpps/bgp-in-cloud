from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, DataTable

from bic.core import BIC_DB

class ListAllocationsScreen(Screen):
    """Screen to list all IP address allocations."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("IP Address Allocations", classes="title")
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "IP Address", "Client", "Pool", "Description")
        allocations = self.db_core.find_all("ip_allocations")
        for alloc in allocations:
            client = self.db_core.find_one("clients", {"id": alloc['client_id']})
            pool = self.db_core.find_one("ip_pools", {"id": alloc['pool_id']})
            table.add_row(
                str(alloc['id']),
                alloc['ip_address'],
                client['name'] if client else "N/A",
                pool['name'] if pool else "N/A",
                alloc['description']
            )
