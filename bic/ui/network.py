from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, TableColumn
from bic.modules import network_management

# --- Views ---
view_allocations = UIView(
    name="IP Allocations",
    template="pools_list.html",
    handler=network_management.list_allocations_with_details,
    table_columns=[
        TableColumn(name="pool_name", label="Pool"),
        TableColumn(name="client_name", label="Client"),
        TableColumn(name="address", label="Allocation"),
        TableColumn(name="description", label="Description"),
    ]
)

# --- IP Pool Actions ---
add_pool_action = UIAction(
    name="Add IP Pool",
    handler=network_management.add_pool,
    redirect_to="/page/network/pools",
    template="generic_form.html",
    form_fields=[
        FormField(name="name", label="Pool Name", required=True),
        FormField(name="cidr", label="CIDR (e.g., 10.0.0.0/8)", required=True),
        FormField(name="description", label="Description"),
    ]
)

list_pools_view = UIView(
    name="List IP Pools",
    handler=lambda db_core, **kwargs: db_core.find_all('ip_pools'),
    template="allocations_list.html",
    table_columns=[
        TableColumn(name="name", label="Pool Name"),
        TableColumn(name="cidr", label="CIDR"),
        TableColumn(name="description", label="Description"),
    ],
    actions=[
        {"name": "Add Pool", "path": "/page/network/pools/add"},
    ]
)

view_routing_table = UIView(
    name="Routing Table",
    template="routing_table.html",
    handler=network_management.get_routing_table,
)

# --- Menu ---
network_menu = UIMenu(
    name="Network Management",
    items=[
        UIMenuItem(name="IP Pools", path="pools", item=list_pools_view),
        UIMenuItem(name="Add IP Pool", path="pools/add", item=add_pool_action, hidden=True),
        UIMenuItem(name="IP Allocations", path="allocations", item=view_allocations),
        UIMenuItem(name="Routing Table", path="routing-table", item=view_routing_table),
    ]
)
