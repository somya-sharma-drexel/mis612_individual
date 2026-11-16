"""Serve the registration page at a fixed URL: http://localhost:8000 (AUT-5)."""
import functools
import http.server
import pathlib

PORT = 8000
DIRECTORY = pathlib.Path(__file__).parent

if __name__ == "__main__":
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIRECTORY))
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        print(f"Registration page at http://localhost:{PORT}")
        server.serve_forever()
