from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, FormSelectOption
from bic.modules import client_management
from bic.core import BIC_DB

def list_clients(db_core: BIC_DB):
    return db_core.find_all("clients")

def load_client_for_edit(db_core: BIC_DB, id: str):
    client = db_core.find_one("clients", {"id": id})
    client['ip_allocations'] = db_core.find_all_by('ip_allocations', {'client_id': id})
    client['ip_subnets'] = db_core.find_all_by('ip_subnets', {'client_id': id})
    return client

def get_client_type_options(db_core: BIC_DB):
    return [
        FormSelectOption(label="Standard", value="Standard"),
        FormSelectOption(label="Transit", value="Transit"),
    ]

# Views
view_clients = UIView(
    name="List Clients",
    handler=list_clients,
    columns=[
        {"key": "display_id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "email", "label": "Email"},
        {"key": "type", "label": "Type"},
    ],
    actions=[
        UIMenuItem(name="Edit", path="/clients/edit"),
        UIMenuItem(name="Delete", path="/clients/delete"),
        UIMenuItem(name="Send Email", path="/clients/send-email"),
        UIMenuItem(name="View Configs", path="/clients/configs"),
    ]
)

# Actions
edit_client_action = UIAction(
    name="Edit Client",
    handler=client_management.edit_client_from_form,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="email", label="Email", type="email"),
        FormField(name="type", label="Client Type", type="select", options_loader=get_client_type_options, required=True),
    ]
)
# ... (other actions remain the same)

client_menu = UIMenu(
    name="Client Management",
    items=[
        UIMenuItem(name="List Clients", path="/clients/list", item=view_clients),
        UIMenuItem(name="Provision New Client", path="/clients/provision/new"),
    ]
)
