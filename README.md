# Ollama IQ Model Tester ✅

A small Python app that queries an Ollama server, finds models (defaults to those containing `etch`), measures per-prompt latency, and runs lightweight "smartness" and code-skill checks. It provides a CLI and a modern, cozy Flask web UI with persistent run history and downloadable JSON results.

---

## What's new ✨
- Redesigned UI with a warm, modern look and improved spacing for readability
- Theme options: **Light**, **Dark**, and **Warm Dark** (switch in the header)
- New **About** page describing the tests, developer, and tech stack
- Cleaner footer and improved accessibility and responsiveness

---

## Features 🔧
- Discover models on an Ollama server (local or remote)
- Auto-filter models containing `etch` (configurable)
- Measure latency (repeatable runs) and compute simple statistics
- Heuristic "smartness" checks and basic code-skill scoring (sandboxed subprocess)
- Interactive web UI with charts, live progress, and saved run history
- Save / download past runs (SQLite)

---

## Quickstart — Docker (recommended)
Run the official image exposing the default app port (9912):

```bash
# Pull and run in one command
docker run -d \
  --name ollamaiq \
  -p 9912:9912 \
  ftsiadimos/ollamaiq

# Open http://localhost:9912
```

Or with Docker Compose (example):

```yaml
version: '3.8'
services:
  ollamaiq:
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

## Local install (development)
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

## About the tests 🧪
- **Code Generation:** accuracy of generated code for programming prompts
- **Smartness:** heuristic score across reasoning and puzzle-like prompts
- **Latency:** mean/median/min/max response times per prompt

See the **About** page in the UI for more details and tips for getting reproducible results.

---

## Security & Notes ⚠️
- Code-skill tests run in a sandboxed subprocess with conservative limits; this reduces risk but is not a full sandbox. For production, consider stronger isolation (containers, dedicated sandboxes).
- The smartness scoring is heuristic and intended for quick comparisons, not formal benchmarking.

---

## Contributing
Contributions are welcome! Please open an issue or pull request. If you add tests, update CI to run them.

---

## License
MIT — see the repository LICENSE file for details.
