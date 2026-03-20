# Changelog

## Version 2026.03.20.1344

-   **Security:** Migrated `SECRET_KEY` from a hardcoded value to a secure, database-driven setting. A new key is now generated automatically on first startup.

## Version 2026.03.20.1336

-   **Bugfix:** Truncated passwords to 72 bytes before hashing to prevent a `ValueError` with bcrypt.

## Version 2026.03.20.1332

-   **Bugfix:** Fixed a `NameError` on startup caused by a missing `os` import in `bic/webapp.py`.

## Version 2026.03.20.1327

-  **INITIAL RELEASE**

-   **Advanced Authentication:** Implemented Passkey (WebAuthn), YubiKey, and Google Authenticator support for enhanced security.
-   **IPAM Enhancements:** Updated the IPAM allocator with block-alignment and gap-search strategies for more efficient IP address management.
-   **BGP and Blackhole Management:** Refined BGP export filters and blackhole community tagging for more precise route control.
-   **WireGuard Configuration:** Updated the WireGuard configuration generator with static server IPs and dynamic client IP assignments.
-   **Documentation:** Updated all project documentation to reflect the latest features and changes.
