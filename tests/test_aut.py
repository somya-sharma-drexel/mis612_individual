"""Smoke tests for the registration page (AUT-1..5). Starts the AUT server itself."""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000"
SERVE = Path(__file__).resolve().parent.parent / "aut" / "serve.py"


@pytest.fixture(scope="module")
def aut_server():
    proc = subprocess.Popen([sys.executable, str(SERVE)])
    for _ in range(50):
        try:
            urllib.request.urlopen(URL, timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield
    proc.terminate()


@pytest.fixture()
def page(aut_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(URL)
        yield pg
        browser.close()


def test_elements_present_with_test_ids(page):  # AUT-1, AUT-4
    for tid in ("username", "password", "register"):
        assert page.get_by_test_id(tid).is_visible()


def test_password_masked(page):  # AUT-2
    assert page.get_by_test_id("password").get_attribute("type") == "password"


def test_valid_registration_shows_hello_world(page):  # AUT-3
    page.get_by_test_id("username").fill("alice")
    page.get_by_test_id("password").fill("password123")
    page.get_by_test_id("register").click()
    assert page.get_by_test_id("success").inner_text() == "HELLO WORLD"
    assert not page.get_by_test_id("error").is_visible()


@pytest.mark.parametrize(
    "username,password,message",
    [
        ("", "password123", "Username is required."),
        ("alice", "", "Password is required."),
        ("alice", "short", "at least 8"),
        ("alice", "1234567", "at least 8"),
    ],
)
def test_invalid_input_shows_error(page, username, password, message):
    page.get_by_test_id("username").fill(username)
    page.get_by_test_id("password").fill(password)
    page.get_by_test_id("register").click()
    assert message in page.get_by_test_id("error").inner_text()
    assert not page.get_by_test_id("success").is_visible()


def test_eight_char_password_is_accepted(page):  # boundary
    page.get_by_test_id("username").fill("alice")
    page.get_by_test_id("password").fill("12345678")
    page.get_by_test_id("register").click()
    assert page.get_by_test_id("success").is_visible()
