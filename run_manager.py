import asyncio
import uuid
from typing import Any, Dict

RUNS: Dict[str, Dict[str, Any]] = {}
RUNS_LOCK = asyncio.Lock()


def create_run(metadata: Dict[str, Any]) -> str:
    """Create a new run and return run_id."""
    run_id = uuid.uuid4().hex
    RUNS[run_id] = {
        "id": run_id,
        "status": "pending",
        "messages": [],
        "progress": 0,
        "metadata": metadata,
        "result": None,
    }
    return run_id


async def set_running(run_id: str):
    async with RUNS_LOCK:
        if run_id in RUNS:
            RUNS[run_id]["status"] = "running"


async def append_message(run_id: str, msg: str):
    async with RUNS_LOCK:
        if run_id in RUNS:
            RUNS[run_id]["messages"].append(msg)


async def set_progress(run_id: str, pct: float):
    async with RUNS_LOCK:
        if run_id in RUNS:
            RUNS[run_id]["progress"] = pct


async def set_result(run_id: str, result: Dict[str, Any]):
    async with RUNS_LOCK:
        if run_id in RUNS:
            RUNS[run_id]["status"] = "done"
            RUNS[run_id]["result"] = result
            RUNS[run_id]["progress"] = 100


async def set_error(run_id: str, err_msg: str):
    async with RUNS_LOCK:
        if run_id in RUNS:
            RUNS[run_id]["status"] = "error"
            RUNS[run_id]["messages"].append(err_msg)


async def get_run(run_id: str):
    return RUNS.get(run_id)


async def list_runs():
    return list(RUNS.values())
