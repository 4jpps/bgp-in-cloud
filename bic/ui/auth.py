from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField
from bic.modules import user_management

login_action = UIAction(
    name="Login",
    handler=user_management.login_user,
    redirect_to="/",
    form_fields=[
        FormField(name="username", label="Username", required=True),
        FormField(name="password", label="Password", type="password", required=True),
    ],
)

login_view = UIView(
    name="Login",
    template="login.html",
    handler=None,
)


two_fa_view = UIView(
    name="Two-Factor Authentication",
    template="2fa.html",
)


auth_menu = UIMenu(
    name="Authentication",
    items=[
        UIMenuItem(name="Login", path="/login", item=login_view),
        UIMenuItem(name="Login Action", path="/login", item=login_action, hidden=True),
        UIMenuItem(name="2FA", path="/2fa", item=two_fa_view, hidden=True),
    ]
)
