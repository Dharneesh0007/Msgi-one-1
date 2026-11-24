import os
import sys
import time
import subprocess
import urllib.request
import http.server
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "apps" / "mobile" / "dist"
SCREENSHOTS_DIR = ROOT / "docs" / "phase7" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Using Chromium browser at: {CHROME_PATH}")


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self):
        # Resolve clean path
        clean_path = self.path.split("?")[0].lstrip("/")
        target = Path(self.directory) / clean_path
        if not target.exists() or target.is_dir():
            self.path = "/index.html"
        return super().do_GET()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


httpd = ReusableTCPServer(("127.0.0.1", 8089), SPAHandler)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()
print("SPA Server running on http://127.0.0.1:8089")

try:
    time.sleep(1.0)
    targets = [
        ("login_compact_android_360x800.png", 360, 800),
        ("login_standard_android_412x915.png", 412, 915),
        ("login_web_1440x900.png", 1440, 900),
    ]

    for filename, width, height in targets:
        out_path = SCREENSHOTS_DIR / filename
        cmd = [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={width},{height}",
            "--virtual-time-budget=6000",
            f"--screenshot={out_path}",
            "http://127.0.0.1:8089/",
        ]
        print(f"Capturing {filename} ({width}x{height})...")
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"SUCCESS: {filename} ({out_path.stat().st_size} bytes)")
        else:
            print(f"FAILED to capture {filename}: stderr={res.stderr.decode('utf-8', errors='ignore')}")

finally:
    print("Shutting down SPA server...")
    httpd.shutdown()
    print("Server stopped cleanly.")
