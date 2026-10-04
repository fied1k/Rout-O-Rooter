"""
Rout-o-Rooter Local Web Server & GUI Runner
Serves the web application and connects the frontend interface to the RouteOptimizer core engine.
"""
import os
import sys
import json
import base64
import tempfile
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from email.parser import BytesParser
from email.policy import default

from route_optimizer import RouteOptimizer, __version__

PORT = 8080
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
optimizer = RouteOptimizer()


class RoutORooterHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_data = {
                "status": "online",
                "version": __version__,
                "engine": "OSRM Trip API",
                "ocr_support": True
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        # Default fallback to index.html for root path
        if parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/optimize":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                coords = [tuple(c) for c in data.get("coords", [])]
                start_coord = tuple(data["start_coord"]) if data.get("start_coord") else None
                end_coord = tuple(data["end_coord"]) if data.get("end_coord") else None
                roundtrip = bool(data.get("roundtrip", False))

                if len(coords) < 1 and not (start_coord and end_coord):
                    raise ValueError("At least 2 total coordinates are required.")

                optimized = optimizer.optimize_route(
                    coords,
                    start_coord=start_coord,
                    end_coord=end_coord,
                    roundtrip=roundtrip
                )
                maps_url = optimizer.generate_google_maps_url(optimized)
                apple_maps_url = optimizer.generate_apple_maps_url(optimized)
                qr_path = optimizer.generate_qr(maps_url)

                response_payload = {
                    "success": True,
                    "optimized_coords": optimized,
                    "google_maps_url": maps_url,
                    "apple_maps_url": apple_maps_url,
                    "qr_path": qr_path
                }
                self._send_json(200, response_payload)
            except Exception as e:
                self._send_json(400, {"success": False, "error": str(e)})
            return

        elif parsed.path == "/api/parse":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                raw_text = data.get("text", "")
                coords = optimizer.parse_coordinates(raw_text)
                self._send_json(200, {"success": True, "coords": coords})
            except Exception as e:
                self._send_json(400, {"success": False, "error": str(e)})
            return

        elif parsed.path == "/api/upload":
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            try:
                # Support JSON payload with Base64 content
                if "application/json" in content_type:
                    body = self.rfile.read(content_length).decode("utf-8")
                    payload = json.loads(body)
                    filename = payload.get("filename", "upload.tmp")
                    b64_data = payload.get("base64", "")
                    if "," in b64_data:
                        b64_data = b64_data.split(",", 1)[1]
                    file_bytes = base64.b64decode(b64_data)
                elif "multipart/form-data" in content_type:
                    # Python 3.14 compliant multipart parsing via email.parser
                    raw_data = self.rfile.read(content_length)
                    full_payload = (
                        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
                        + raw_data
                    )
                    msg = BytesParser(policy=default).parsebytes(full_payload)
                    file_part = None
                    for part in msg.iter_parts():
                        if part.get_filename():
                            file_part = part
                            break
                    if not file_part:
                        raise ValueError("No file found in multipart upload.")
                    filename = file_part.get_filename()
                    file_bytes = file_part.get_payload(decode=True)
                else:
                    raise ValueError("Unsupported Content-Type. Send JSON or multipart/form-data.")

                ext = os.path.splitext(filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                try:
                    coords = optimizer.ingest_file(tmp_path)
                    self._send_json(200, {"success": True, "filename": filename, "coords": coords})
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            except Exception as e:
                self._send_json(400, {"success": False, "error": str(e)})
            return

        self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def run(port=PORT, open_browser=True):
    server_address = ("", port)
    httpd = HTTPServer(server_address, RoutORooterHandler)
    url = f"http://localhost:{port}"
    print(f"==================================================")
    print(f"  Rout-o-Rooter Web GUI Server v{__version__}")
    print(f"  Serving at: {url}")
    print(f"  Press Ctrl+C to stop the server.")
    print(f"==================================================")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    open_browser = "--no-open" not in sys.argv
    run(port=port, open_browser=open_browser)
