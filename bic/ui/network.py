from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, FormSelectOption
from bic.modules import network_management
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

# Loader function for the edit form
def load_pool_for_edit(db_core: BIC_DB, id: int):
    return db_core.find_one("ip_pools", {"id": id})

# Define Actions
edit_pool_action = UIAction(
    name="Edit Pool",
    handler=network_management.edit_pool_from_form,
    loader=load_pool_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="cidr", label="CIDR", required=True),
        FormField(name="description", label="Description"),
    ]
)

delete_pool_action = UIAction(
    name="Delete Pool",
    handler=network_management.delete_pool_from_form,
    loader=load_pool_for_edit, # To show which pool is being deleted
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Pool to Delete"),
    ]
)

swap_pool_action = UIAction(
    name="Swap Pool CIDR",
    handler=network_management.swap_pool_prefix,
    loader=load_pool_for_edit, # Can reuse the edit loader
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Pool Name (Cannot be changed)"),
        FormField(name="new_cidr", label="New CIDR", required=True),
    ]
)

# Define Views
view_pools = UIView(
    name="List IP Pools",
    handler=lambda db: db.find_all("ip_pools"),
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "cidr", "label": "CIDR"},
        {"key": "description", "label": "Description"},
    ],
    actions=[
        UIMenuItem(name="Edit", path="/network/pools/edit", item=edit_pool_action),
        UIMenuItem(name="Delete", path="/network/pools/delete", item=delete_pool_action),
        UIMenuItem(name="Swap CIDR", path="/network/pools/swap", item=swap_pool_action),
    ]
)

add_pool_action = UIAction(
    name="Add IP Pool",
    handler=network_management.add_pool,
    form_fields=[
        FormField(name="name", label="Name", required=True),
        FormField(name="cidr", label="CIDR", required=True),
        FormField(name="description", label="Description"),
    ]
)

list_allocations_view = UIView(
    name="List All Allocations",
    handler=network_management.list_all_allocations_joined,
    columns=[
        {"key": "ip_address", "label": "IP Address"},
        {"key": "client_name", "label": "Client"},
        {"key": "pool_name", "label": "Pool"},
        {"key": "description", "label": "Description"},
    ]
)

find_free_ip_action = UIAction(
    name="Find Free IP",
    handler=network_management.find_free_ip_for_web,
    form_fields=[
        FormField(name="pool_id", label="IP Pool", type="select", options_loader=get_ip_pool_options, required=True),
    ]
)

# Define the menu
network_menu = UIMenu(
    name="Network Management",
    items=[
        UIMenuItem(name="List IP Pools", path="/network/pools/list", item=view_pools),
        UIMenuItem(name="Add IP Pool", path="/network/pools/add", item=add_pool_action),
        UIMenuItem(name="List All Allocations", path="/network/allocations/list", item=list_allocations_view),
        UIMenuItem(name="Find Free IP", path="/network/find-free-ip", item=find_free_ip_action),
        # Hidden items for routing actions from the list view
        UIMenuItem(name="Edit Pool", path="/network/pools/edit", item=edit_pool_action, hidden=True),
        UIMenuItem(name="Delete Pool", path="/network/pools/delete", item=delete_pool_action, hidden=True),
        UIMenuItem(name="Swap Pool CIDR", path="/network/pools/swap", item=swap_pool_action, hidden=True),
    ]
)
