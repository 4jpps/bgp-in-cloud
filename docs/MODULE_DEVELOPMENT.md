# BIC IPAM Module Development Guide

This guide provides technical standards and best practices for writing functions within the `bic/modules/` directory. Adhering to these standards is crucial for maintaining the stability and consistency of the application.

---

## Core Principles

1.  **Pure Business Logic**: Modules in this directory must contain *only* business logic. They should have no knowledge of the user interface. Functions should not print to the console (unless for specific, unavoidable error logging), nor should they contain any HTML, Textual widgets, or other presentation-layer code.

2.  **Database is the Entry Point**: All module functions that interact with data should accept the `db_core: BIC_DB` object as their first argument. This dependency injection ensures that all database operations go through the centralized `BIC_DB` class in `bic/core.py`.

3.  **Stateless Operations**: Functions should be as stateless as possible. All the information they need to perform an operation should be passed in as arguments. They should read from the database for state and write back to the database to persist changes.

---

## Function Signatures and Return Values

To ensure compatibility with the generic UI rendering engines, your handler functions should follow these conventions.

### For `UIView` Handlers

These functions are used to fetch lists of data for display in tables.

- **Signature**: `def my_list_handler(db_core: BIC_DB) -> list[dict]:`
- **Returns**: The function **must** return a `list` of `dict`s. Each dictionary in the list represents a row, and the keys of the dictionary should correspond to the `key` values you define in the `UIView`'s `columns`.

```python
# In bic/modules/client_management.py

def list_all_clients(db_core: BIC_DB) -> list[dict]:
    """Returns a list of all clients."""
    # The find_all method conveniently returns a list of dicts.
    return db_core.find_all("clients")
```

### For `UIAction` Handlers

These functions process form submissions.

- **Signature**: `def my_action_handler(db_core: BIC_DB, **kwargs):`
- **Arguments**: The function will receive all the fields from the form as keyword arguments (`kwargs`). The names of the arguments will match the `name` you gave each `FormField` in your `UIAction` definition.
- **Returns**: The function should return a `dict` with at least a `"success": True` or `"success": False` key. You can also include a `"message"` key for displaying errors to the user.

```python
# In bic/modules/network_management.py

def add_pool(db_core: BIC_DB, name: str, cidr: str, description: str):
    """Adds a new IP pool to the database."""
    try:
        net = ipaddress.ip_network(cidr)
        # ... (logic to add the pool)
        db_core.insert('ip_pools', {...})
        update_bird_configs(db_core)
        return {"success": True, "message": f"IP Pool '{name}' created."}
    except ValueError as e:
        return {"success": False, "message": str(e)}
```

### For `UIAction` Loaders

These optional functions pre-populate forms with data (e.g., for an "Edit" screen).

- **Signature**: `def my_loader_function(db_core: BIC_DB, id: int) -> dict:`
- **Arguments**: The function typically receives the `id` of the item to load.
- **Returns**: It **must** return a single `dict` containing the data for the item. The keys should match the `name`s of the `FormField`s in the form.

```python
# In bic/ui/clients.py (Loaders can also be defined here if they are simple)

def load_client_for_edit(db_core: BIC_DB, id: int):
    return db_core.find_one("clients", {"id": id})
```

---

## Interacting with Other Modules

It is common and encouraged for a module function to call functions in other modules. For example, the `provision_new_client` function in `client_management.py` is an orchestrator that calls functions in `network_management`, `wireguard_management`, `bgp_management`, and `email_notifications` to perform its complex task.

This practice keeps each module focused on its specific domain while allowing you to build powerful, high-level workflows.
