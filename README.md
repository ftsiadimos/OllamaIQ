<p align="center">
  <img src="mis/ollamaIQmain.png" width="120" alt="OllamaIQ Logo">
</p>



<h1 align="center">Ollama Benchmark</h1>

<p align="center">
  <strong>Ollama - Benchmark your local LLM models, finds models, measures per-prompt latency, and runs lightweight "smartness" and code-skill checks. <strong><br>
  Practical and easy to manage.
</p>


<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/flask-2.x-green.svg" alt="Flask 2.x">
  <img src="https://img.shields.io/badge/vue.js-3.x-brightgreen.svg" alt="Vue.js 3">
  <img src="https://img.shields.io/badge/license-GPL--3.0-orange.svg" alt="License GPL-3.0">
  <img src="https://img.shields.io/badge/SPDX-GPL--3.0--only-blue.svg" alt="SPDX GPL-3.0-only">
  <a href="https://hub.docker.com/r/ftsiadimos/ollamaiq"><img src="https://img.shields.io/docker/pulls/ftsiadimos/ollamaiq?style=flat-square&logo=docker" alt="Docker Pulls"></a>
</p>


---

## 📸 Screenshot

<div align="center">
  <div style="display:inline-flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;justify-content:center">
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid #eee;color:#333;font-weight:600">🧠 Smartness</span>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid #eee;color:#333;font-weight:600">💻 Code</span>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid #eee;color:#333;font-weight:600">⚡ Latency</span>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid #eee;color:#333;font-weight:600">📊 Charts</span>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid #eee;color:#333;font-weight:600">🗂️ History</span>
  </div>

  <a href="mis/image.png" target="_blank">
    <img src="mis/image.png" alt="Dashboard View" style="max-width:900px;width:100%;height:auto;border-radius:12px;border:1px solid #e6e6e6;box-shadow:0 10px 30px rgba(16,24,40,0.08)"/>
  </a>
  <div style="margin-top:8px;color:#6b6b6b;font-size:0.95rem"><em>Dashboard overview</em></div>
</div>

---

## 🔧 Features
- Discover models on an Ollama server (local or remote)
- Auto-filter models containing `etch` (configurable)
- Measure latency (repeatable runs) and compute simple statistics
- Heuristic "smartness" checks and basic code-skill scoring (sandboxed subprocess)
- Interactive web UI with charts, live progress, and saved run history
- Save / download past runs (SQLite)

---

## 🚀 Quickstart — Docker (recommended)
You can pull the officially released container from **Docker Hub** or the **GitHub Container Registry** (GHCR). Both images are built from the same codebase and kept in sync.

#### Pull from Docker Hub and run in one command

```bash
# Docker Hub (default)
docker run -d \
  --name ollamaiq \
  -p 9912:9912 \
  ftsiadimos/ollamaiq
```

#### Or pull the same image from GHCR

```bash
# GitHub Container Registry
docker run -d \
  --name ollamaiq-ghcr \
  -p 9912:9912 \
  ghcr.io/ftsiadimos/ollamaiq
```

Open http://localhost:9912


Or with Docker Compose (example):

```yaml
version: '3.8'
services:
  ollamaiq:
    # change to ghcr.io/ftsiadimos/ollamaiq if you prefer GHCR
    image: ftsiadimos/ollamaiq
    container_name: ollamaiq
    ports:
      - "9912:9912"
    restart: unless-stopped
```

Start it:

```bash
docker-compose up -d
```

The service listens on port **9912** by default.

---

## 💻 Local install (development)
1. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the web UI:

```bash
# Option A (run directly - dev):
python app.py

# Option B (Flask runner):
export FLASK_APP=app
flask run --host=127.0.0.1 --port=9912

# Option C (production-like using Gunicorn):
# gunicorn -w 1 --threads 4 -b 0.0.0.0:9912 app:app
```

Visit http://127.0.0.1:9912

Environment variables:
- `OLLAMA_DEFAULT_HOST` — default host shown in the UI (e.g. `http://localhost:11434`)
- `OLLAMA_API_KEY` — optional API key for cloud access
- `FLASK_RUN_HOST` / `FLASK_RUN_PORT` — override host/port when running Flask (default 9912)

---

## 🧪 About the tests
- **Code Generation:** accuracy of generated code for programming prompts
- **Smartness:** heuristic score across reasoning and puzzle-like prompts
- **Latency:** mean/median/min/max response times per prompt

See the **About** page in the UI for more details and tips for getting reproducible results.

---

## ⚠️ Security & Notes
- Code-skill tests run in a sandboxed subprocess with conservative limits; this reduces risk but is not a full sandbox. For production, consider stronger isolation (containers, dedicated sandboxes).
- The smartness scoring is heuristic and intended for quick comparisons, not formal benchmarking.

---

## 🤝 Contributing
Contributions are welcome! Please open an issue or pull request. If you add tests, update CI to run them.

---

## 📄 License
GPL-3.0 — see the repository LICENSE file for details.  
SPDX: `GPL-3.0-only`
