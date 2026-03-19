# BIC IPAM Technical Documentation

This document provides a detailed breakdown of each file and directory in the project, explaining its specific role and purpose.

---

## Root Directory

- **`bic-installer.sh`**
  - **Purpose**: The primary installation script for setting up a new Debian 12 server. It installs system dependencies (BIRD, WireGuard, Python), sets up the Python virtual environment, and performs the initial, one-time patching of `/etc/bird/bird.conf` to make it modular.

- **`bic-start.sh`**
  - **Purpose**: The main startup script for the application. It activates the Python virtual environment and can launch either the TUI or the Web App.
  - **Usage**:
    - `./bic-start.sh --tui`: Launches the Text-based UI (default).
    - `./bic-start.sh --web`: Launches the FastAPI web server.

- **`requirements.txt`**
  - **Purpose**: Lists all Python dependencies required by the project (e.g., `rich`, `fastapi`, `psutil`). The installer script uses this file with `pip` to set up the environment.

- **`ipam.db`**
  - **Purpose**: The SQLite database file. This is the single source of truth for the entire application, storing all data related to clients, IP pools, allocations, and settings. It is created automatically on the first run.

- **`README.md`**
  - **Purpose**: The main project entry point, providing a high-level overview, feature list, and getting-started guide.

- **`DOCUMENTATION.md`** (This file)
  - **Purpose**: In-depth technical reference for developers.

---

## `bic/` - Main Application Package

- **`core.py`**
  - **Purpose**: The most critical file in the backend. The `BIC_DB` class within manages the connection to the `ipam.db` database, handles schema creation and migration, and provides a standard set of methods (`insert`, `find_one`, `update`, etc.) for all other modules to interact with the database.

- **`webapp.py`**
  - **Purpose**: The entry point for the FastAPI web server. It is architected to be fully definition-driven. It contains generic, dynamic endpoints like `/action/{action_path:path}` that use the `menu_structure.py` file to find the appropriate `web_handler` and `web_form` definitions. This allows it to process actions and render forms without having hardcoded logic for each specific action, ensuring maximum consistency with the TUI and easy extensibility.

---

## `bic/tui/` - Text-based UI

- **`main_menu.py`**
  - **Purpose**: The main application entry point for the TUI. It contains the primary `while` loop that renders menus, processes user input, and calls the appropriate action modules. It also orchestrates the initial system synchronization on startup.

---

## `bic/menus/` - TUI and Web UI Definitions

- **`menu_structure.py`**
  - **Purpose**: A centralized Python dictionary that defines the entire hierarchy and content of both the TUI and Web UI. This structure dictates the titles, descriptions, and targets of all menu items. It contains the following keys for each action:
    - `handler`: The path to the TUI script to execute.
    - `web_handler`: The full Python path to the backend module function to be called by the web UI (e.g., `bic.modules.client_management.add_client`).
    - `web_form`: A list of dictionaries that declaratively defines an HTML form for the action, including field names, labels, and types. This is used by `webapp.py` to dynamically generate all user input forms.

- **`clients/`**, **`network/`**, **`system/`**
  - **Purpose**: These directories contain the TUI-specific action files. The logic within these files is minimal, primarily concerned with gathering input from the user via `rich.prompt` and then calling the appropriate centralized function in a backend module.

---

## `bic/modules/` - Core Backend Logic

This directory contains the heart of the automation engine. These modules contain the shared business logic used by both the TUI and the Web App.

- **`system_management.py`**: Orchestrates host-level configuration on startup.
- **`client_management.py`**: Contains the centralized logic for provisioning and deprovisioning clients.
- **`network_management.py`**: Provides the core IPAM functions for managing pools and addresses.
- **`wireguard_management.py`**: Manages all aspects of WireGuard.
- **`bird_management.py`**: Manages BIRD configuration files for your network's prefixes.
- **`bgp_management.py`**: Manages BIRD configurations for client BGP sessions.
- **`firewall_management.py`**: Manages server security rules using `iptables`.
- **`email_notifications.py`**: Handles sending emails.
- **`statistics_management.py`**: Gathers and processes system and network statistics for the dashboards.

---

## `bic/templates/` - Web UI Templates

- **`base.html`**: The main Jinja2 template. It provides the overall page structure, including the header, navigation menu, and footer, that all other pages extend.
- **`dashboard.html`**: The template for the main dashboard, which displays the statistics widgets.
- **`clients.html`**, **`pools.html`**: Templates that render tables of clients and network pools, respectively.
- **`client_detail.html`**: A detailed view for managing a single client, including their assigned resources and management actions.
- **`generic_action.html`**: A powerful, reusable template that dynamically generates an HTML form based on the `web_form` metadata provided by `webapp.py`.

---

## `bic/static/` - Static Web Assets

- **`style.css`**: Contains custom CSS rules to provide basic styling for the web interface.
