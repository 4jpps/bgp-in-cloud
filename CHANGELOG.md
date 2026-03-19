# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Calendar Versioning](https://calver.org/) using the `YYYY.MM.DD.HHmm` format.

---

## [2026.03.19.0446] - 2026-03-19

### Fixed
- **Unified Statistics:** Refactored the `statistics_management` module to be the single, robust source of all system metrics. The main TUI dashboard now correctly displays all system and network statistics.
- **Case-Insensitive Menu:** The TUI menu now correctly accepts typed commands in a case-insensitive manner.

## [2026.03.19.0434] - 2026-03-19

### Added
- **New TUI Layout:** The TUI has been completely rewritten with a new layout, placing a live statistics panel on the right and the main working area on the left.
- **Mouse Support:** Foundational support for mouse clickability has been added to the TUI menu items.

### Changed
- **Robust Statistics:** The TUI statistics panel is now more resilient and will display "N/A" instead of crashing if a metric is unavailable.

### Fixed
- Resolved a bug where menu items in the TUI were unselectable.
- Corrected a text formatting issue that was causing the time display to be garbled.

## [Unreleased]

