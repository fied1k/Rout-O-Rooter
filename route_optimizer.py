"""
Route Optimizer Core (v0.2.1)
Pipeline: File/Image/Text -> Extract Coords -> OSRM TSP Solver -> Map URL & QR
"""
import csv
import json
import os
import re
import urllib.parse
from typing import List, Tuple
import unittest
import requests
import qrcode
import pytesseract
from PIL import Image

__version__ = "0.2.1"


class RouteOptimizer:
    def __init__(self):
        # Regex capturing Latitude, Longitude patterns across diverse text formats
        self.coord_pattern = re.compile(r"(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)")

    def ingest_image(self, image_path: str) -> str:
        """Extracts raw text from an image using Tesseract OCR."""
        try:
            return pytesseract.image_to_string(Image.open(image_path))
        except Exception as e:
            raise ValueError(f"OCR Failed: {str(e)}")

    def parse_coordinates(self, text: str) -> List[Tuple[float, float]]:
        """Parses raw text and returns a list of (lat, lon) tuples."""
        matches = self.coord_pattern.findall(text)
        if not matches:
            raise ValueError("No valid coordinates found in input.")
        return [(float(lat), float(lon)) for lat, lon in matches]

    def ingest_file(self, file_path: str) -> List[Tuple[float, float]]:
        """
        Parses coordinates from a file path supporting .csv, .json, .txt, or image formats.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # Image OCR routing
        if ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
            raw_text = self.ingest_image(file_path)
            return self.parse_coordinates(raw_text)

        # JSON file ingestion
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            coords: List[Tuple[float, float]] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        coords.append((float(item[0]), float(item[1])))
                    elif isinstance(item, dict):
                        lat = item.get("lat") or item.get("latitude")
                        lon = item.get("lon") or item.get("lng") or item.get("longitude")
                        if lat is not None and lon is not None:
                            coords.append((float(lat), float(lon)))
            if not coords:
                raise ValueError("No coordinates found in JSON.")
            return coords

        # CSV file ingestion
        elif ext == ".csv":
            coords = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and any(h and h.lower() in ["lat", "latitude"] for h in reader.fieldnames):
                    for row in reader:
                        row_lower = {k.lower(): v for k, v in row.items() if k}
                        lat = row_lower.get("lat") or row_lower.get("latitude")
                        lon = row_lower.get("lon") or row_lower.get("lng") or row_lower.get("longitude")
                        if lat and lon:
                            coords.append((float(lat), float(lon)))
                else:
                    # Fallback for headerless CSVs
                    f.seek(0)
                    return self.parse_coordinates(f.read())
            if not coords:
                raise ValueError("No coordinates found in CSV.")
            return coords

        # Plain text and fallback
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return self.parse_coordinates(f.read())

    def optimize_route(
        self,
        coords: List[Tuple[float, float]],
        start_coord: Tuple[float, float] = None,
        end_coord: Tuple[float, float] = None,
        roundtrip: bool = False
    ) -> List[Tuple[float, float]]:
        """Uses OSRM Trip API to sequence coordinates (TSP solver) with optional start/end endpoints."""
        route_points = list(coords)
        if start_coord and (not route_points or route_points[0] != start_coord):
            route_points.insert(0, start_coord)

        if end_coord and (not route_points or route_points[-1] != end_coord):
            route_points.append(end_coord)

        if len(route_points) < 2:
            raise ValueError("Requires at least 2 coordinates.")

        coord_string = ";".join([f"{lon},{lat}" for lat, lon in route_points])

        dest_flag = "last" if (end_coord or roundtrip) else "any"
        roundtrip_flag = "true" if roundtrip else "false"

        url = (
            f"http://router.project-osrm.org/trip/v1/driving/{coord_string}"
            f"?roundtrip={roundtrip_flag}&source=first&destination={dest_flag}"
        )

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise ConnectionError("Failed to reach OSRM routing engine.")

        data = response.json()
        if data.get("code") != "Ok":
            raise ValueError("OSRM failed to optimize route.")

        # Re-order original points by waypoint order
        waypoints = data["waypoints"]
        waypoints.sort(key=lambda x: x["waypoint_index"])
        return [(wp["location"][1], wp["location"][0]) for wp in waypoints]

    def generate_google_maps_url(self, coords: List[Tuple[float, float]]) -> str:
        """Builds a clickable Google Maps multi-stop URL."""
        if len(coords) < 2:
            raise ValueError("Requires at least 2 coordinates.")

        origin = f"{coords[0][0]},{coords[0][1]}"
        destination = f"{coords[-1][0]},{coords[-1][1]}"
        waypoints = "|".join([f"{lat},{lon}" for lat, lon in coords[1:-1]])

        base_url = "https://www.google.com/maps/dir/?api=1"
        params = {"origin": origin, "destination": destination}
        if waypoints:
            params["waypoints"] = waypoints

        return f"{base_url}&{urllib.parse.urlencode(params)}"

    def generate_apple_maps_url(self, coords: List[Tuple[float, float]]) -> str:
        """Builds a clickable Apple Maps multi-stop navigation URL using the unified Maps URL scheme."""
        if len(coords) < 2:
            raise ValueError("Requires at least 2 coordinates.")

        source = f"{coords[0][0]},{coords[0][1]}"
        destination = f"{coords[-1][0]},{coords[-1][1]}"
        base_url = "https://maps.apple.com/directions"

        params = [f"source={source}", f"destination={destination}"]
        for lat, lon in coords[1:-1]:
            params.append(f"waypoint={lat},{lon}")
        params.append("mode=driving")

        return f"{base_url}?{'&'.join(params)}"

    def chunk_coordinates(self, coords: List[Tuple[float, float]], max_stops: int = 10) -> List[List[Tuple[float, float]]]:
        """
        Splits a list of coordinates into consecutive chained parts where each part has at most
        `max_stops` locations (with the end stop of Part N being the start stop of Part N+1).
        """
        if len(coords) <= max_stops:
            return [coords]

        chunks = []
        step = max_stops - 1
        for i in range(0, len(coords) - 1, step):
            chunk = coords[i : i + max_stops]
            chunks.append(chunk)
            if i + max_stops >= len(coords):
                break
        return chunks

    def generate_segmented_urls(
        self, coords: List[Tuple[float, float]], max_stops: int = 10
    ) -> List[dict]:
        """
        Generates Google Maps and Apple Maps navigation URLs partitioned into multi-stop parts
        (to respect Google Maps and Apple Maps ~10 waypoint limits per URL).
        """
        chunks = self.chunk_coordinates(coords, max_stops=max_stops)
        segments = []
        total_parts = len(chunks)

        start_offset = 1
        for idx, chunk in enumerate(chunks, 1):
            g_url = self.generate_google_maps_url(chunk)
            a_url = self.generate_apple_maps_url(chunk)
            end_offset = start_offset + len(chunk) - 1
            segments.append({
                "part": idx,
                "total_parts": total_parts,
                "start_index": start_offset,
                "end_index": end_offset,
                "label": f"Part {idx} (Stops {start_offset}–{end_offset})",
                "stops_count": len(chunk),
                "coords": chunk,
                "google_maps_url": g_url,
                "apple_maps_url": a_url,
            })
            start_offset = end_offset
        return segments

    def generate_qr(self, url: str, output_path: str = "route_qr.png") -> str:
        """Generates a QR code image from the URL."""
        img = qrcode.make(url)
        img.save(output_path)
        return output_path


# ==========================================
# BUILT-IN QUALITY CHECKS & SELF-TESTING
# ==========================================
class TestRouteOptimizer(unittest.TestCase):
    def setUp(self):
        self.ro = RouteOptimizer()
        self.sample_text = "Stop A: 38.9806, -94.6730\nStop B: 39.0997, -94.5786"
        self.temp_files = []

    def tearDown(self):
        for path in self.temp_files:
            if os.path.exists(path):
                os.remove(path)

    def test_coordinate_parsing(self):
        coords = self.ro.parse_coordinates(self.sample_text)
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[0], (38.9806, -94.6730))

    def test_file_ingestion_csv(self):
        csv_path = "test_coords.csv"
        self.temp_files.append(csv_path)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("lat,lon,name\n38.9806,-94.6730,Location 1\n39.0997,-94.5786,Location 2\n")
        coords = self.ro.ingest_file(csv_path)
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[0], (38.9806, -94.6730))

    def test_file_ingestion_json(self):
        json_path = "test_coords.json"
        self.temp_files.append(json_path)
        data = [{"lat": 38.9806, "lon": -94.6730}, {"lat": 39.0997, "lon": -94.5786}]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        coords = self.ro.ingest_file(json_path)
        self.assertEqual(len(coords), 2)
        self.assertEqual(coords[1], (39.0997, -94.5786))

    def test_routing_and_url(self):
        coords = [(38.9806, -94.6730), (39.0997, -94.5786)]
        optimized = self.ro.optimize_route(coords)
        url = self.ro.generate_google_maps_url(optimized)
        self.assertIn("api=1", url)
        self.assertIn("origin=", url)
        apple_url = self.ro.generate_apple_maps_url(optimized)
        self.assertIn("maps.apple.com/directions", apple_url)
        self.assertIn("source=", apple_url)
        self.assertIn("destination=", apple_url)

    def test_start_and_end_endpoints(self):
        stops = [(39.0997, -94.5786), (39.1141, -94.6275)]
        start = (38.9806, -94.6730)
        end = (38.9282, -94.7214)
        optimized = self.ro.optimize_route(stops, start_coord=start, end_coord=end)
        self.assertEqual(len(optimized), 4)
        self.assertAlmostEqual(optimized[0][0], start[0], places=2)
        self.assertAlmostEqual(optimized[-1][0], end[0], places=2)

    def test_segmented_urls(self):
        # 20 coordinates split into max 10 stops per part
        coords = [(36.0 + i * 0.01, -95.0 - i * 0.01) for i in range(20)]
        segments = self.ro.generate_segmented_urls(coords, max_stops=10)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["part"], 1)
        self.assertEqual(segments[0]["stops_count"], 10)
        self.assertEqual(segments[1]["part"], 2)
        self.assertEqual(segments[1]["stops_count"], 10)
        self.assertEqual(segments[2]["part"], 3)
        self.assertEqual(segments[2]["stops_count"], 2)
        self.assertIn("api=1", segments[0]["google_maps_url"])
        self.assertIn("maps.apple.com/directions", segments[0]["apple_maps_url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
