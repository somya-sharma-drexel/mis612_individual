"""Make sure the registration page (AUT) is running before tests execute (AUT-5)."""
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

from agent_app.config import ROOT, ServiceError

_proc: subprocess.Popen | None = None


def aut_reachable(url: str) -> bool:
    try:
        urllib.request.urlopen(url, timeout=2)
        return True
    except OSError:
        return False


def ensure_aut_running(url: str) -> None:
    """Start the local AUT server if nothing answers at `url`; raise ServiceError if it cannot."""
    global _proc
    if aut_reachable(url):
        return
    parsed = urlparse(url)
    if parsed.hostname not in ("localhost", "127.0.0.1") or not parsed.port:
        raise ServiceError(f"The registration page is not reachable at {url}.")
    _proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(parsed.port), "--bind", "127.0.0.1",
         "--directory", str(ROOT / "aut")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if aut_reachable(url):
            return
        time.sleep(0.1)
    raise ServiceError(f"Could not start the registration page at {url}.")
