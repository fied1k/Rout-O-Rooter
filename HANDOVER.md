# Project Handover Document: Rout-o-Rooter

**Repository:** `https://github.com/fied1k/rout-o-rooter`  
**Current Release:** `v0.2.1`  
**Architecture Model:** Zero-Cost Open Source Route Optimizer  
**Handover Date:** October 2026  

---

## 1. Executive Summary & Objective

`rout-o-rooter` is a zero-cost ($0 budget), automated pipeline designed to ingest geographic coordinates across untraditional and multi-modal channels (plain text, IMAP email bodies, image OCR, `.csv`, `.json`, and raw `.txt` files), solve the Traveling Salesperson Problem (TSP) using public routing engines, and generate actionable outputs: universal multi-stop Google Maps navigation links and mobile-ready QR codes.

---

## 2. Architecture & Ingestion Flow

```text
[ Data Ingestion ]                  [ Core Engine: route_optimizer.py ]           [ Delivery Outputs ]
┌─────────────────────────┐        ┌────────────────────────────────────┐        ┌─────────────────────────┐
│ • File (.csv, .json,    │        │ 1. Coordinate Ingestion & Parsing  │        │ • Clickable Google Maps │
│   .txt, image formats)  ├───────►│    - Regex / JSON / CSV column map │───────►│   Multi-stop URL        │
│ • IMAP Email Poller     │        │ 2. TSP Optimization (OSRM Trip API)│        │ • Scannable QR Code PNG │
│ • Raw Text Strings      │        │ 3. Built-in Self-Testing (unittest)│        │ • Terminal / Log Output │
└─────────────────────────┘        └────────────────────────────────────┘        └─────────────────────────┘
```

### Component Inventory

1. **`route_optimizer.py` (Core Engine - `v0.2.1`)**
   * **`ingest_file(path)`**: Single entry point handling `.csv` (header-aware & raw fallback), `.json` (tuples or key-value dicts), plain `.txt`, and images (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`).
   * **`ingest_image(path)`**: Pytesseract OCR pipeline reading text from visual files.
   * **`parse_coordinates(text)`**: High-tolerance regex extractor extracting `(lat, lon)` pairs.
   * **`optimize_route(coords, start_coord=None, end_coord=None, roundtrip=False)`**: Zero-cost TSP solver communicating with Open Source Routing Machine (`http://router.project-osrm.org/trip/v1/driving/`), supporting optional fixed origin, fixed destination, and roundtrips.
   * **`generate_google_maps_url(coords)`**: Constructs standard multi-stop navigation URLs with origin, destination, and intermediate waypoints.
   * **`generate_apple_maps_url(coords)`**: Constructs native Apple Maps multi-stop navigation URLs using the unified `/directions` multi-waypoint scheme.
   * **`generate_segmented_urls(coords, max_stops=10)`**: Splits long routes into chained navigation parts (Part 1, Part 2, etc.) to comply with Google & Apple Maps limits.
   * **`generate_qr(url, output_path)`**: Builds local PNG QR code files for handoff to mobile devices.
   * **`TestRouteOptimizer`**: Self-testing harness covering regex extraction, CSV ingestion, JSON parsing, and routing URL generation.

2. **`email_listener.py` (Automated Background Ingestion)**
   * Headless IMAP consumer using Python standard libraries (`imaplib`, `email`).
   * Scans for unseen messages, parses plaintext contents, coordinates optimization, and logs the generated map URLs.

---

## 3. Repository Layout & Archival Policy

The repository preserves the current active release while retaining the three previous version snapshots in `/archive`:

```text
rout-o-rooter/
├── archive/
│   ├── v0.1.0-alpha/README.md     # Initial project scaffold
│   ├── v0.1.1-alpha/README.md     # Parser prototype
│   └── v0.1.2-beta/README.md      # OCR proof of concept
├── .gitignore                     # Standard Python artifact exclusions
├── CHANGELOG.md                   # Complete semantic change history
├── email_listener.py              # IMAP polling background script
├── HANDOVER.md                    # System architecture & maintenance guide
├── index.html                     # Responsive Web GUI (Leaflet + QR + OSRM)
├── README.md                      # General documentation and setup
├── requirements.txt               # Pinned dependencies
├── route_optimizer.py             # Active production codebase (v0.2.1)
└── web_server.py                  # Local GUI web server & API bridge
```

---

## 4. Setup & Operating Instructions

### Prerequisites
* **Python 3.9+**
* **Tesseract OCR Engine**:
  * **Debian/Ubuntu:** `sudo apt-get update && sudo apt-get install -y tesseract-ocr`
  * **macOS:** `brew install tesseract`
  * **Windows:** Download installer and append binary path to system `PATH`.

### Dependency Installation
```bash
pip install -r requirements.txt
```

### Running Self-Tests
Verify local pipeline integrity and routing connectivity:
```bash
python route_optimizer.py
```

### Basic Programmatic Usage
```python
from route_optimizer import RouteOptimizer

opt = RouteOptimizer()

# 1. Ingest coordinates from any supported file
coords = opt.ingest_file("deliveries.csv")  # or stops.json, photo.png, notes.txt

# 2. Compute optimized path
optimized = opt.optimize_route(coords)

# 3. Generate navigation link and QR code
url = opt.generate_google_maps_url(optimized)
qr_path = opt.generate_qr(url)

print("Map URL:", url)
print("QR Code created at:", qr_path)
```

---

## 5. Version Archival Runbook

When releasing subsequent versions (e.g., `v0.2.2` or `v0.3.0`), follow this checklist:

1. **Retire Oldest Archive:** Delete `archive/v0.1.0-alpha/`.
2. **Snapshot Preceding Release:** Create `archive/v0.2.0/` and copy the `v0.2.0` script state there.
3. **Bump Version:**
   * Update `__version__ = "X.X.X"` at the top of `route_optimizer.py`.
   * Add release notes under a new section in `CHANGELOG.md`.
4. **Run Unit Tests:** Confirm `python route_optimizer.py` passes cleanly.
5. **Commit & Push:**
   ```bash
   git add .
   git commit -m "release: vX.X.X with updated archive"
   git push origin main
   ```

---

## 6. Constraints & Operational Notes

* **OSRM Public API Limits:** The public endpoint (`router.project-osrm.org`) has rate limits intended for moderate traffic and development. If deploying for high-concurrency production, run a self-hosted OSRM backend via Docker.
* **Google Maps Web URL Waypoint Limits:** Multi-stop web URLs typically support up to 9-10 intermediate waypoints plus origin and destination without requiring specialized Google Cloud platform keys.
