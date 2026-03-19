from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import network_management
from bic.core import BIC_DB

# Loader function for the edit form
def load_pool_for_edit(db_core: BIC_DB, id: int):
    return db_core.find_one("ip_pools", {"id": id})

# Define Actions and Views
edit_pool = UIAction(
    name="Edit Pool",
    handler=network_management.edit_pool_from_form,
    loader=load_pool_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="description", label="Description"),
    ]
)

delete_pool = UIAction(
    name="Delete Pool",
    handler=network_management.delete_pool_from_form,
    form_fields=[
        FormField(name="id", type="hidden"),
    ]
)

swap_pool = UIAction(
    name="Swap Pool CIDR",
    handler=network_management.swap_pool_prefix,
    loader=load_pool_for_edit, # Can reuse the edit loader
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Pool Name (Cannot be changed)"),
        FormField(name="new_cidr", label="New CIDR", required=True),
    ]
)

view_pools = UIView(
    name="List IP Pools",
    handler=lambda db: db.find_all("ip_pools"),
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "cidr", "label": "CIDR"},
        {"key": "afi", "label": "Family"},
        {"key": "description", "label": "Description"},
    ],
    actions=[
        edit_pool,
        delete_pool,
        swap_pool,
    ]
)

add_pool = UIAction(
    name="Add IP Pool",
    handler=network_management.add_pool,
    form_fields=[
        FormField(name="name", label="Name", required=True),
        FormField(name="cidr", label="CIDR", required=True),
        FormField(name="afi", label="Address Family", required=True, type="select", options=["ipv4", "ipv6"]),
        FormField(name="description", label="Description"),
    ]
)

list_allocations = UIView(
    name="List All Allocations",
    handler=network_management.list_all_allocations_joined,
    columns=[
        {"key": "ip_address", "label": "IP Address"},
        {"key": "client_name", "label": "Client"},
        {"key": "pool_name", "label": "Pool"},
        {"key": "description", "label": "Description"},
    ]
)

find_free_ip = UIAction(
    name="Find Free IP",
    handler=network_management.find_free_ip_for_web, # A new web-specific handler
    form_fields=[
        FormField(
            name="pool_id", 
            label="IP Pool", 
            type="select", 
            db_source_table="ip_pools", 
            db_source_display_key="name"
        ),
    ]
)

# Define the menu
network_menu = UIMenu(
    name="Network Management",
    items=[
        UIMenuItem(name="List IP Pools", path="/network/pools/list", item=view_pools),
        UIMenuItem(name="Add IP Pool", path="/network/pools/add", item=add_pool),
        UIMenuItem(name="List All Allocations", path="/network/allocations/list", item=list_allocations),
        UIMenuItem(name="Find Free IP", path="/network/find-free-ip", item=find_free_ip),
    ]
)
