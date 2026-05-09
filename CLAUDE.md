# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

QuickPoll is a local voting/polling tool with three layers:

1. **Backend** (`backend/`) — Python FastAPI server + PyQt6 Admin GUI
2. **Frontend** (`frontend/`) — SvelteKit SPA, built as static files into `backend/static/`
3. **Distribution** — PyInstaller bundles backend + pre-built static frontend into a single `.exe`

The frontend is always served by the FastAPI backend in production. The SvelteKit static adapter outputs directly to `backend/static/`, which FastAPI then serves via a catch-all route with SPA fallback.

## Development Commands

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # first time only
pip install -r requirements.txt                   # first time only

python admin_gui.py   # start full app (GUI + server on :8000)
python api.py         # start API server only (no GUI)
```

### Frontend

```bash
cd frontend
npm install          # first time only
npm run dev          # dev server on :5173 (proxies API to :8000)
npm run build        # builds static output into backend/static/
```

### Build Executable

```bash
# Linux/Mac
bash scripts/build_exe.sh

# Windows
powershell scripts/build_exe.ps1
```

The build script runs `npm run build` then PyInstaller with `backend/admin_gui.spec`. Output: `backend/dist/QuickPoll-v1.2.0[.exe]`.

## Key Data Flows

**Voting flow**: Browser → `POST /api/vote` (IP used as client ID server-side) → `database.py` checks `clients` table → on success, `WebSocketManager` broadcasts `vote_cast` + `results_update` to all connected clients.

**Admin unlock**: GUI button → `POST /api/admin/unlock` → DB sets `clients.has_voted = FALSE` (votes preserved) → WebSocket broadcasts `unlock` → all browser clients reload to `/`.

**Admin reset**: `POST /api/admin/reset` → deletes all rows from `votes` + resets client status → broadcasts `reset`.

## WebSocket Message Types

The `WebSocketManager` (`backend/websocket_manager.py`) broadcasts these event types to all connected browser clients:

| Type | Trigger |
|---|---|
| `initial_data` | Client connects |
| `results_update` | Any vote, reset, or candidate delete |
| `candidates_update` | Candidate added/edited/deleted |
| `vote_cast` | New vote submitted |
| `reset` | Admin resets all votes |
| `unlock` | Admin unlocks clients for new round |

## Frontend Routes

- `/` — Voting page (`+page.svelte`): candidate selection, one vote per IP per round
- `/results` — Live results with Chart.js bar chart
- `/live` — Presenter view (results, auto-updating via WebSocket)

Frontend state is managed via Svelte stores in `src/lib/stores.js`. All API calls go through `src/lib/api.js`, which dynamically resolves the API base URL (same host:8000 in production, `localhost:8000` in dev).

## Backend Module Responsibilities

- `api.py` — FastAPI app, all REST endpoints + WebSocket endpoint + static file serving
- `database.py` — `Database` class, all SQLite access (thread-safe via `threading.Lock`)
- `models.py` — Pydantic request/response models
- `websocket_manager.py` — `WebSocketManager`, fan-out broadcasts to all active WebSocket connections
- `admin_gui.py` — PyQt6 GUI, embeds the FastAPI server in a `QThread`

## Client Deduplication

One vote per IP per round. The `clients` table tracks `client_identifier` (IP address from `request.client.host`) and a `has_voted` boolean. "Unlock" resets `has_voted` without deleting vote records. "Reset" deletes all vote records and resets `has_voted`.

## Settings

The `settings` table stores key/value pairs. Currently only `vote_title` is used, editable via the "Titel ändern" button in the admin GUI or `POST /api/settings/vote-title`.
