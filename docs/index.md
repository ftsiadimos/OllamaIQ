---
title: Ollama Benchmark Docs
description: Documentation for the OllamaIQ benchmark application
---

# Ollama Benchmark Documentation

Welcome to the OllamaIQ documentation site. This repository provides an easy way to benchmark local Ollama models, measure prompt latency, and run lightweight smartness and code-skill checks.

## Features

- Discover models on an Ollama server (local or remote)
- Auto-filter models containing `etch` (configurable)
- Measure latency with repeatable runs and statistics
- Run heuristic smartness checks and sandboxed code-skill scoring
- View interactive charts and save historical results

## Quickstart

### Docker (recommended)

```bash
docker run -d \
  --name ollamaiq \
  -p 9912:9912 \
  ftsiadimos/ollamaiq
```

Then open `http://localhost:9912`.

### Docker Compose

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

```bash
docker-compose up -d
```

## Local development

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

Visit `http://127.0.0.1:9912`.

## GitHub Pages

This repository includes a `docs/` folder and a GitHub Actions workflow to publish documentation from that folder.

Once GitHub Pages is enabled for the repository, the site will be served from the `docs/` directory.

## Contributing

Contributions are welcome. Please open an issue or pull request and update documentation if you add new features.
