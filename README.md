# BGP in the Cloud (BIC) IPAM

## Overview

BGP in the Cloud (BIC) is a comprehensive, self-hosted IP Address Management (IPAM) and network automation platform. It is designed for small-scale service providers, hobbyists, and labs who need to manage network resources and client configurations efficiently.

A key architectural feature is its **Unified UI Schema**. Both the Terminal User Interface (TUI) and the full-featured Web UI are dynamically generated from a single, declarative set of Python data classes. This ensures a consistent user experience across both interfaces and makes the system highly maintainable and easy to extend.

## Features

- **Dual Interfaces**: Full-featured, dynamically generated interfaces for both Web and Terminal (TUI).
- **Client Management**: A complete lifecycle management workflow for clients, including provisioning, updating, and de-provisioning.
- **Automated Provisioning**: A powerful, multi-step workflow for onboarding new clients that automatically:
    - Assigns IP addresses or subnets from configurable pools.
    - Assigns a private ASN for BGP clients.
    - Generates a complete WireGuard configuration for a secure tunnel.
    - Generates server-side BGP (BIRD) and WireGuard configurations.
    - Sends a comprehensive welcome email with all necessary client-side configuration files (`wireguard.conf`, `frr.conf`, `client_bird.conf`).
- **IP Pool Management**: Create, edit, delete, and manage IPv4 and IPv6 pools.
- **Pool Swapping**: Seamlessly migrate an entire IP pool and all its allocated addresses to a new CIDR block (e.g., when moving from private IP space to a new ARIN allocation). All client and server configurations are automatically updated.
- **Dynamic BGP Configuration**: The application automatically generates and manages your BIRD configuration files (`peers.conf`, `filter.conf`, etc.), including blackhole routes for your public prefixes.
- **System Configuration**: Easily configure system settings through the UI, including:
    - **Branding**: Set your own company name and email signature.
    - **SMTP**: Configure for sending email notifications.
    - **DNS**: Specify DNS servers for client WireGuard configurations.
    - **WireGuard Endpoint**: Set the public-facing endpoint for your server.

## Installation

1.  **Prerequisites**: A modern Linux server (e.g., Debian, Ubuntu) with `git`, `python3`, `pip`, and superuser privileges. Core system services like `wireguard`, `bird2`, and `iptables` must be installed for full functionality.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/4jpps/bgp-in-cloud.git
    cd bgp-in-cloud
    ```

3.  **Run the Installer**:
    The installer script will set up system dependencies, create a Python virtual environment, install required packages, and create the initial BIRD configuration.
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

## Configuration

After the first run, all system settings can be managed through the UI. Navigate to **System -> Settings** in either the Web UI or the TUI to configure SMTP, DNS, the WireGuard endpoint, and application branding.

## License

This is a proprietary commercial product.

**Copyright (c) 2026 Jeff Parrish PC Services. All Rights Reserved.**

For full license details, please see the `LICENSE` file included in this repository.
