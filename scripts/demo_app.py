"""Run the real UI on fake services (no credentials, no network): for UI checks and demo rehearsal.

    python -m streamlit run scripts/demo_app.py
"""
import runpy
import sys
import tempfile
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.fakes import build_services

if "_services" not in st.session_state:
    demo = build_services(Path(tempfile.mkdtemp(prefix="demo_")), failing=("TC-3",))
    # Make the fake test run take about 10 seconds so the sidebar spinner can be seen.
    fast = demo.run_tests
    demo.run_tests = lambda scenarios, url: (time.sleep(10), fast(scenarios, url))[1]
    # A few earlier runs so the dashboard and past-runs list have something to show.
    for key, status, pct in (("QA-101", "Pass", 100.0), ("QA-102", "Partial", 75.0), ("QA-103", "Rejected", 50.0),
                            ("QA-104", "Pass", 100.0), ("QA-105", "Fail", 0.0)):
        run_id = demo.store.create_run(key, f"https://example.atlassian.net/browse/{key}", status)
        demo.store.update_run(run_id, status=status, pass_pct=pct)
    st.session_state["_services"] = demo
runpy.run_path(str(ROOT / "agent_app" / "app.py"))
