# SPDX-License-Identifier: GPL-3.0-only
from flask import Flask, render_template, request, jsonify, send_file, abort
import threading
import os
import json
import time
import asyncio
import sys
import logging
import re
import io
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

# make repo importable: ensure project root and cwd are on sys.path
proj_root = os.path.abspath(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
# also ensure current working directory is available (covers `flask run` behavior)
cwd = os.path.abspath(os.getcwd())
if cwd not in sys.path:
    sys.path.insert(0, cwd)

from ollama import Client
from ollama_etch_tester import test_model
import db
import run_manager

# initialize DB
DB_FILE = os.path.join(os.path.dirname(__file__), "data.db")
try:
    db.init_db(DB_FILE)
except Exception:
    pass

# default host shown in the UI
DEFAULT_HOST = os.environ.get('OLLAMA_DEFAULT_HOST', 'http://localhost:11434')

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ollamaiq")

def get_saved_hosts():
    s = _unique(db.list_hosts())
    if DEFAULT_HOST not in s:
        s.append(DEFAULT_HOST)
    return s

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))

import datetime

@app.template_filter('datetimeformat')
def datetimeformat(ts):
    return datetime.datetime.fromtimestamp(ts).isoformat()


def _unique(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

# helper to call async run_manager functions from sync code
def arun(coro):
    return asyncio.run(coro)

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
_HOST_RE = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')

def validate_host(host: str) -> Optional[str]:
    """Return None if valid, else an error message."""
    if not host or not host.strip():
        return "Host URL is required."
    host = host.strip()
    if not _HOST_RE.match(host):
        return "Invalid URL format. Use http:// or https://."
    parsed = urlparse(host)
    if not parsed.hostname:
        return "Invalid hostname."
    return None

def validate_api_key(key: str) -> Optional[str]:
    if key and len(key) > 1024:
        return "API key too long."
    return None

def sanitize_string(s: str, default: str = "") -> str:
    if not s:
        return default
    return s.strip()[:2048]


def _get_client(host: str, api_key: Optional[str]) -> Client:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return Client(host=host, headers=headers) if headers or host else Client()


def _normalize_models(models_raw) -> List[str]:
    # normalize and dedupe across possible Ollama response shapes
    names: List[str] = []
    try:
        for m in list(models_raw):
            name = None
            if isinstance(m, str):
                name = m
            elif isinstance(m, dict):
                name = m.get('name') or m.get('model') or str(m)
            elif isinstance(m, (list, tuple)) and len(m) == 2 and isinstance(m[0], str) and isinstance(m[1], (list, tuple)):
                for e in m[1]:
                    if hasattr(e, 'model'):
                        nm = getattr(e, 'model')
                        if nm and nm not in names:
                            names.append(nm)
                continue
            elif hasattr(m, 'model'):
                name = getattr(m, 'model')
            else:
                name = str(m)
            if name and name not in names:
                names.append(name)
    except Exception:
        names = [str(models_raw)]
    return names


def _run_tests_sync(host: str, api_key: Optional[str], repeat: int, models: Optional[List[str]], run_id: Optional[str] = None) -> Dict[str, Any]:
    client = _get_client(host, api_key)

    try:
        models_raw = client.list()
    except Exception as e:
        if run_id:
            arun(run_manager.set_error(run_id, str(e)))
        return {"host": host, "models_tested": [], "available_models": [], "timestamp": time.time(), "error": str(e)}

    # save host
    try:
        db.add_host(host)
    except Exception:
        pass

    names = _normalize_models(models_raw)

    if models:
        test_models = [mn for mn in models if mn in names]
    else:
        test_models = [mn for mn in names if 'etch' in mn.lower()]

    summary = {"host": host, "models_tested": [], "available_models": names, "timestamp": time.time()}
    if not test_models:
        return summary

    total = len(test_models)
    for idx, mn in enumerate(test_models, start=1):
        if run_id:
            arun(run_manager.append_message(run_id, f"Testing model: {mn} ({idx}/{total})..."))
            arun(run_manager.set_progress(run_id, int(((idx - 1) / total) * 100)))

        res = test_model(client, mn, repeat)
        summary['models_tested'].append(res)

        if run_id:
            arun(run_manager.append_message(run_id, f"Completed {mn}: smartness={res.get('smartness_score')}% mean={res.get('latency_stats', {}).get('mean')}s"))
            arun(run_manager.set_progress(run_id, int((idx / total) * 95)))

    if run_id:
        arun(run_manager.set_progress(run_id, 95))

    return summary


@app.route('/')
def index():
    saved = get_saved_hosts()
    return render_template('index.html', results=None, rows=[], fastest=None, best_code=None, best_smart=None, saved_hosts=saved)


@app.route('/fetch', methods=['POST'])
def fetch():
    chosen = sanitize_string(request.form.get('host_new')) or sanitize_string(request.form.get('host')) or ''
    api_key = request.form.get('api_key', '')

    host_err = validate_host(chosen)
    if host_err:
        return render_template('index.html', request=request, results={'host':chosen,'models_tested':[],'available_models':[],'timestamp':time.time(),'error':host_err}, rows=[], fastest=None, best_code=None, best_smart=None, saved_hosts=db.list_hosts())

    key_err = validate_api_key(api_key)
    if key_err:
        return render_template('index.html', request=request, results={'host':chosen,'models_tested':[],'available_models':[],'timestamp':time.time(),'error':key_err}, rows=[], fastest=None, best_code=None, best_smart=None, saved_hosts=db.list_hosts())

    try:
        db.add_host(chosen)
    except Exception:
        pass

    client = _get_client(chosen, api_key)
    try:
        models_raw = client.list()
    except Exception as e:
        logger.warning("fetch failed for %s: %s", chosen, e)
        return render_template(
            'index.html',
            request=request,
            results={
                'host': chosen,
                'models_tested': [],
                'available_models': [],
                'timestamp': time.time(),
                'error': str(e)
            },
            rows=[],
            fastest=None,
            best_code=None,
            best_smart=None,
            saved_hosts=db.list_hosts()
        )

    # Normalized list of model names
    model_names = _normalize_models(models_raw)

    # Gather detailed info for each model (especially those containing 'etch')
    model_details: Dict[str, Any] = {}
    for name in model_names:
        try:
            # The Ollama client provides a `show` method to retrieve model details.
            # If the method does not exist or fails, we fall back to an empty dict.
            raw_details = getattr(client, 'show', lambda m: {})(name)
        except Exception:
            raw_details = {}

        # Convert ShowResponse (or other pydantic models) to plain dicts for JSON serialization.
        if hasattr(raw_details, "dict"):
            try:
                details = raw_details.dict()
            except Exception:
                details = {}
        elif hasattr(raw_details, "model_dump"):
            try:
                details = raw_details.model_dump()
            except Exception:
                details = {}
        else:
            details = raw_details

        model_details[name] = details

    results = {
        'host': chosen,
        'models_tested': [],
        'available_models': model_names,
        'model_details': model_details,
        'timestamp': time.time()
    }
    return render_template(
        'index.html',
        results=results,
        rows=[],
        fastest=None,
        best_code=None,
        best_smart=None,
        saved_hosts=get_saved_hosts()
    )


@app.route('/start_run', methods=['POST'])
def start_run():
    payload = request.get_json() or {}
    host = payload.get('host')
    api_key = payload.get('api_key')
    repeat = int(payload.get('repeat') or 1)
    models = payload.get('models')
    if not host:
        return jsonify({'error':'host required'})

    run_id = run_manager.create_run({'host': host, 'models': models or [], 'repeat': repeat})

    def bg():
        arun(run_manager.set_running(run_id))
        arun(run_manager.append_message(run_id, 'Starting run...'))
        try:
            summary = _run_tests_sync(host, api_key, repeat, models, run_id=run_id)

            # compute top summary
            try:
                ms = summary.get('models_tested', []) or []
                top = {}
                if ms:
                    try:
                        fastest = min(ms, key=lambda m: (m.get('latency_stats') or {}).get('mean') or float('inf'))
                        top['fastest'] = {'model': fastest.get('model'), 'mean': (fastest.get('latency_stats') or {}).get('mean')}
                    except Exception:
                        pass
                    try:
                        best_code = max(ms, key=lambda m: (m.get('code_score') is not None) and float(m.get('code_score')) or -1)
                        if best_code and best_code.get('code_score') is not None:
                            top['best_code'] = {'model': best_code.get('model'), 'code_score': best_code.get('code_score')}
                    except Exception:
                        pass
                    try:
                        best_smart = max(ms, key=lambda m: (m.get('smartness_score') is not None) and float(m.get('smartness_score')) or -1)
                        if best_smart and best_smart.get('smartness_score') is not None:
                            top['best_smart'] = {'model': best_smart.get('model'), 'smartness_score': best_smart.get('smartness_score')}
                    except Exception:
                        pass
                summary['top_summary'] = top
            except Exception:
                summary['top_summary'] = {}

            arun(run_manager.append_message(run_id, 'Tests complete; saving result'))
            arun(run_manager.set_result(run_id, summary))
            try:
                p = os.path.join(os.path.dirname(__file__), 'latest_results.json')
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2)
                arun(run_manager.append_message(run_id, f"Saved results to {p}"))
            except Exception as e2:
                arun(run_manager.append_message(run_id, f"Failed to save results: {e2}"))

            try:
                run_db_id = db.save_run(summary)
                arun(run_manager.append_message(run_id, f"Saved run into DB (id={run_db_id})"))
                summary['_db_id'] = run_db_id
                arun(run_manager.set_result(run_id, summary))
            except Exception as e3:
                arun(run_manager.append_message(run_id, f"Failed to persist run to DB: {e3}"))

            arun(run_manager.set_progress(run_id, 100))
        except Exception as e:
            arun(run_manager.set_error(run_id, str(e)))

    thread = threading.Thread(target=bg, daemon=True)
    thread.start()

    return jsonify({'run_id': run_id})


@app.route('/run_status/<run_id>')
def run_status(run_id):
    r = arun(run_manager.get_run(run_id))
    if not r:
        return jsonify({'error':'not found'})
    return jsonify(r)


@app.route('/about')
def about():
    version = None
    try:
        with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'r', encoding='utf-8') as vf:
            version = vf.read().strip()
    except Exception:
        version = 'unknown'
    return render_template('about.html', version=version)


@app.route('/delete_host', methods=['POST'])
def delete_host():
    payload = request.get_json() or {}
    host = payload.get('host')
    if not host:
        return jsonify({'error': 'No host provided'})
    try:
        db.delete_host(host)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/history')
def history():
    try:
        runs = db.list_runs()
    except Exception as e:
        # DB not initialized or other error
        return render_template('history.html', runs=[], db_error=str(e))
    return render_template('history.html', runs=runs)

@app.route('/api/total_history')
def total_history():
    try:
        runs = db.list_runs()
        total = len(runs)
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500
    return jsonify({'total': total})

@app.route('/download/<int:run_id>')
def download_run(run_id):
    try:
        data = db.get_run(run_id)
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500
    if not data:
        abort(404)
    return jsonify(data)


@app.route('/view/<int:run_id>')
def view_run(run_id):
    try:
        data = db.get_run(run_id)
    except Exception as e:
        logger.error("view_run db error: %s", e)
        return render_template('index.html', results={'error': f'Database error: {e}'}, rows=[], fastest=None, best_code=None, best_smart=None, saved_hosts=get_saved_hosts())
    if not data:
        return render_template('history.html', runs=db.list_runs())
    return render_template('index.html', results=data, rows=[], fastest=None, best_code=None, best_smart=None, saved_hosts=get_saved_hosts())

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": time.time()})

# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------
@app.route('/export/<int:run_id>')
def export_csv(run_id):
    try:
        data = db.get_run(run_id)
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500
    if not data:
        abort(404)

    models_tested = data.get('models_tested', []) or []
    lines = ["Model,Smartness %,Code %,Mean(s),Median(s),Min(s),Max(s)"]
    for m in models_tested:
        ls = m.get('latency_stats', {}) or {}
        smart = m.get('smartness_score', '')
        code = m.get('code_score', '')
        mean = ls.get('mean', '')
        median = ls.get('median', '')
        mn = ls.get('min', '')
        mx = ls.get('max', '')
        # Escape model name for CSV
        model = m.get('model', '')
        if ',' in model or '"' in model:
            model = '"' + model.replace('"', '""') + '"'
        lines.append(f"{model},{smart},{code},{mean},{median},{mn},{mx}")
    csv_content = "\n".join(lines) + "\n"
    response = app.make_response(csv_content)
    response.headers.set('Content-Type', 'text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename=f'ollamaiq_run_{run_id}.csv')
    return response


if __name__ == '__main__':
    # Debug mode controlled via env var: FLASK_DEBUG=1 or FLASK_ENV=development
    debug_env = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes') or os.environ.get('FLASK_ENV') == 'development'
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', '9912'))
    # When debugging, enable the reloader for convenience
    app.run(host=host, port=port, debug=debug_env, use_reloader=debug_env)
