#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Siddham Texts Archive — Local & Production Web Hosting Server (Python)
Serves index.html, styles.css, app.js, all 215 XML files, and all 216 downloadable PDFs.
"""

import http.server
import os
import socketserver
import sys
import webbrowser

PORT = int(os.environ.get("PORT", 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SiddhamRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SiddhamRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print("=" * 68)
        print("  SIDDHAM SOUTH ASIA INSCRIPTIONS ARCHIVE — WEB SERVER")
        print(f"  Hosting at: {url}")
        print("  Press Ctrl+C to stop the server.")
        print("=" * 68)
        if "--no-browser" not in sys.argv:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
