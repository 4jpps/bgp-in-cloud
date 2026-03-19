from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import client_management
from bic.core import BIC_DB

# Loader function for the edit form
def load_client_for_edit(db_core: BIC_DB, id: int):
    return db_core.find_one("clients", {"id": id})

# Define Actions and Views first
edit_client = UIAction(
    name="Edit Client",
    handler=client_management.edit_client_from_form,
    loader=load_client_for_edit,
    form_fields=[
        FormField(name="id", type="hidden"),
        FormField(name="name", label="Name", required=True),
        FormField(name="email", label="Email", type="email"),
    ]
)

delete_client = UIAction(
    name="Delete Client",
    handler=client_management.delete_client_from_form,
    form_fields=[
        FormField(name="id", type="hidden"),
    ]
)

def send_email_action(db_core: BIC_DB, id: int):
    from bic.modules.email_notifications import send_client_welcome_email
    send_client_welcome_email(db_core, id)
    return {"success": True} # This action doesn't redirect, just performs a task

send_welcome_email = UIAction(
    name="Send Welcome Email",
    handler=send_email_action,
    form_fields=[
        FormField(name="id", type="hidden"),
    ]
)

view_clients = UIView(
    name="List Clients",
    handler=lambda db: db.find_all("clients"),
    columns=[
        {"key": "id", "label": "ID"},
        {"key": "name", "label": "Name"},
        {"key": "email", "label": "Email"},
    ],
    actions=[
        edit_client,
        delete_client,
        send_welcome_email,
    ]
)

# Define the menu that uses them
client_menu = UIMenu(
    name="Client Management",
    items=[
        UIMenuItem(name="List Clients", path="/clients/list", item=view_clients),
        UIMenuItem(name="Provision New Client", path="/clients/provision/new"), # This now correctly points to the special workflow
    ]
)

# We need a way to register this menu with the main application
# For now, this file just defines the structure.
