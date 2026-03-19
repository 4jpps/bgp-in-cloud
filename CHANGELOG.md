# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Calendar Versioning](https://calver.org/) using the `YYYY.MM.DD.HHmm` format.

---

## [2026.03.19.0459] - 2026-03-19

### Added
- **Major TUI Overhaul:** The TUI has been completely rewritten using the Textual framework to provide a modern, GUI-like experience.
- **Native Mouse Support:** The TUI menu is now composed of distinct buttons that are fully clickable with a mouse.
- **Live Statistics Panel:** A live-updating statistics panel is now a permanent fixture on the right side of the TUI.

### Changed
- The TUI now uses a CSS file (`main_menu.css`) for styling and layout.

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

