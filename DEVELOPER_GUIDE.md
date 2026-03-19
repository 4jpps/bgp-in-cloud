# BGP in the Cloud (BIC) - Developer Guide

## Table of Contents
1.  [Architectural Overview](#architectural-overview)
2.  [Part 1: Creating a New Module (Backend Logic)](#part-1-creating-a-new-module-backend-logic)
3.  [Part 2: Database Integration](#part-2-database-integration)
4.  [Part 3: Creating a New Menu (UI Integration)](#part-3-creating-a-new-menu-ui-integration)
5.  [Complete Example: A "Firewall Rules" Module](#complete-example-a-firewall-rules-module)

---

## Architectural Overview

This application is built on a **definition-driven architecture**. The core principle is that the user interface (both the TUI and the Web UI) is dynamically generated at runtime from a single, centralized data structure. This ensures consistency and makes adding new features incredibly efficient.

The central file governing this architecture is **`bic/menus/menu_structure.py`**. By adding an entry to this file, you are telling the application about your new feature. The TUI and Web UI will automatically create the necessary menus and forms based on the information you provide.

Your development workflow will always follow this pattern:
1.  **Create the backend logic** in a new `bic/modules/` file.
2.  **Define the database schema** for your new data in `bic/core.py`.
3.  **Create the UI definition** in `bic/menus/menu_structure.py`, which includes:
    a.  The TUI handler script.
    b.  The Web UI handler function and form definition.

---

## Part 1: Creating a New Module (Backend Logic)

All business logic must reside in the `bic/modules/` directory. These modules are the "engine" of the application and are called by both the TUI and the Web UI.

**1. Create the Module File:**

Create a new Python file in the `bic/modules/` directory. The filename should be descriptive and end in `_management.py` to maintain consistency.

*File Location:*
`bic/modules/new_feature_management.py`

**2. Write the Boilerplate Code:**

Your module should contain functions that perform specific actions. Every function that interacts with the database **must** accept `db_core: BIC_DB` as its first argument.

*Example `bic/modules/new_feature_management.py`*
```python
from bic.core import BIC_DB

# A function to add a new record
def add_new_item(db_core: BIC_DB, item_name: str, item_description: str):
    """Adds a new item to the database."""

    # ... (database logic will go here) ...

    # Always return a dictionary with a success status and a message
    return {"success": True, "message": f"Successfully added '{item_name}'."}

# A function to get all items
def get_all_items(db_core: BIC_DB):
    """Retrieves all items from the database."""
    items = db_core.find_all('new_items')
    return items
```

---

## Part 2: Database Integration

To store data for your new module, you must define its table schema in the central database core.

**1. Edit the Core Schema Definition:**

Open `bic/core.py` and locate the `SCHEMA` dictionary. This dictionary defines all tables and columns in the SQLite database.

**2. Add Your New Table:**

Add a new key to the `SCHEMA` dictionary. The key is the table name, and the value is a list of strings, where each string defines a column.

*Example addition to `bic/core.py`*
```python
SCHEMA = {
    "clients": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "name TEXT NOT NULL UNIQUE",
        # ... other columns
    ],
    # ... other tables
    "new_items": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "name TEXT NOT NULL",
        "description TEXT",
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ]
}
```

**3. Perform CRUD Operations:**

The `BIC_DB` class in `core.py` provides all the necessary methods (`insert`, `find_one`, `find_all`, `update`, `delete`). You use these methods within your module's functions.

*Example of using CRUD in `bic/modules/new_feature_management.py`*
```python
from bic.core import BIC_DB

def add_new_item(db_core: BIC_DB, item_name: str, item_description: str):
    item_id = db_core.insert('new_items', {
        'name': item_name,
        'description': item_description
    })
    if item_id:
        return {"success": True, "message": f"Successfully added '{item_name}'."}
    else:
        return {"success": False, "message": "Failed to add item."}
```

**Database Migrations:** The `BIC_DB` class handles schema creation automatically. When you add a new table definition, it will be created the next time the application runs. For column additions or modifications, a manual migration script may be required in the future, but for new tables, no extra steps are needed.

---

## Part 3: Creating a New Menu (UI Integration)

This is where you bring your new feature to life in the user interfaces.

**1. Edit the Menu Structure:**

Open `bic/menus/menu_structure.py` and add a new entry to the `MENU_STRUCTURE` dictionary.

*Example addition to `bic/menus/menu_structure.py`*
```python
"New Feature": {
    "type": "submenu",
    "handler": {
        "Add New Item": {
            "type": "action",
            "handler": "bic.menus.new_feature.add",  # TUI handler script
            "web_handler": "bic.modules.new_feature_management.add_new_item", # Web UI function
            "web_form": [
                {"label": "Item Name", "name": "item_name", "type": "text", "required": True},
                {"label": "Item Description", "name": "item_description", "type": "text"}
            ]
        }
    }
},
```

**2. Create the TUI Handler:**

Based on the `handler` path you defined (`bic.menus.new_feature.add`), create the corresponding file.

*File Location:*
`bic/menus/new_feature/add.py`

This TUI script is a thin presentation layer. Its only job is to get input from the user and call the backend module function.

*Example `bic/menus/new_feature/add.py`*
```python
from rich.prompt import Prompt
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import new_feature_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Add New Item[/bold underline]")

    item_name = Prompt.ask("Enter the item name")
    item_description = Prompt.ask("Enter the item description")

    result = new_feature_management.add_new_item(db_core, item_name, item_description)

    if result["success"]:
        console.print(f"\n[green]{result['message']}[/green]")
    else:
        console.print(f"\n[red]Error: {result['message']}[/red]")
```

**3. Web UI Integration (Automatic):**

**No further steps are needed for the Web UI.** The `webapp.py` server will automatically:
1.  Read the `web_handler` path and know which function to call.
2.  Read the `web_form` definition and use the `generic_action.html` template to render a complete HTML form for you.

---

## Complete Example: A "Firewall Rules" Module

Let's add a simple module to manage custom firewall rules.

**1. Database Schema (`bic/core.py`):**
```python
"firewall_rules": [
    "id INTEGER PRIMARY KEY AUTOINCREMENT",
    "protocol TEXT NOT NULL",
    "port INTEGER NOT NULL",
    "action TEXT NOT NULL DEFAULT 'ACCEPT'"
]
```

**2. Backend Module (`bic/modules/custom_firewall_management.py`):**
```python
from bic.core import BIC_DB

def add_firewall_rule(db_core: BIC_DB, protocol: str, port: int, action: str):
    db_core.insert('firewall_rules', {'protocol': protocol, 'port': port, 'action': action})
    # In a real scenario, you would also call a function to apply this rule to iptables
    return {"success": True, "message": f"Rule for {protocol}/{port} added."}
```

**3. Menu Definition (`bic/menus/menu_structure.py`):**
```python
"System Settings": {
    "type": "submenu",
    "handler": {
        // ... existing settings ...
        "Add Firewall Rule": {
            "type": "action",
            "handler": "bic.menus.system.add_firewall_rule",
            "web_handler": "bic.modules.custom_firewall_management.add_firewall_rule",
            "web_form": [
                {"label": "Protocol", "name": "protocol", "type": "select", "options": ["TCP", "UDP"]},
                {"label": "Port Number", "name": "port", "type": "number", "required": True},
                {"label": "Action", "name": "action", "type": "select", "options": ["ACCEPT", "DROP"]}
            ]
        }
    }
},
```

**4. TUI Handler (`bic/menus/system/add_firewall_rule.py`):**
```python
from rich.prompt import Prompt
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import custom_firewall_management

def run(db_core: BIC_DB):
    console = Console()
    console.print("\n[bold underline]Add Custom Firewall Rule[/bold underline]")

    protocol = Prompt.ask("Protocol", choices=["TCP", "UDP"], default="TCP")
    port = int(Prompt.ask("Port Number"))
    action = Prompt.ask("Action", choices=["ACCEPT", "DROP"], default="ACCEPT")

    result = custom_firewall_management.add_firewall_rule(db_core, protocol, port, action)
    console.print(f"\n[green]{result['message']}[/green]")
```

By following these four steps, you have successfully extended the application with a new feature that is fully integrated into the database and available in both the TUI and the Web UI, all while strictly adhering to the project's architecture.
