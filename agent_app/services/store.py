"""SQLite run history (FR-02, FR-21). Each run is one row; the details live in a JSON blob."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_key TEXT NOT NULL,
    jira_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    pass_pct REAL,
    data TEXT NOT NULL DEFAULT '{}'
)
"""


class RunStore:
    def __init__(self, db_path: Path | str):
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)  # Streamlit reruns use new threads
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def create_run(self, jira_key: str, jira_url: str, status: str = "Started") -> int:
        cur = self._conn.execute(
            "INSERT INTO runs (jira_key, jira_url, created_at, status) VALUES (?, ?, ?, ?)",
            (jira_key, jira_url, datetime.now().isoformat(timespec="seconds"), status),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_run(self, run_id: int, *, status: str | None = None,
                   pass_pct: float | None = None, **data) -> None:
        """Set status / pass_pct and merge any extra keyword fields into the JSON blob
        (test_cases, decisions, commit_url, report_path, ...)."""
        row = self._conn.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"No run with id {run_id}")
        merged = {**json.loads(row["data"]), **data}
        self._conn.execute(
            "UPDATE runs SET data = ?, status = COALESCE(?, status), "
            "pass_pct = COALESCE(?, pass_pct) WHERE id = ?",
            (json.dumps(merged), status, pass_pct, run_id),
        )
        self._conn.commit()

    def get_run(self, run_id: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._to_dict(row) if row else None

    def list_runs(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
        return [self._to_dict(r) for r in rows]

    @staticmethod
    def _to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["data"] = json.loads(d["data"])
        return d
