# Changelog

## Version 2026.03.20.1413

-   **Architecture:** Decoupled database initialization from application startup to resolve critical race conditions and `ValueError` on first run. A new `init_db.py` script now handles initial setup.

## Version 2026.03.20.1404

-   **Bugfix:** Corrected the password hashing function to properly handle byte truncation and prevent a `ValueError` during `passlib` initialization.

## Version 2026.03.20.1400

-   **Bugfix:** Completed a comprehensive audit and refactoring of UI handlers to resolve all module-related `AttributeError` issues at startup. Consolidated audit log and backup functions into the `system_management` module.

## Version 2026.03.20.1353

-   **Bugfix:** Restored the `get_all_settings` function, fixing a startup error caused by a missing UI loader function.

## Version 2026.03.20.1349

-   **Bugfix:** Restored the `save_all_settings` function, which was causing a startup error due to a missing attribute in the system management module.

## Version 2026.03.20.1347

-   **Bugfix:** Removed an unused `SECRET_KEY` import in `bic/webapp.py` that was causing a startup error.

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
