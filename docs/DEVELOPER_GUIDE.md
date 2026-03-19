# BIC IPAM Developer Guide

This guide provides instructions for developers on how to extend the BIC IPAM application by adding new features, views, and actions. It is essential to follow this guide to maintain the consistency and stability of the unified architecture.

---

## Core Philosophy: The Unified UI Schema

The entire application—both the Web UI and the Text-based UI (TUI)—is dynamically generated from a single, declarative source of truth located in the `bic/ui/` directory. This means that to add a new feature, you do **not** write any presentation-specific code (like HTML or Textual layout code). Instead, you simply define the feature using the provided Python `dataclasses`.

The main building blocks, defined in `bic/ui/schema.py`, are:

- **`UIView`**: Represents a screen that displays a list of items in a table (e.g., List Clients).
- **`UIAction`**: Represents a screen that performs an action, usually via a form (e.g., Add Pool, Edit Client, Swap Pool).
- **`UIMenu`**: A container that holds a list of `UIMenuItem`s, which can be other menus, views, or actions.

By defining your feature using these classes, the generic rendering engines in `webapp.py` and `bic/tui/generic_screens.py` will automatically build the correct interface for both platforms.

---

## How to Add a New Feature (Example: A "System Reboot" Action)

Let's walk through adding a simple new feature: a "System Reboot" action that asks for confirmation and then runs a command.

### Step 1: Write the Backend Logic

All core business logic belongs in a module within the `bic/modules/` directory. Since this is a system-level action, we'll add our logic to `bic/modules/system_management.py`.

```python
# In bic/modules/system_management.py

import subprocess

def reboot_system(db_core, confirmation: str):
    """Reboots the system if the user confirms."""
    if confirmation.lower() != 'yes':
        return {"success": False, "message": "Reboot cancelled."}
    
    # This is a placeholder for the actual reboot command
    # In a real scenario, you might run: subprocess.run(["sudo", "reboot"], check=True)
    print("SYSTEM IS REBOOTING NOW...")
    return {"success": True, "message": "System is rebooting."}
```

### Step 2: Define the UI

Now, we define how this action should appear in the UI. Since it's a system action, we'll add the definition to `bic/ui/system.py`.

We will create a `UIAction` object. This object tells the rendering engines to build a form.

```python
# In bic/ui/system.py

# ... (import statements)
from bic.modules import system_management

# ... (other definitions)

# Define the new action
reboot_action = UIAction(
    name="Reboot System",
    handler=system_management.reboot_system,
    form_fields=[
        FormField(name="confirmation", label="Type \'yes\' to confirm reboot", required=True)
    ]
)
```

### Step 3: Add the Item to the Menu

Finally, we need to make the action accessible by adding it to a menu. We'll add a `UIMenuItem` to the `system_menu` in `bic/ui/system.py`.

```python
# In bic/ui/system.py, find the system_menu definition

system_menu = UIMenu(
    name="System",
    items=[
        UIMenuItem(name="Dashboard", path="/", item=None), # Special case
        UIMenuItem(name="Settings", path="/system/settings", item=edit_settings),
        # Add our new item here!
        UIMenuItem(name="Reboot System", path="/system/reboot", item=reboot_action),
    ]
)
```

### That's It!

With these three simple steps, you have added a new "Reboot System" feature. Because of the unified architecture:

- A "Reboot System" option will automatically appear in the "System" menu in **both** the Web UI and the TUI.
- Clicking it will navigate to a new page/screen.
- A form with a single text box (`Type 'yes' to confirm reboot`) will be dynamically generated.
- Submitting the form will correctly call your `reboot_system` function.

This process applies to all new features. By separating the core logic (`modules`) from the UI definition (`ui`), the system remains clean, consistent, and easy to extend.
