# Changelog

All notable changes to this project will be documented in this file.

## [2026.03.19.0919] - 2026-03-19

### Added
- **Initial Major Release**
- Unified UI architecture with dynamically generated Web and TUI interfaces from a single schema.
- Full client lifecycle management (provision, update, de-provision).
- Automated IP, subnet, and ASN assignment.
- Automated generation of WireGuard, BIRD, and FRR configurations.
- Automated welcome emails with all necessary client-side configs.
- IP Pool management with support for migrating pools to new CIDRs ("Swap Pool").
- Dynamic generation of server-side BIRD and WireGuard configurations.
- System settings management for SMTP, DNS, branding, and endpoints.
- NAT rules for private IP space.
- Blackhole routing for public prefixes.
- Hierarchical IP allocation logic for pools.

### Fixed
- WebUI navigation for system statistics by linking directly to special route instead of generic page route.
- TUI navigation by removing duplicate button press handler and fixing stats display updates.
- Client provisioning redirect in generic page route to handle direct URL access.
- Client provisioning form to display pool descriptions and implement proper Single IP vs Subnet logic: Single IP automatically uses /32 (IPv4) or /128 (IPv6), Subnet shows /29, /27 (IPv4) or /64, /56 (IPv6) options.

### Fixed
- TUI widget ID generation to use valid identifiers, preventing startup crashes.
- TUI menu navigation by adding button press handlers for menu items.
- Web UI template error by creating missing `generic_menu.html` template.
- TUI statistics display KeyError by correcting dictionary key references.
- Client provisioning navigation path mismatch between TUI and Web UI.
- System statistics page by adding proper UIView definition.
- Form select field rendering in Web UI with database-sourced options.
- Missing UIView import causing NameError on TUI startup.
- Missing __main__.py preventing TUI from running and enabling navigation.
- TUI button focus to enable keyboard navigation.
- BGP sessions list error handling for missing database table.
- Browser translation prompts by adding notranslate meta tag.
- Client provisioning 404 error by fixing menu link to use special route.
- Direct access 404 for client provisioning by adding redirect in page route.
