# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Calendar Versioning](https://calver.org/) using the `YYYY.MM.DD.HHmm` format.

---

## [2026.03.19.0646] - 2026-03-19

### Fixed
- **Web App Crash:** Corrected a `sqlite3.ProgrammingError` and `jinja2.exceptions.TemplateNotFound` error that prevented the web application from starting. The database is now initialized correctly, and the required template files have been created.

## [2026.03.19.0642] - 2026-03-19

### Fixed
- **TUI Crash:** Corrected a `VisualError` in the `SystemDashboardScreen` by refactoring it to use stateful widgets, which is a more robust `textual` pattern.
- **Web App Crash:** Corrected a `sqlite3.ProgrammingError` that occurred due to improper multi-threaded database access.

## [2026.03.19.0638] - 2026-03-19

### Fixed
- **Web App Crash:** Corrected a `sqlite3.ProgrammingError` that occurred due to improper multi-threaded database access.
- **TUI Crash:** Corrected a `MountError` in the `SystemDashboardScreen` by properly wrapping a `rich` element in a `textual` widget.

## [2026.03.19.0635] - 2026-03-19

### Fixed
- **TUI Crash:** Corrected a crash in the `SystemDashboardScreen` by refactoring the layout to be more compliant with the `textual` framework.

## [2026.03.19.0633] - 2026-03-19

### Fixed
- **Web App Crash:** Corrected a `RuntimeError` that prevented the web application from starting by creating the required `static` directory.

## [2026.03.19.0630] - 2026-03-19

### Changed
- **System Dashboard:** The legacy "System Dashboard" has been completely refactored into a modern, live-updating `textual` screen, eliminating the full-screen takeover and providing a much smoother experience.
- **UX:** The new System Dashboard now uses a "Press any key to return" prompt for a more intuitive workflow.

### Fixed
- **Critical TUI Crash:** Corrected a catastrophic layout regression that caused the main menu and statistics panel to disappear.
- **Critical TUI Crash:** Corrected a `NameError` for `system_management` that prevented the application from launching.
- **Robust Statistics:** The disk usage statistic is now gathered using the more reliable `psutil` library to prevent `N/A` errors.
- **TUI Footer:** Implemented a more robust layout for the footer to ensure it is always visible.

## [2026.03.19.0627] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `NameError` for `system_management` that prevented the application from launching. This was a regression from a previous fix.

## [2026.03.19.0624] - 2026-03-19

### Changed
- **System Dashboard:** The legacy "System Dashboard" has been completely refactored into a modern, live-updating `textual` screen, eliminating the full-screen takeover and providing a much smoother experience.
- **UX:** The new System Dashboard now uses a "Press any key to return" prompt for a more intuitive workflow.

### Fixed
- **Critical TUI Crash:** Corrected a `NameError` that prevented the application from launching.
- **Robust Statistics:** The disk usage statistic is now gathered using the more reliable `psutil` library to prevent `N/A` errors.
- **TUI Footer:** Implemented a more robust layout for the footer to ensure it is always visible.

## [2026.03.19.0618] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `NameError` that prevented the application from launching, caused by a missing variable in the main TUI screen.

## [2026.03.19.0616] - 2026-03-19

### Fixed
- **Robust Statistics:** Refactored the entire `statistics_management` module to prevent a single metric failure from cascading and causing other stats to fail.
- **Disk Stat:** The disk usage statistic is now correctly and robustly gathered on Debian systems.
- **Legacy Crash:** Fixed a recurring `KeyError: 'wan_interface'` crash on the legacy "System Dashboard" screen.
- **TUI Footer:** Corrected the layout order of footer widgets to ensure the copyright and version information is always visible.

### Changed
- **UX:** Removed the jarring "Press Enter to return..." prompt after successfully running a legacy module.

## [2026.03.19.0611] - 2026-03-19

### Fixed
- **Legacy Crash:** Fixed a `KeyError: 'wan_interface'` crash on the legacy "System Dashboard" screen by safely handling the data.
- **TUI Footer:** Corrected a layout issue that was causing the copyright and version footer to be hidden.

## [2026.03.19.0607] - 2026-03-19

### Fixed
- **Disk Stat:** The disk usage statistic is now correctly gathered on Debian systems by using a more portable method.
- **Legacy Crash:** Fixed a `KeyError: 'ipam'` crash on the legacy "System Dashboard" screen.

### Changed
- **Footer:** The TUI footer has been cleaned up and now displays the copyright information as requested.

## [2026.03.19.0557] - 2026-03-19

### Changed
- **Branding:** The application title is now correctly set to "BGP in the Cloud", and the version number is displayed in the footer.

### Fixed
- **Critical TUI Crash:** Corrected a recurring `AttributeError` by using the correct `find_one` database method.

## [2026.03.19.0550] - 2026-03-19

### Changed
- The `bic-start.sh` script now automatically checks for code updates via `git pull` before launching.

### Fixed
- **Critical TUI Crash:** Corrected an `AttributeError` that occurred when opening the "Edit Pool" screen.

## [2026.03.19.0544] - 2026-03-19

### Changed
- **TUI Layout:** The main TUI layout has been adjusted to place the statistics panel on the far right, creating a more balanced and traditional feel.
- The TUI header now correctly displays the application name, version, and the current time.

## [2026.03.19.0541] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected an `AttributeError` that occurred when opening the "Edit Pool" screen by using the correct `find_by_id` database method.

## [2026.03.19.0539] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `RuntimeError` that occurred when trying to open the "Edit Pool" screen. The feature now correctly uses a modal screen within the main application event loop.

## [2026.03.19.0536] - 2026-03-19

### Changed
- **Consistent UX:** The "Edit Pool Description" feature has been rewritten as a dedicated Textual application, providing a modern, clickable menu that is consistent with the main TUI.

## [2026.03.19.0533] - 2026-03-19

### Added
- **Edit IP Pool:** You can now edit the description of an existing IP pool.

### Changed
- When creating a new IP pool, if no description is provided, a sensible default will now be automatically generated (e.g., "AMPRNet IPv6 Pool").

## [2026.03.19.0526] - 2026-03-19

### Added
- **Composite Keys for IP Pools:** IPv4 and IPv6 pools can now share the same name. Uniqueness is now enforced on the combination of pool name and address family.

### Changed
- The database schema for `ip_pools` has been updated to version 2, including a safe data migration path.

## [2026.03.19.0519] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `BadIdentifier` error by sanitizing menu labels to create valid widget IDs for Textual.

## [2026.03.19.0517] - 2026-03-19

### Fixed
- **Definitive TUI Overhaul:** The TUI has been completely rewritten with a stable and correct Textual implementation, resolving all previous crashes and usability issues.
- **Critical Bug:** Corrected a `SyntaxError` in `network_management.py`.

## [2026.03.19.0459] - 2026-03-19

### Added
- **Major TUI Overhaul:** The TUI has been completely rewritten using the Textual framework to provide a modern, GUI-like experience.
- **Native Mouse Support:** The TUI menu is now composed of distinct buttons that are fully clickable with a mouse.
- **Live Statistics Panel:** A live-updating statistics panel is now a permanent fixture on the right side of the TUI.

### Changed
- The TUI now uses a CSS file (`main_menu.css`) for styling and layout.

## [2026.03.19.0512] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `VisualError` by re-architecting the statistics widget to be a proper `DataTable` as required by the Textual framework.

## [2026.03.19.0510] - 2026-03-19

### Fixed
- **Critical TUI Crash:** Corrected a `VisualError` that occurred when updating the statistics panel by implementing the correct widget mounting procedure in Textual.

## [2026.03.19.0506] - 2026-03-19

### Changed
- The `bic-start.sh` script now automatically checks for and installs missing Python dependencies, making the application more robust after code updates.

## [2026.03.19.0501] - 2026-03-19

### Fixed
- **Critical Bug:** Corrected a `SyntaxError` in `network_management.py` that caused the application to crash when accessing IP pool functions.
- **TUI Overhaul:** The TUI has been completely rewritten using the Textual framework to provide a stable, modern, GUI-like experience with native mouse support for all menu buttons.

## [2026.03.19.0450] - 2026-03-19

### Fixed
- **Critical Bug:** Corrected a `SyntaxError` in `network_management.py` that caused the application to crash when accessing IP pool functions.
- **TUI Layout:** The input prompt is now correctly located within the main working area of the TUI, creating a more cohesive layout.

## [2026.03.19.0446] - 2026-03-19

### Fixed
- **Unified Statistics:** Refactored the `statistics_management` module to be the single, robust source of all system metrics. The main TUI dashboard now correctly displays all system and network statistics.
- **Case-Insensitive Menu:** The TUI menu now correctly accepts typed commands in a case-insensitive manner.

## [2026.03.19.0434] - 2026-03-19

### Added
- **New TUI Layout:** The TUI has been completely rewritten with a new layout, placing a live statistics panel on the right and the main working area on the left.


### Changed
- **Robust Statistics:** The TUI statistics panel is now more resilient and will display "N/A" instead of crashing if a metric is unavailable.

### Fixed
- Resolved a bug where menu items in the TUI were unselectable.
- Corrected a text formatting issue that was causing the time display to be garbled.

## [Unreleased]
