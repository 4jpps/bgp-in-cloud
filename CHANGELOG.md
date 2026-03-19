# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-18

### Added
- Implemented a new dashboard-style TUI with a two-column layout, featuring a persistent menu sidebar and a live-updating statistics panel.

## [1.0.3] - 2026-03-18

### Fixed
- Fixed a `KeyError: 'title'` crash in the TUI by correctly tracking and displaying the menu navigation path (breadcrumb).

## [1.0.2] - 2026-03-18

### Fixed
- Resolved an `AttributeError` during startup by removing a call to a non-existent function (`synchronize_security_filters`).

## [1.0.1] - 2026-03-18

### Fixed
- Corrected a `sqlite3.OperationalError` that occurred on first run by adding the missing `ip_pools` table definition to the core database schema.
- Resolved a `ModuleNotFoundError` in the `bic-start.sh` script by executing the TUI as a module (`python -m`) to ensure the project path is correctly recognized.
- Prevented a `ufw: command not found` error in the installer by adding a check to verify if `ufw` exists before attempting to use it.

## [1.0.0] - 2026-03-18

### Added
- Initial release of the BGP in the Cloud (BIC) IPAM system.
- Core features include TUI and Web UI for client and network management.
- Definition-driven architecture using `menu_structure.py`.
- Comprehensive documentation including `README.md`, `LICENSE`, `SECURITY.md`, and `DEVELOPER_GUIDE.md`.
