# Rout-o-Rooter (v0.2.1)

A zero-cost route optimization pipeline that ingests raw coordinate data via text, direct file uploads (.csv, .json, .txt), email (IMAP), or image OCR, solves the Traveling Salesperson Problem (TSP) using OSRM, and outputs ready-to-use Google Maps URLs and QR codes.

## Features
* **Zero Cost Engine:** Free OSRM Trip API for route sequencing.
* **Flexible Ingestion:** Direct file upload (.csv, .json, .txt), plain text strings, IMAP email polling, and image OCR via Tesseract.
* **Universal Output:** Web-ready Google Maps multi-stop links and generated QR codes.
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
Run the built-in test suite:
```bash
python route_optimizer.py
```
