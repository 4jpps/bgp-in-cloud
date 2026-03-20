#!/usr/bin/env python
"""
This file defines the UI structure for the User Management section.
"""

from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, TableColumn
from bic.modules import user_management

# --- User Management Actions & Views ---

list_users_view = UIView(
    name="List Users",
    template="user_list.html",
    handler=user_management.list_users,
    table_columns=[
        TableColumn(name="username", label="Username"),
        TableColumn(name="email", label="Email"),
        TableColumn(name="role", label="Role"),
        TableColumn(name="last_login", label="Last Login"),
    ],
    actions=[
        {"name": "Edit", "path": "/page/system/users/edit/{id}"},
        {"name": "Manage Passkeys", "path": "/page/system/users/passkeys/{id}"},
        {"name": "Manage YubiKeys", "path": "/page/system/users/yubikeys/{id}"},
        {"name": "Manage Google Authenticator", "path": "/page/system/users/google-authenticator/{id}"},
        UIAction(name="Delete", handler=user_management.delete_user, redirect_to="/page/system/users/list", form_fields=[]),
    ]
)

manage_google_authenticator_view = UIView(
    name="Manage Google Authenticator",
    template="manage_google_authenticator.html",
    loader=user_management.get_user,
)

manage_yubikeys_view = UIView(
    name="Manage YubiKeys",
    template="manage_yubikeys.html",
    loader=user_management.get_user,
)

manage_passkeys_view = UIView(
    name="Manage Passkeys",
    template="manage_passkeys.html",
    loader=user_management.get_user,
)

add_user_action = UIAction(
    name="Add User",
    handler=user_management.create_user,
    redirect_to="/page/system/users/list",
    template="generic_form.html",
    form_fields=[
        FormField(name="username", label="Username", required=True),
        FormField(name="email", label="Email", type="email", required=True),
        FormField(name="password", label="Password", type="password", required=True),
        FormField(name="role", label="Role", type="select", options=['user', 'admin'], required=True),
    ]
)

edit_user_action = UIAction(
    name="Edit User",
    handler=user_management.update_user,
    redirect_to="/page/system/users/list",
    template="generic_form.html",
    loader=user_management.get_user,
    form_fields=[
        FormField(name="username", label="Username", required=True),
        FormField(name="email", label="Email", type="email", required=True),
        FormField(name="role", label="Role", type="select", options=['user', 'admin'], required=True),
        FormField(name="password", label="New Password", type="password", required=False, help_text="Leave blank to keep the current password."),
    ]
)

delete_user_action = UIAction(
    name="Delete User",
    handler=user_management.delete_user,
    redirect_to="/page/system/users/list",
    form_fields=[]
)

users_menu = UIMenu(
    name="User Management",
    required_role="admin",
    items=[
        UIMenuItem(name="List Users", path="list", item=list_users_view),
        UIMenuItem(name="Add User", path="add", item=add_user_action),
        UIMenuItem(name="Edit User", path="edit/{id}", item=edit_user_action, hidden=True),
        UIMenuItem(name="Manage Passkeys", path="passkeys/{id}", item=manage_passkeys_view, hidden=True),
        UIMenuItem(name="Manage YubiKeys", path="yubikeys/{id}", item=manage_yubikeys_view, hidden=True),
        UIMenuItem(name="Manage Google Authenticator", path="google-authenticator/{id}", item=manage_google_authenticator_view, hidden=True),
        UIMenuItem(name="Delete User", path="delete/{id}", item=delete_user_action, hidden=True),
    ]
)
