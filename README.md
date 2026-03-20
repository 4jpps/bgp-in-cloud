# BGP in Cloud IPAM

This project is a comprehensive IP Address Management (IPAM) and BGP orchestration platform designed for cloud environments. It provides a web-based interface for managing clients, network resources, and BGP sessions.

## Features

-   **Client Management:** Create, provision, and manage clients and their associated network resources.
-   **IPAM:** Allocate IPv4 and IPv6 addresses and subnets from custom-defined pools.
-   **BGP Orchestration:** Manage BGP peers, advertised prefixes, and blackholing.
-   **WireGuard Integration:** Automatically generate WireGuard configurations for clients.
-   **Advanced Authentication:** Secure your instance with Passkeys (WebAuthn), YubiKeys, and Google Authenticator.
-   **System Administration:** Manage users, view audit logs, and configure system settings.
-   **Extensible UI:** The application features a dynamic and extensible UI framework.

## Getting Started

This project includes an installer script to automate the setup process.

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/4jpps/bgp-in-cloud.git
    cd bgp-in-cloud
    ```

2.  **Run the Installer:**

    On Linux or macOS:
    ```bash
    ./bic-installer.sh
    ```

    On Windows (in PowerShell):
    ```powershell
    .\bic-installer.ps1
    ```

    This script will create a Python virtual environment, install all dependencies, and initialize the database. If you prefer to run the steps manually, please see the [Developer Guide](docs/DEVELOPER_GUIDE.md).

3.  **Run the Application:**

    After the installer completes, activate the virtual environment and start the application:
    ```bash
    source venv/bin/activate
    uvicorn bic.webapp:app --reload
    ```

## Documentation

-   [User & Administrator Guide](docs/DOCUMENTATION.md)
-   [Developer Guide](docs/DEVELOPER_GUIDE.md)
-   [Module Development](docs/MODULE_DEVELOPMENT.md)
