from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import client_management
from bic.core import BIC_DB

# Loader function for the edit form
def load_client_for_edit(db_core: BIC_DB, id: int):
    return db_core.find_one("clients", {"id": id})

# Define Actions
edit_client_action = UIAction(
    name="Edit Client",
    handler=client_management.edit_client_from_form,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="email", label="Email", type="email"),
    ]
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
    # This handler needs to return a dict for the web UI, even if it's just a success message
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
    ],
    actions=[
        UIMenuItem(name="Edit", path="/clients/edit", item=edit_client_action),
        UIMenuItem(name="Delete", path="/clients/delete", item=delete_client_action),
        UIMenuItem(name="Send Email", path="/clients/send-email", item=send_welcome_email_action),
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
    ]
)
