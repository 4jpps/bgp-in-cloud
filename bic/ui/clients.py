from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, FormSelectOption, TableColumn
from bic.modules import client_management, network_management, email_notifications
from bic.core import BIC_DB

# --- Loader Functions for Form Fields ---

def get_ip_pool_options(db_core: BIC_DB, **kwargs):
    pools = db_core.find_all("ip_pools")
    return [FormSelectOption(label=f"{p['name']} ({p['cidr']})", value=p['id']) for p in pools]

def get_client_type_options(db_core: BIC_DB, **kwargs):
    return [
        FormSelectOption(label="Standard", value="Standard"),
        FormSelectOption(label="Transit", value="Transit"),
    ]

# --- Loader Functions for Views/Actions ---

def load_client_for_view(db_core: BIC_DB, id: int, **kwargs):
    """Loads a client and all their related data for a detailed view."""
    client = db_core.find_one("clients", {"id": id})
    if client:
        # Load IP allocations and WireGuard peer info
        client['allocations'] = db_core.find_all('ip_allocations', {'client_id': id})
        client['wireguard_peer'] = db_core.find_one('wireguard_peers', {'client_id': id})
    return client

# --- Define Actions ---

provision_client_action = UIAction(
    name="Provision New Client",
    handler=client_management.provision_new_client,
    redirect_to="/page/clients/list",
    form_fields=[
        FormField(name="name", label="Client Name", required=True),
        FormField(name="email", label="Client Email", type="email", required=True),
        FormField(name="type", label="Client Type", type="select", options_loader=get_client_type_options, required=True),
        FormField(name="asn", label="BGP ASN", type="number", help_text="Private ASN in the range 64512-65534. Required for Transit clients."),
    ],
)

edit_client_action = UIAction(
    name="Edit Client",
    handler=client_management.update_client_details,
    redirect_to="/page/clients/list",
    loader=load_client_for_view,
    form_fields=[
        FormField(name="id", label="ID", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="email", label="Email", type="email"),
        FormField(name="type", label="Client Type", type="select", options_loader=get_client_type_options, required=True),
        # Fields for adding a new assignment
        FormField(name="assignment_pool_id[]", label="Assign from Pool", type="select", options_loader=get_ip_pool_options),
        FormField(name="assignment_type[]", label="Assignment Type", type="select", options=[
            FormSelectOption(label="Static IP", value="static"),
            FormSelectOption(label="Subnet", value="subnet"),
        ]),
        FormField(name="assignment_prefix[]", label="Subnet Prefix", placeholder="e.g., 29 (for /29)"),
        FormField(name="assignment_prefix_ipv6[]", label="IPv6 Subnet Prefix", type="select", options_loader=network_management.get_ipv6_subnet_options),
    ],
)

delete_client_action = UIAction(
    name="Delete Client",
    handler=client_management.deprovision_and_delete_client,
    redirect_to="/page/clients/list",
    loader=load_client_for_view,
    form_fields=[
        FormField(name="id", label="ID", type="hidden"),
        FormField(name="name", label="Client to Delete", readonly=True),
    ]
)

send_welcome_email_action = UIAction(
    name="Send Welcome Email",
    handler=email_notifications.send_client_welcome_email,
    redirect_to="/page/clients/list",
    loader=load_client_for_view,
    form_fields=[
        FormField(name="id", label="ID", type="hidden"),
        FormField(name="name", label="Send Welcome Email to", readonly=True),
    ]
)

# --- Define Views ---

view_clients_list = UIView(
    name="List Clients",
    template="clients_list.html",
    handler=lambda db_core, **kwargs: db_core.find_all("clients"),
    context_name="clients",
    table_columns=[
        TableColumn(name="name", label="Name"),
        TableColumn(name="email", label="Email"),
        TableColumn(name="type", label="Type"),
        TableColumn(name="asn", label="ASN"),
    ],
    actions=[
        UIMenuItem(name="Edit", path="edit"),
        UIMenuItem(name="Delete", path="delete"),
        UIMenuItem(name="Configs", path="configs"),
        UIMenuItem(name="Send Email", path="send-email"),
    ]
)

view_client_detail = UIView(
    name="Client Detail",
    template="client_configs.html",
    handler=load_client_for_view,
    context_name="client",
)

# --- Define the Menu Structure ---

client_menu = UIMenu(
    name="Client Management",
    items=[
        UIMenuItem(name="List Clients", path="list", item=view_clients_list),
        UIMenuItem(name="Provision New Client", path="provision", item=provision_client_action),
        # The following are hidden because they are accessed via actions on the list page,
        # but they still need to exist in the tree for the router to find them.
        UIMenuItem(name="Edit Client", path="edit/{id}", item=edit_client_action, hidden=True),
        UIMenuItem(name="Delete Client", path="delete/{id}", item=delete_client_action, hidden=True),
        UIMenuItem(name="Client Details", path="configs/{id}", item=view_client_detail, hidden=True),
        UIMenuItem(name="Send Email", path="send-email/{id}", item=send_welcome_email_action, hidden=True),
    ]
)
