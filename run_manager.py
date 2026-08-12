# SPDX-License-Identifier: GPL-3.0-only
"""Run state management with SQLite persistence.

Replaces the in-memory RUNS dict with a SQLite-backed store so that
run progress survives server restarts and multiple workers.
"""
import asyncio
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# SQLite-backed store
# ---------------------------------------------------------------------------

_DB_PATH: Optional[str] = None
_LOCK = asyncio.Lock()


def _get_db() -> sqlite3.Connection:
    """Return a connection to the run store DB, creating tables if needed."""
    global _DB_PATH
    import os
    if _DB_PATH is None:
        _DB_PATH = os.path.join(os.path.dirname(__file__), "runs.db")
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            messages TEXT NOT NULL DEFAULT '[]',
            progress REAL NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '{}',
            result TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def create_run(metadata: Dict[str, Any]) -> str:
    """Create a new run and return run_id."""
    run_id = uuid.uuid4().hex
    now = time.time()
    conn = _get_db()
    conn.execute(
        "INSERT INTO runs (id, status, messages, progress, metadata, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (run_id, "pending", "[]", 0, __to_json(metadata), 0, now, now),
    )
    conn.commit()
    conn.close()
    return run_id


async def set_running(run_id: str):
    async with _LOCK:
        conn = _get_db()
        conn.execute("UPDATE runs SET status='running', updated_at=? WHERE id=?", (time.time(), run_id))
        conn.commit()
        conn.close()


async def append_message(run_id: str, msg: str):
    async with _LOCK:
        conn = _get_db()
        cur = conn.execute("SELECT messages FROM runs WHERE id=?", (run_id,))
        row = cur.fetchone()
        msgs: List[str] = []
        if row:
            msgs = __from_json(row[0], default=[])
            msgs.append(msg)
            conn.execute("UPDATE runs SET messages=?, updated_at=? WHERE id=?", (__to_json(msgs), time.time(), run_id))
            conn.commit()
        conn.close()


async def set_progress(run_id: str, pct: float):
    async with _LOCK:
        conn = _get_db()
        conn.execute("UPDATE runs SET progress=?, updated_at=? WHERE id=?", (pct, time.time(), run_id))
        conn.commit()
        conn.close()


async def set_result(run_id: str, result: Dict[str, Any]):
    async with _LOCK:
        conn = _get_db()
        conn.execute(
            "UPDATE runs SET status='done', result=?, progress=100, updated_at=? WHERE id=?",
            (__to_json(result), time.time(), run_id),
        )
        conn.commit()
        conn.close()


async def set_error(run_id: str, err_msg: str):
    async with _LOCK:
        conn = _get_db()
        cur = conn.execute("SELECT messages FROM runs WHERE id=?", (run_id,))
        row = cur.fetchone()
        msgs: List[str] = []
        if row:
            msgs = __from_json(row[0], default=[])
        msgs.append(err_msg)
        conn.execute(
            "UPDATE runs SET status='error', messages=?, updated_at=? WHERE id=?",
            (__to_json(msgs), time.time(), run_id),
        )
        conn.commit()
        conn.close()


async def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_db()
    cur = conn.execute("SELECT id, status, messages, progress, metadata, result, created_at, updated_at FROM runs WHERE id=?", (run_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "messages": __from_json(row[2], default=[]),
        "progress": row[3],
        "metadata": __from_json(row[4], default={}),
        "result": __from_json(row[5], default=None),
        "created_at": row[6],
        "updated_at": row[7],
    }


async def list_runs() -> List[Dict[str, Any]]:
    conn = _get_db()
    cur = conn.execute("SELECT id, status, messages, progress, metadata, result, created_at, updated_at FROM runs ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    out = []
    for row in rows:
        out.append({
            "id": row[0],
            "status": row[1],
            "messages": __from_json(row[2], default=[]),
            "progress": row[3],
            "metadata": __from_json(row[4], default={}),
            "result": __from_json(row[5], default=None),
            "created_at": row[6],
            "updated_at": row[7],
        })
    return out


async def delete_run(run_id: str) -> bool:
    async with _LOCK:
        conn = _get_db()
        cur = conn.execute("DELETE FROM runs WHERE id=?", (run_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def __to_json(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return "{}"


def __from_json(raw: Optional[str], default: Any = None) -> Any:
    import json
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default
