import sqlite3
import time
import json
from typing import List

DB_PATH = None


def init_db(db_path: str):
    global DB_PATH
    DB_PATH = db_path
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            added_at REAL NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at REAL NOT NULL,
            host TEXT,
            summary_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_host(url: str) -> None:
    if not DB_PATH:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO hosts (url, added_at) VALUES (?, ?)", (url, time.time()))
        conn.commit()
    except sqlite3.OperationalError:
        # Table doesn't exist yet - ignore
        pass
    finally:
        conn.close()


def delete_host(url: str) -> None:
    if not DB_PATH:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM hosts WHERE url = ?", (url,))
        conn.commit()
    except sqlite3.OperationalError:
        # Table doesn't exist yet - ignore
        pass
    finally:
        conn.close()


def list_hosts() -> List[str]:
    if not DB_PATH:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT url FROM hosts ORDER BY added_at DESC")
        rows = c.fetchall()
        return [r[0] for r in rows]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []
    finally:
        conn.close()


def save_run(summary: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at REAL NOT NULL,
            host TEXT,
            summary_json TEXT NOT NULL
        )
        """)
        conn.commit()
        c.execute("INSERT INTO runs (created_at, host, summary_json) VALUES (?, ?, ?)", (time.time(), summary.get('host'), json.dumps(summary)))
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()


def list_runs() -> List[dict]:
    if not DB_PATH:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, created_at, host FROM runs ORDER BY created_at DESC")
        rows = c.fetchall()
        return [{'id': r[0], 'created_at': r[1], 'host': r[2]} for r in rows]
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return []
    finally:
        conn.close()


def get_run(run_id: int) -> dict:
    if not DB_PATH:
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT summary_json FROM runs WHERE id = ?", (run_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return None
    finally:
        conn.close()
