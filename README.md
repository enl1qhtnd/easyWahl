# easyWahl - Lokales Poll-Tool

Ein modernes, lokales Abstimmungssystem mit Python-Backend und Svelte-Frontend.

## Features

✅ **Admin-GUI** (PyQT)
- Server starten/stoppen
- Kandidaten verwalten (Hinzufügen, Bearbeiten, Löschen)
- Live-Ergebnisse anzeigen
- Wahl zurücksetzen
- Clients entsperren
- Excel-Export

✅ **Backend** (Python + FastAPI)
- REST-API für alle Operationen
- WebSocket für Live-Updates
- SQLite-Datenbank
- Client-Tracking (1 Stimme pro Runde)

✅ **Frontend** (Svelte)
- Moderne, responsive Voting-UI
- Live-Ergebnisse mit Chart.js
- Automatische Updates via WebSocket
- Client-ID basierend auf Browser-Fingerprint

## Projektstruktur

```
easyWahl/
├── backend/
│   ├── admin_gui.py          # Tkinter Admin-Panel
│   ├── api.py                # FastAPI Server
│   ├── database.py           # SQLite Manager
│   ├── models.py             # Pydantic Models
│   ├── websocket_manager.py  # WebSocket Handler
│   ├── requirements.txt      # Python Dependencies
│   └── poll.db               # SQLite DB (wird automatisch erstellt)
│
└── frontend/
    ├── src/
    │   ├── lib/
    │   │   ├── api.js        # API Client
    │   │   └── stores.js     # Svelte Stores
    │   ├── routes/
    │   │   ├── +page.svelte  # Voting Page
    │   │   └── results/
    │   │       └── +page.svelte  # Results Page
    │   └── app.css           # Global Styles
    └── package.json
```

## Installation & Start

### Voraussetzungen

- Python 3.10 oder höher
- Node.js 18 oder höher
- npm oder pnpm
- Docker (für Frontend)

### Backend einrichten

```bash
# Backend-Build herunterladen
wget https://github.com/enl1qhtnd/easyWahl/releases/download/v1.1.0/easyWahl-v1.1.0.exe

# Backend starten
./easyWahl-v1.1.0.exe
```

Die API läuft dann auf: **http://localhost:8000**

### Frontend einrichten

```bash
# easyWahl-Repo herunterladen
git clone https://github.com/enl1qhtnd/easyWahl.git
cd easyWahl

# Docker-Image bauen und Frontend starten
docker compose up -d
```

Das Frontend ist erreichbar unter: **http://localhost:9999**

## API-Dokumentation

Der Server bietet eine automatische API-Dokumentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Wichtige Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/candidates` | GET | Alle Kandidaten abrufen |
| `/api/candidates` | POST | Kandidat erstellen |
| `/api/candidates/{id}` | PUT | Kandidat bearbeiten |
| `/api/candidates/{id}` | DELETE | Kandidat löschen |
| `/api/vote` | POST | Stimme abgeben |
| `/api/vote/check` | POST | Prüfen ob Client abgestimmt hat |
| `/api/results` | GET | Aktuelle Ergebnisse |
| `/api/admin/reset` | POST | Alle Stimmen zurücksetzen |
| `/api/admin/unlock` | POST | Clients entsperren |
| `/api/export` | GET | Excel-Export |
| `/ws` | WebSocket | Live-Updates |


## Deployment

### Lokales Netzwerk

Server kann im lokalen Netzwerk freigegeben werden:

1. Backend startet standardmäßig auf `0.0.0.0:8000` (alle Interfaces)
2. Frontend-Dev-Server mit `--host` Flag läuft ebenfalls auf allen Interfaces
3. Clients im gleichen Netzwerk können zugreifen via:
   - `http://<SERVER-IP>:9999` (Voting)
   - `http://<SERVER-IP>:8000` (API)

## Building from source

### Python Build (Backend)

```bash
cd backend

# Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Admin-GUI starten
python admin_gui.py
```

### Development (Frontend)

```bash
cd frontend

# Dependencies installieren
npm install

# Development-Server starten
npm run dev
```
#
### made with ❤️ by @enl1qhtnd