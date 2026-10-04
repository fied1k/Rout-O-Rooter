# Changelog

All notable changes to this project are documented in this file.

## [v0.2.1] - 2026-10-04
### Added
- Multi-format file ingestion via `RouteOptimizer.ingest_file(path)`.
- Support for structured `.csv` files with column header detection (`lat`, `latitude`, `lon`, `lng`, etc.) and raw headerless fallback.
- Support for `.json` files structured as coordinate dictionaries or coordinate tuples/lists.
- Plain `.txt` file parsing and automated routing to `pytesseract` for image files (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`).
- Integrated unit test suite expansions for `.csv` and `.json` file ingestion validation.

### Changed
- Bumped project version to `v0.2.1`.

## [v0.2.0] - 2026-10-02
### Added
- Integrated OSRM Trip API for free route sequencing.
- Added URL builder for native Google Maps multi-stop directions.
- Integrated QR code generation for mobile handoff (`route_qr.png`).
- Added IMAP email listener (`email_listener.py`).
- Added built-in self-testing test harness.

## [v0.1.2-beta] - Archive
- Added `pytesseract` coordinate extraction prototype.

## [v0.1.1-alpha] - Archive
- Coordinate regex parsing and data structure definitions.

## [v0.1.0-alpha] - Archive
- Initial project layout and structure.
