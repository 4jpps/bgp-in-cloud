from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, FormSelectOption
from bic.modules import client_management, network_management
from bic.core import BIC_DB

def get_ip_pool_options(db_core: BIC_DB):
    pools = db_core.find_all("ip_pools")
    options = []
    for p in pools:
        try:
            prefix = p['cidr'].split('/')[1]
            label = p.get('description') or p['name']
            value = f"{p['id']}_{p['afi']}_{prefix}"
            options.append(FormSelectOption(label=label, value=value))
        except IndexError:
            continue # Skip pools with invalid CIDR format
    return options

def get_client_type_options(db_core: BIC_DB):
    # In the future, this could come from a dedicated table
    return [
        FormSelectOption(label="Standard", value="Standard"),
        FormSelectOption(label="Transit", value="Transit"),
    ]

# Loader function for the edit form
def load_client_for_edit(db_core: BIC_DB, id: int):
    client = db_core.find_one("clients", {"id": id})
    if client:
        client['ip_allocations'] = db_core.find_all_by('ip_allocations', {'client_id': id})
        client['ip_subnets'] = db_core.find_all_by('ip_subnets', {'client_id': id})
    return client

# Define Actions
add_subnet_action = UIAction(
    name="Add Subnet",
    handler=network_management.allocate_next_available_subnet,
    form_fields=[
        FormField(name="client_id", type="hidden"),
        FormField(name="pool_id", label="Subnet Pool", type="select", options_loader=get_ip_pool_options, required=True),
        FormField(name="prefix_len", label="Prefix Length", type="number", required=True),
        FormField(name="description", label="Description", required=True),
    ]
)

edit_client_action = UIAction(
    name="Edit Client",
    handler=client_management.edit_client_from_form,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="email", label="Email", type="email"),
        FormField(name="type", label="Client Type", type="select", options_loader=get_client_type_options, required=True),
    ],
    actions=[]
)

delete_client_action = UIAction(
    name="Delete Client",
    handler=client_management.delete_client_from_form,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Client to Delete"),
    ]
)

def send_email_handler(db_core: BIC_DB, id: int):
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, id)
    return {"success": True, "message": "Welcome email sent successfully."}

send_welcome_email_action = UIAction(
    name="Send Welcome Email",
    handler=send_email_handler,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Send Welcome Email to"),
    ]
)

# Define Views
view_clients = UIView(
    name="List Clients",
    handler=lambda db: db.find_all("clients"),
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "email", "label": "Email"},
        {"key": "type", "label": "Type"},
    ],
    actions=[
        UIMenuItem(name="Edit", path="/clients/edit", item=edit_client_action),
        UIMenuItem(name="Delete", path="/clients/delete", item=delete_client_action),
        UIMenuItem(name="Send Email", path="/clients/send-email", item=send_welcome_email_action),
        UIMenuItem(name="View Configs", path="/clients/configs", item=None), # Special case handled in template
    ]
)

# Define the menu
client_menu = UIMenu(
    name="Client Management",
    items=[
        UIMenuItem(name="List Clients", path="/clients/list", item=view_clients),
        UIMenuItem(name="Provision New Client", path="/clients/provision/new"), # Special workflow
        # Hidden items for routing actions from the list view
        UIMenuItem(name="Edit Client", path="/clients/edit", item=edit_client_action, hidden=True),
        UIMenuItem(name="Delete Client", path="/clients/delete", item=delete_client_action, hidden=True),
        UIMenuItem(name="Send Welcome Email", path="/clients/send-email", item=send_welcome_email_action, hidden=True),
        UIMenuItem(name="Add Subnet", path="/clients/add-subnet", item=add_subnet_action, hidden=True),
    ]
)
