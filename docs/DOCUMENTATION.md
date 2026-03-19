# BIC IPAM Technical Documentation

This document provides a detailed breakdown of each file and directory in the project, explaining its specific role and purpose in the new Unified UI Schema architecture.

---

## Root Directory

- **`bic-installer.sh`**
  - **Purpose**: The primary installation script for setting up a new Debian 12 server. It installs system dependencies (BIRD, WireGuard, Python), sets up the Python virtual environment, and creates the initial modular `/etc/bird/bird.conf`.

- **`bic-start.sh`**
  - **Purpose**: The main startup script for the application. It activates the Python virtual environment and can launch either the TUI or the Web App.



- **`README.md`**
  - **Purpose**: The main project entry point, providing a high-level overview and feature list.

- **`CHANGELOG.md`**
  - **Purpose**: A curated list of notable changes for each version release.

---

## `bic/` - Main Application Package

- **`core.py`**
  - **Purpose**: The most critical file in the backend. The `BIC_DB` class manages the connection to the `ipam.db` database, handles schema creation and migrations, and provides a standard set of methods (`insert`, `find_one`, `update`, etc.) for all other modules to interact with the database.

- **`webapp.py`**
  - **Purpose**: The entry point for the FastAPI web server. It acts as a generic rendering engine for the UI Schema. It uses dynamic routes to interpret the UI schema and render the correct view using a minimal set of generic templates. It contains almost no hardcoded logic for specific pages.

- **`__main__.py`**
  - **Purpose**: The main entry point when running the application as a module. It parses command-line arguments (`--tui` or `--web`) and launches the appropriate interface.

- **`__version__.py`**
  - **Purpose**: Stores the current version string for the application.

---

## `bic/ui/` - The Unified UI Schema

This directory is the heart of the new architecture. It declaratively defines the entire structure, content, and behavior of both the TUI and the WebApp.

- **`schema.py`**
  - **Purpose**: Defines the core Python `dataclasses` (`UIMenu`, `UIMenuItem`, `UIView`, `UIAction`, `FormField`) that serve as the building blocks for the entire UI.

- **`__init__.py`**
  - **Purpose**: Aggregates all the individual menu definitions from the other files in this directory into a single `main_menu` object that both the WebApp and TUI consume.

- **`clients.py`**, **`network.py`**, **`system.py`**, etc.
  - **Purpose**: These are the modular UI definition files. Each file defines a specific section of the UI (e.g., Client Management) by creating instances of the `UIMenu`, `UIView`, and `UIAction` classes and linking them to the appropriate handler functions in the `bic/modules/` directory.

---

## `bic/tui/` - Text-based UI

- **`main_menu.py`**
  - **Purpose**: The main application class for the Textual TUI. It consumes the `main_menu` object from the UI schema and dynamically builds the menu interface.

- **`generic_screens.py`**
  - **Purpose**: Contains the powerful, reusable screens (`GenericListScreen`, `GenericFormScreen`) that render the `UIView` and `UIAction` objects from the schema. These screens are responsible for displaying data tables, handling row selection, and generating forms dynamically.

- **`provision_client_screen.py`**
  - **Purpose**: A special, dedicated screen for the complex, multi-step client provisioning workflow, which is too advanced for the generic form screen.

---

## `bic/modules/` - Core Backend Logic

This directory contains the shared business logic used by both the TUI and the Web App. The functions here are called by the handlers defined in the `bic/ui/` schema.

- **`system_management.py`**: Manages the loading and saving of system-wide settings.
- **`client_management.py`**: Contains the centralized logic for provisioning and deprovisioning clients.
- **`network_management.py`**: Provides the core IPAM functions for managing pools, addresses, and BGP filter/prefix files.
- **`wireguard_management.py`**: Manages all aspects of WireGuard.
- **`bgp_management.py`**: Manages BIRD configurations for client BGP sessions.
- **`firewall_management.py`**: Manages server security rules using `iptables`.
- **`email_notifications.py`**: Handles sending emails.
- **`statistics_management.py`**: Gathers and processes system and network statistics.

---

## `bic/templates/` - Web UI Templates

- **`base.html`**: The main Jinja2 template. It provides the overall page structure and navigation.
- **`dashboard.html`**: The template for the main dashboard.
- **`generic_list.html`**: A powerful, reusable template that renders a table of items based on a `UIView` object.
- **`generic_form.html`**: A reusable template that dynamically generates an HTML form based on a `UIAction` object.
- **`provision_client.html`**: A special, dedicated template for the multi-step client provisioning workflow.
- **`view_configs.html`**: A template for displaying the stored configurations for a client.

---

## `bic/static/` - Static Web Assets

- **`style.css`**: Contains custom CSS rules for the web interface.
