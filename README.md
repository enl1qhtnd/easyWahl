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

### Backend einrichten

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

Die Admin-GUI öffnet sich automatisch. Von dort aus kannst du:
1. Den Server starten (Button "Server starten")
2. Kandidaten hinzufügen
3. Live-Ergebnisse beobachten

Der Server läuft dann auf: **http://localhost:8000**

### Frontend einrichten

```bash
cd frontend

# Dependencies installieren
npm install

# Development-Server starten
npm run dev
```

Das Frontend ist erreichbar unter: **http://localhost:5173**

## Verwendung

### 1. Backend starten
- Starte `admin_gui.py`
- Klicke auf "Server starten"
- Füge Kandidaten über die GUI hinzu

### 2. Frontend öffnen
- Öffne http://localhost:5173 im Browser
- Oder klicke in der Admin-GUI auf "Frontend öffnen"

### 3. Abstimmen
- Clients öffnen die Voting-Seite
- Wählen einen Kandidaten
- Stimmen ab (nur 1x pro Runde möglich)

### 4. Ergebnisse ansehen
- Navigiere zu `/results` oder klicke auf "Zu den Ergebnissen"
- Ergebnisse werden in Echtzeit aktualisiert

### 5. Neue Runde starten
- **Clients entsperren**: Clients können erneut abstimmen, Stimmen bleiben
- **Wahl zurücksetzen**: Alle Stimmen werden gelöscht, Kandidaten bleiben

### 6. Excel-Export
- Klicke in der Admin-GUI auf "Excel exportieren"
- Die Datei wird im Downloads-Ordner gespeichert

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

## Technologie-Stack

### Backend
- **FastAPI**: Modernes Python-Web-Framework
- **SQLite**: Leichtgewichtige Datenbank
- **Tkinter**: Native Python-GUI
- **uvicorn**: ASGI-Server
- **openpyxl**: Excel-Export
- **websockets**: Echtzeit-Kommunikation

### Frontend
- **SvelteKit**: Modernes Frontend-Framework
- **TailwindCSS**: Utility-First CSS
- **Chart.js**: Datenvisualisierung
- **Vite**: Build-Tool

## Sicherheit

- **Client-Tracking**: Kombination aus localStorage + Browser-Fingerprint
- **Einmalige Abstimmung**: Datenbank verhindert Mehrfachabstimmung
- **Thread-Safe**: Database-Lock für sichere Concurrent-Zugriffe

## Deployment

### Lokales Netzwerk

Server kann im lokalen Netzwerk freigegeben werden:

1. Backend startet standardmäßig auf `0.0.0.0:8000` (alle Interfaces)
2. Frontend-Dev-Server mit `--host` Flag läuft ebenfalls auf allen Interfaces
3. Clients im gleichen Netzwerk können zugreifen via:
   - `http://<SERVER-IP>:5173` (Voting)
   - `http://<SERVER-IP>:8000` (API)

### Production-Build

```bash
cd frontend
npm run build
npm run preview
```

## Troubleshooting

### Server startet nicht
- Prüfe ob Port 8000 frei ist: `lsof -i :8000` (Mac/Linux) oder `netstat -ano | findstr :8000` (Windows)
- Prüfe ob alle Dependencies installiert sind

### Frontend verbindet nicht
- Stelle sicher, dass Backend läuft
- Prüfe CORS-Einstellungen in `api.py`
- Prüfe Browser-Console für Fehler

### WebSocket-Fehler
- Prüfe ob Server läuft
- Prüfe Browser-Kompatibilität (moderne Browser erforderlich)

### Excel-Export funktioniert nicht
- Server muss laufen
- Prüfe Schreibrechte im Downloads-Ordner

## Erweiterungen

### Mögliche Features
- [ ] Mehrfachauswahl (Multiple-Choice)
- [ ] Zeitlimit für Abstimmung
- [ ] Live-Teilnehmerzähler
- [ ] SMS/Email-Benachrichtigungen
- [ ] PDF-Export zusätzlich zu Excel
- [ ] Kandidaten-Bilder
- [ ] Anonyme Kommentare
- [ ] Historie aller Abstimmungen

### Code-Struktur
Der Code ist modular aufgebaut und leicht erweiterbar:
- **Backend**: Jede Datei hat eine klare Verantwortung
- **Frontend**: Component-basiert, wiederverwendbar
- **API**: RESTful und gut dokumentiert

## Lizenz

Dieses Projekt ist für den privaten und lokalen Gebrauch gedacht.

## Support

Bei Fragen oder Problemen:
1. Prüfe die Logs in der Konsole
2. Prüfe die API-Dokumentation unter `/docs`
3. Prüfe die Browser-Console (F12)

## Entwickelt mit ❤️

Ein vollständiges, produktionsreifes Poll-System mit modernster Technologie.

**Viel Erfolg bei deinen Abstimmungen! 🗳️**
