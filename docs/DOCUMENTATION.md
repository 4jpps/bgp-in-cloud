# User & Administrator Guide

This guide provides an overview of the BGP in Cloud IPAM application, covering key features and administrative tasks.

## 1. Introduction

The BGP in Cloud IPAM is a web-based platform for managing clients, IP addresses, and BGP configurations in a cloud environment.

## 2. Accessing the Application

The application is accessible via a web browser. Your administrator will provide you with the URL and login credentials.

## 3. Core Concepts

-   **Clients:** Entities that are allocated network resources.
-   **IP Pools:** Ranges of IPv4 or IPv6 addresses from which allocations are made.
-   **BGP Peers:** BGP routers that the system peers with.
-   **Advertised Prefixes:** Network prefixes that are announced via BGP.

## 4. User Features

-   **Dashboard:** View high-level statistics about the system.
-   **Client Management:** View and manage client details and resource allocations.
-   **Network Management:** View IP pools and allocations.
-   **BGP Management:** View BGP peer status and advertised routes.

## 5. Administrator Features

In addition to user features, administrators can:

-   **Manage Users:** Create, edit, and delete user accounts.
-   **System Settings:** Configure application settings, including branding and email notifications.
-   **Advanced Authentication:** Set up and manage Passkeys, YubiKeys, and Google Authenticator for users.
-   **Backup & Restore:** Create and restore backups of the application database.
-   **View Audit Logs:** Track all user actions within the system.

## 6. Advanced Authentication

Administrators can enhance security by enabling multi-factor authentication (MFA) for users.

### 6.1. Passkeys (WebAuthn)

-   **Setup:** Users can register a Passkey (e.g., Windows Hello, Apple Touch ID) in their profile.
-   **Login:** After entering their username, users can click "Login with Passkey" for a passwordless experience.

### 6.2. YubiKey

-   **Setup:** An administrator can associate a YubiKey with a user's account.
-   **Login:** After entering their username and password, users will be prompted to touch their YubiKey.

### 6.3. Google Authenticator

-   **Setup:** Users can set up Google Authenticator by scanning a QR code in their profile.
-   **Login:** After entering their username and password, users will be prompted for a 6-digit code from their authenticator app.
