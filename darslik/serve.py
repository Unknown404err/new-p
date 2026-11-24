#!/usr/bin/env python3
"""
Darslik uchun kichik statik server (preview uchun).

Oddiy `python3 -m http.server` dan farqi:
  * UTF-8 charset to'g'ri beriladi (o'zbekcha apostroflar buzilmaydi);
  * HTML/PDF keshlanmaydi — tahrirdan keyin darhol yangi nusxa ko'rinadi;
  * `/` -> index.html, `/favicon.ico` 404 emas (ichki SVG belgi);
  * PDF brauzerda ochiladi (inline) va yuklab olish ham mumkin.

Ishlatish:
    python3 serve.py [port]        # standart 8000
"""

from __future__ import annotations

import functools
import http.server
import os
import re
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="12" fill="#0f6b62"/>'
    '<text x="32" y="44" font-family="Georgia,serif" font-size="34" font-weight="bold" '
    'fill="#fbf9f5" text-anchor="middle">1000</text></svg>'
).encode("utf-8")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".pdf": "application/pdf",
        ".svg": "image/svg+xml",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0] in ("/favicon.ico", "/favicon.svg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(FAVICON)))
            self.end_headers()
            self.wfile.write(FAVICON)
            return
        super().do_GET()

    def send_head(self):
        if self.path.split("?")[0] == "/":
            self.path = "/index.html"

        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()

        # oddiy Range qo'llab-quvvatlash — telefonda PDF sahifalab yuklash uchun
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
        if not match:
            return super().send_head()

        size = os.path.getsize(path)
        start_s, end_s = match.groups()
        if start_s:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
        else:  # "bytes=-500" — oxirgi 500 bayt
            start = max(size - int(end_s or 0), 0)
            end = size - 1
        if start >= size or end < start:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        end = min(end, size - 1)
        length = end - start + 1

        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return _SlicedFile(f, length)

    def log_message(self, fmt, *args):  # konsol toza bo'lsin, lekin xatolar ko'rinsin
        if str(args[1] if len(args) > 1 else "").startswith(("4", "5")):
            super().log_message(fmt, *args)


class _SlicedFile:
    """Faylning faqat kerakli bo'lagini o'qiydigan o'ram (copyfile uchun)."""

    def __init__(self, f, length: int):
        self._f = f
        self._left = length

    def read(self, size: int = -1) -> bytes:
        if self._left <= 0:
            return b""
        if size is None or size < 0:
            size = self._left
        data = self._f.read(min(size, self._left))
        self._left -= len(data)
        return data

    def close(self) -> None:
        self._f.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    handler = functools.partial(Handler, directory=str(ROOT))
    with Server(("0.0.0.0", PORT), handler) as httpd:
        print(f"Darslik: http://0.0.0.0:{PORT}/  (papka: {ROOT})", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
