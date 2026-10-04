# Rout-o-Rooter (v0.2.1)

A zero-cost route optimization pipeline that ingests raw coordinate data via text, direct file uploads (.csv, .json, .txt), email (IMAP), or image OCR, solves the Traveling Salesperson Problem (TSP) using OSRM, and outputs ready-to-use Google Maps URLs and QR codes.

## Features
* **Zero Cost Engine:** Free OSRM Trip API for route sequencing.
* **Modern Web GUI:** Interactive Leaflet map, drag-and-drop file upload, instant OSRM routing, live scannable QR codes, and dual Google Maps / Apple Maps handoff.
* **Flexible Ingestion:** Direct file upload (.csv, .json, .txt), plain text strings, IMAP email polling, and image OCR via Tesseract.
* **Universal Output:** Web-ready Google Maps and Apple Maps multi-stop navigation links, and dynamic QR codes.
* **Integrated Testing:** Self-testing `unittest` suite validating parsing, file ingestion, and routing before deployment.

## Installation
1. Install system OCR dependency (if using images):
   * Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   * macOS: `brew install tesseract`
   * Windows: Install Tesseract-OCR and ensure it is in your system PATH.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Web GUI (Interactive Interface)
Launch the local web server with full Python OCR engine connectivity:
```bash
python web_server.py
```
This serves `index.html` at `http://localhost:8080` and automatically opens your browser.

*Note: You can also open `index.html` directly in any web browser to run in zero-server standalone mode with client-side OSRM routing.*

### 2. Command-Line & Self-Testing
Run the built-in test suite:
```bash
python route_optimizer.py
```

### 3. Background Email Listener
Monitor an IMAP inbox for incoming coordinate payloads:
```bash
python email_listener.py
```
