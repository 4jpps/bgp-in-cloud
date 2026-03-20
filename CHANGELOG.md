# Changelog

## Version 2026.03.20.1538

-   **Bugfix:** Resolved a critical `AttributeError` by adding a missing template definition to the `provision_client` UI action.

## Version 2026.03.20.1536

-   **Bugfix:** Resolved a critical `AttributeError` by adding a missing template definition to the `edit_settings` UI action.

## Version 2026.03.20.1534

-   **Bugfix:** Performed a full template audit and created all missing templates to resolve `TemplateNotFound` errors.

## Version 2026.03.20.1515

-   **UAT:** Completed a full user acceptance test, validating all navigation, page rendering, and core functionality.
-   **UI/UX:** Implemented a comprehensive layout overhaul, including a top navigation bar with dropdowns and a functional toast notification system.

## Version 2026.03.20.1511

-   **UI/UX:** Overhauled the main layout to use a horizontal navigation bar with dropdown menus.
-   **UI/UX:** Corrected the update notification to ensure it always renders as a proper toast.

## Version 2026.03.20.1507

-   **Bugfix:** Fixed the "Edit User" page by correctly loading and pre-selecting the user's role in the dropdown.

## Version 2026.03.20.1501

-   **Bugfix:** Resolved a second `NameError` by refactoring `get_current_user_optional` to use database-driven JWT settings.

## Version 2026.03.20.1459

-   **UI/UX:** Redesigned the login form with a modern, centered card layout.
-   **UI/UX:** Corrected the update notification to function as a proper toast.

## Version 2026.03.20.1457

-   **Bugfix:** Resolved a `NameError` after login by refactoring the `get_current_user` function to use database-driven JWT settings.
-   **Bugfix:** Corrected the stylesheet path in the base template to fix all UI styling issues.

## Version 2026.03.20.1448

-   **Bugfix:** Gracefully handle 404 errors when checking for updates from GitHub.
-   **Bugfix:** Resolved a `KeyError` during login by ensuring the full user object is fetched.

## Version 2026.03.20.1444

-   **Bugfix:** Added the missing `python-multipart` dependency to resolve form parsing errors.
-   **Bugfix:** Corrected the static file path to fix broken UI styling.

## Version 2026.03.20.1439

-   **Bugfix:** Corrected the UI routing configuration to resolve a `404 Not Found` error on the login page.

## Version 2026.03.20.1437

-   **Bugfix:** Added the missing `Jinja2` dependency to `requirements.txt` to resolve a startup `AssertionError`.

## Version 2026.03.20.1434

-   **Bugfix:** Replaced `passlib` with direct `bcrypt` calls to definitively resolve startup errors related to password hashing.

## Version 2026.03.20.1431

-   **Refactor:** Replaced `passlib` with direct `bcrypt` calls to resolve dependency conflicts and simplify the password hashing implementation.

## Version 2026.03.20.1427

-   **Bugfix:** Pinned `bcrypt` version to `>3.2.0` to resolve a critical version incompatibility with `passlib` that was causing startup errors.

## Version 2026.03.20.1424

-   **Installer:** Added a `bic-installer.sh` script to automate the entire setup process, from virtual environment creation to database initialization.

## Version 2026.03.20.1418

-   **Bugfix:** Added missing `passlib` and `zxcvbn` dependencies to `requirements.txt` to prevent `ModuleNotFoundError` on startup.

## Version 2026.03.20.1416

-   **Docs:** Added `git clone` command to the `README.md` for clarity.

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
