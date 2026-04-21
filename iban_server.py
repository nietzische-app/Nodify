"""IBAN doğrulama için basit yerel web arayüzü."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from iban_parser import parse_iban


PAGE = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>IBAN Doğrulama</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 560px; margin: 3rem auto; padding: 0 1rem; }}
  input {{ width: 100%; padding: .6rem; font-size: 1rem; font-family: monospace; }}
  button {{ margin-top: .6rem; padding: .6rem 1.2rem; font-size: 1rem; cursor: pointer; }}
  pre {{ background: #f4f4f4; padding: 1rem; border-radius: 6px; white-space: pre-wrap; }}
</style>
</head>
<body>
  <h1>IBAN Doğrulama</h1>
  <form method="get" action="/">
    <input name="iban" value="{iban}" placeholder="TR.. veya DE.. ile başlayan IBAN" autofocus>
    <button type="submit">Kontrol et</button>
  </form>
  {result}
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        iban = (params.get("iban", [""])[0]).strip()
        result_html = ""
        if iban:
            result_html = f"<pre>{html.escape(parse_iban(iban))}</pre>"

        body = PAGE.format(iban=html.escape(iban), result=result_html).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    port = 8000
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"IBAN arayüzü: http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
