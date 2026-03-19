from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, Input, Select, Button, Label
from textual.containers import Vertical, Horizontal

from bic.core import BIC_DB

class ProvisionClientScreen(Screen):
    """A dedicated screen for the multi-step client provisioning workflow."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.ip_pools = self.db_core.find_all("ip_pools")
        self.assignment_count = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Provision New Client", classes="title")
        with Vertical(id="form-container"):
            yield Label("Client Details")
            yield Input(placeholder="Client Name", id="name")
            yield Input(placeholder="Client Email", id="email")
            yield Label("Client Type")
            yield Select([("Standard", "Standard"), ("BGP", "BGP")], id="client_type")
            yield Static("IP Assignments", classes="subtitle")
            yield Vertical(id="assignments-wrapper")
            yield Button("+ Add Assignment", id="add_assignment")
            yield Button("Provision Client", id="submit_button", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        # Add the first assignment row automatically
        self.add_assignment_row()

    def add_assignment_row(self):
        self.assignment_count += 1
        wrapper = self.query_one("#assignments-wrapper")
        pool_options = [(pool.get('description', pool['name']), pool['id']) for pool in self.ip_pools]
        
        assignment_container = Horizontal(id=f"assign_row_{self.assignment_count}")
        with assignment_container:
            yield Select(pool_options, id=f"pool_{self.assignment_count}")
            yield Select([("Single IP", "static"), ("Subnet", "subnet")], id=f"type_{self.assignment_count}")
            yield Input(placeholder="Prefix Len (e.g. 29 for IPv4, 64 for IPv6)", id=f"prefix_{self.assignment_count}", classes="hidden")
        
        wrapper.mount(assignment_container)
        # A bit of a hack to get the select widgets to update their display
        self.query(Select)[-1].refresh()
        self.query(Select)[-2].refresh()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id.startswith("type_"):
            row_num = event.select.id.split('_')[1]
            prefix_input = self.query_one(f"#prefix_{row_num}", Input)
            if event.value == "static":
                prefix_input.display = False
            else:
                prefix_input.display = True
                # Update placeholder based on pool family
                pool_select = self.query_one(f"#pool_{row_num}", Select)
                pool_id = pool_select.value
                pool = next((p for p in self.ip_pools if p['id'] == pool_id), None)
                if pool and ':' in pool['cidr']:
                    prefix_input.placeholder = "Prefix Len (e.g. 64 or 56 for IPv6)"
                else:
                    prefix_input.placeholder = "Prefix Len (e.g. 29 or 27 for IPv4)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_assignment":
            self.add_assignment_row()
        elif event.button.id == "submit_button":
            name = self.query_one("#name", Input).value
            email = self.query_one("#email", Input).value
            client_type = self.query_one("#client_type", Select).value
            
            assignments = []
            for i in range(1, self.assignment_count + 1):
                pool_id = self.query_one(f"#pool_{i}", Select).value
                assign_type = self.query_one(f"#type_{i}", Select).value
                prefix = self.query_one(f"#prefix_{i}", Input).value
                
                assignment = {"pool_id": pool_id, "type": assign_type}
                if assign_type == 'subnet':
                    assignment["prefix_len"] = int(prefix)
                assignments.append(assignment)

            # ... (Call the core provisioning logic) ...
            from bic.modules import client_management, network_management
            asn = None
            if client_type == "BGP":
                asn = network_management.get_next_available_asn(self.db_core)
            
            try:
                result = client_management.provision_new_client(
                    db_core=self.db_core,
                    client_name=name,
                    client_email=email,
                    client_type=client_type,
                    asn=asn,
                    assignments=assignments
                )
                if result.get("success"):
                    self.app.pop_screen()
                else:
                    self.query_one(".title").update(f"[bold red]Error: {result.get('message')}[/]")
            except Exception as e:
                self.query_one(".title").update(f"[bold red]Error: {e}[/]")
