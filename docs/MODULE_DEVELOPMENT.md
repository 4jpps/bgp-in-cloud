# Module Development Guide

This guide explains how to extend the BGP in Cloud IPAM application by creating new modules.

## 1. Module Structure

Each functional area of the application is organized into a module. A module typically consists of:

-   A `_management.py` file containing the core business logic.
-   A `_ui.py` file defining the UI structure, including menus, views, and actions.

## 2. Creating a New Module

1.  **Create a Management File:**

    -   Create a new file in the `bic/modules` directory (e.g., `my_module_management.py`).
    -   Implement the functions that will handle the business logic for your module.

2.  **Create a UI File:**

    -   Create a new file in the `bic/ui` directory (e.g., `my_module_ui.py`).
    -   Define the UI structure for your module using the `UIMenu`, `UIView`, and `UIAction` classes from `bic/ui/schema.py`.

3.  **Integrate the Module:**

    -   In `bic/ui/main.py`, import your new UI menu and add it to the `main_menu`.

## 3. UI Schema

-   **`UIMenu`:** Represents a menu in the navigation structure.
-   **`UIMenuItem`:** A single item within a menu, which can link to a `UIView` or another `UIMenu`.
-   **`UIView`:** A page that displays information. It can have a `loader` function to fetch data and a `handler` to process data for display.
-   **`UIAction`:** A form that performs an action. It has a `handler` function to process the form data.

## 4. Example: Creating a "Hello World" Module

1.  **`bic/modules/hello_management.py`:**

    ```python
    def get_hello_message():
        return "Hello, World!"
    ```

2.  **`bic/ui/hello_ui.py`:**

    ```python
    from bic.ui.schema import UIMenu, UIMenuItem, UIView
    from bic.modules import hello_management

    hello_view = UIView(
        name="Hello",
        template="hello.html",
        handler=hello_management.get_hello_message,
    )

    hello_menu = UIMenu(
        name="Hello",
        items=[
            UIMenuItem(name="Say Hello", path="/say-hello", item=hello_view),
        ]
    )
    ```

3.  **`bic/ui/main.py`:**

    ```python
    # ... imports
    from .hello_ui import hello_menu

    main_menu = UIMenu(
        # ... other items
        UIMenuItem(name="Hello", path="hello", item=hello_menu),
    )
    ```

4.  **`templates/hello.html`:**

    ```html
    {% extends "base.html" %}
    {% block title %}Hello{% endblock %}
    {% block content %}
        <h1>{{ list_data }}</h1>
    {% endblock %}
    ```
