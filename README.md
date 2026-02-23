# DraftForge Repair Agent

DraftForge Repair Agent is an AI-powered code debugging and repair assistant built for the AkashML Hackathon (winning project).

It accepts broken code + error context, identifies probable root causes, and generates patch-ready fixes with explanations.

## Core Capabilities

- Bug triage with severity and root-cause hypotheses
- Automated patch generation (unified diff style)
- Optional OpenAI-compatible AkashML model integration
- Fallback deterministic repair mode for offline demos
- Lightweight web studio for fast live demos
- Batch repair runner for processing multiple failures in one pass

## Stack

- FastAPI backend
- Static web studio (HTML/CSS/JS)
- `httpx` model client (OpenAI-compatible endpoint)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn apps.api.main:app --reload --port 8010
```

Open `apps/studio/index.html` and point API URL to `http://localhost:8010`.

## Endpoints

- `GET /health`
- `POST /api/v1/analyze`
- `POST /api/v1/repair`

## Batch Mode

Run repair jobs from JSONL input:

```bash
python3 scripts/batch_repair.py \
  --api-url http://localhost:8010 \
  --input ./jobs.jsonl \
  --output ./results.jsonl
```

Sample input row (`jobs.jsonl`):

```json
{"id":"job-1","language":"python","strategy":"minimal_patch","error_log":"TypeError: ...","code":"def foo(): ..."}
```

## AkashML Configuration

Set these in `.env` to run with AkashML-hosted models:

- `AKASH_BASE_URL`
- `AKASH_API_KEY`
- `AKASH_MODEL`

## Beyond Hackathon

See `docs/ROADMAP.md` for productionization milestones.
