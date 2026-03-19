from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import bgp_management
from bic.core import BIC_DB

# Define Actions and Views
view_bgp_sessions = UIView(
    name="List BGP Sessions",
    handler=bgp_management.list_bgp_sessions,
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "client_name", "label": "Client"},
        {"key": "client_asn", "label": "ASN"},
        {"key": "state", "label": "State"},
        {"key": "last_updated", "label": "Last Updated"},
    ]
)

# Define the menu
bgp_menu = UIMenu(
    name="BGP Management",
    items=[
        UIMenuItem(name="List BGP Sessions", path="/bgp/sessions/list", item=view_bgp_sessions),
    ]
)
