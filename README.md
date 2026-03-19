# BGP in the Cloud (BIC) IPAM

**Version:** 1.0.0

## Overview

BGP in the Cloud (BIC) is a self-hosted IP Address Management (IPAM) and network automation platform designed for small-scale service providers, hobbyists, and labs. It provides both a Text-based UI (TUI) and a full-featured Web UI to automate the complex and repetitive tasks of provisioning network services for customers, including IP assignments, WireGuard VPN tunnels, BGP sessions, and firewall management.

The entire application is designed to be definition-driven, meaning both the TUI and Web UI are dynamically generated from a single, centralized menu structure, ensuring a consistent user experience and easy extensibility.

## Installation

1.  **Prerequisites**: Ensure you have a modern Linux environment with `git`, `python3`, `pip`, and `powershell` installed. Core system dependencies like `wireguard`, `bird2`, and `iptables` are required for full functionality.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/4jpps/bgp-in-cloud.git
    cd bgp-in-cloud
    ```

3.  **Run the Installer**:
    The installer script will set up a Python virtual environment, install dependencies, and prepare the system configuration.
    ```bash
    sudo ./bic-installer.sh
    ```

## Usage

The application can be started using the `bic-start.sh` script, which accepts a command-line argument to launch either the Text User Interface (TUI) or the Web UI.

-   **To launch the TUI:**
    ```bash
    ./bic-start.sh --tui
    ```

-   **To launch the Web UI:**
    ```bash
    ./bic-start.sh --web
    ```
    The web interface will be available at `http://127.0.0.1:8000` by default.

## Updating

To update your instance of BGP in the Cloud to the latest version, follow these steps:

1.  **Navigate to the project directory**:
    ```bash
    cd /path/to/bgp-in-cloud
    ```

2.  **Pull the latest changes** from the Git repository:
    ```bash
    git pull origin master
    ```

3.  **Re-run the installer** to update dependencies and apply any new system configurations:
    ```bash
    sudo ./bic-installer.sh
    ```

## Project Architecture

The architecture is designed to be modular and definition-driven, ensuring that both the TUI and Web UI are powered by the same consistent backend logic.

- **`bic-start.sh`**: Dual-mode startup script. Use `--tui` for the text interface and `--web` for the web interface.
- **`bic/__version__.py`**: Declares the application's version number.
- **`bic/core.py`**: Contains the core `BIC_DB` class for all database interactions.
- **`bic/modules/`**: The heart of the backend. Each module contains the centralized business logic for a specific domain (e.g., `client_management.py`, `wireguard_management.py`). These modules are called by both the TUI and the Web UI.
- **`bic/menus/menu_structure.py`**: The single source of truth for the application's user interface. This dictionary defines the menu hierarchy and actions for both UIs.
- **`bic/tui/`**: Contains the TUI-specific presentation logic.
- **`bic/webapp.py`**: A fully dynamic FastAPI application that serves the Web UI.
- **`bic/templates/`**: Jinja2 templates for the web UI. The main navigation and all action forms are dynamically generated from the `menu_structure.py` file.

## License

This is a proprietary commercial product.

**Copyright (c) 2026 Jeff Parrish PC Services. All Rights Reserved.**

For full license details, please see the `LICENSE` file included in this repository.

### Third-Party Modules

This application supports a growing ecosystem of third-party modules. For information on developing, distributing, and using modules, please see the `MODULE_DEVELOPMENT.md` file.
