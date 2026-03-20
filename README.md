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

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/4jpps/bgp-in-cloud.git
    cd bgp-in-cloud
    ```

2.  **Installation:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize the Database:**

    ```bash
    python init_db.py
    ```

3.  **Configuration:**

    -   Copy `.env.example` to `.env` and customize the settings.
    -   Set `YUBICO_CLIENT_ID` and `YUBICO_SECRET_KEY` in your environment if you plan to use the YubiKey integration.

3.  **Running the Application:**

    ```bash
    uvicorn bic.webapp:app --reload
    ```

## Documentation

-   [User & Administrator Guide](docs/DOCUMENTATION.md)
-   [Developer Guide](docs/DEVELOPER_GUIDE.md)
-   [Module Development](docs/MODULE_DEVELOPMENT.md)
