# Changelog

All notable changes to this project will be documented in this file.

## [2026.03.20.0544] - 2026-03-20

### Added
- **Live Web-Based Monitoring:** Replaced the TUI with a new "Live View" page in the web app, featuring real-time, two-panel display of system statistics and console logs via WebSockets.
- **Configuration Viewing:** Added a "View Configs" page to the web UI, allowing for easy viewing of generated WireGuard, BIRD, and FRR configurations for each client.
- **Dynamic IP Assignment UI:** Overhauled the client creation and editing forms with a JavaScript-powered dynamic interface for adding and removing multiple IP or subnet assignments.

### Changed
- **IPAM Core Logic:** Corrected the core IP allocation logic to only assign usable IPs, never the network or broadcast address of a subnet.
- **BGP Configuration:** Refactored BGP configuration generation to be IP family-aware, only creating IPv4 or IPv6 sessions if the client has corresponding IP assignments.
- **WireGuard Configuration:** Implemented a major refactoring of WireGuard configuration generation to adhere to a strict set of new networking rules, correctly handling all IP family scenarios (IPv4-only, IPv6-only, dual-stack, BGP) for `DNS`, `Address`, and `AllowedIPs` fields.
- **Default WireGuard Endpoint:** The default WireGuard endpoint for client configurations now intelligently uses the server's public WAN IP, determined from the local interface, instead of a static placeholder or an external service.

### Fixed
- **BGP Email Notifications:** Corrected an `AttributeError` that occurred when editing a non-BGP client, ensuring BGP configs are only processed for "Transit" type clients.
- **UI Bugs:** Fixed several UI bugs on the "Edit Client" page, including an erroneous "None:" label and an empty "Pool" dropdown.
- **Commit Message Failures:** Resolved repeated commit failures by simplifying commit message content.


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
- Client provisioning form to display pool descriptions and implement proper Single IP vs Subnet logic: Single IP automatically uses /32 (IPv4) or /128 (IPv6), Subnet shows /29, /27 (IPv4) or /64, /56 (IPv6) options. Updated both web and TUI interfaces.
- Fixed client provisioning form action URL to correctly POST to the provision route instead of a non-existent action endpoint.
- Fixed TUI AttributeError by using get_binding() method instead of accessing non-existent bindings attribute.

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
