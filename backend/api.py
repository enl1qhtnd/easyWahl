"""
FastAPI Server für das Poll-System
Stellt REST-API und WebSocket-Endpoints bereit
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import uvicorn
from datetime import datetime
from openpyxl import Workbook
import os
import tempfile

from database import Database
from models import (
    Candidate, CandidateCreate, CandidateUpdate,
    VoteRequest, VoteResponse, VoteCheckRequest, VoteCheckResponse,
    VoteResult, ResultsSummary, ResetResponse, UnlockResponse,
    ServerStatus
)
from websocket_manager import WebSocketManager


# === INITIALISIERUNG ===

app = FastAPI(
    title="easyWahl Poll API",
    description="API für lokales Abstimmungssystem",
    version="1.0.0"
)

# CORS aktivieren (erlaubt Frontend-Zugriff)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion spezifische Origins angeben
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globale Instanzen
db = Database()
ws_manager = WebSocketManager()


# === KANDIDATEN-ENDPOINTS ===

@app.get("/api/candidates", response_model=List[Candidate], tags=["Kandidaten"])
async def get_candidates():
    """Gibt alle Kandidaten zurück"""
    candidates = db.get_candidates()
    return candidates


@app.post("/api/candidates", response_model=Candidate, tags=["Kandidaten"])
async def create_candidate(candidate: CandidateCreate):
    """Erstellt einen neuen Kandidaten"""
    candidate_id = db.add_candidate(candidate.name, candidate.description)

    # Benachrichtige WebSocket-Clients
    await ws_manager.broadcast_candidates_update()

    # Hole den erstellten Kandidaten
    candidates = db.get_candidates()
    created = next((c for c in candidates if c['id'] == candidate_id), None)

    if not created:
        raise HTTPException(status_code=500, detail="Kandidat konnte nicht erstellt werden")

    return created


@app.put("/api/candidates/{candidate_id}", response_model=Candidate, tags=["Kandidaten"])
async def update_candidate(candidate_id: int, candidate: CandidateUpdate):
    """Aktualisiert einen Kandidaten"""
    success = db.update_candidate(candidate_id, candidate.name, candidate.description)

    if not success:
        raise HTTPException(status_code=404, detail="Kandidat nicht gefunden")

    # Benachrichtige WebSocket-Clients
    await ws_manager.broadcast_candidates_update()

    # Hole den aktualisierten Kandidaten
    candidates = db.get_candidates()
    updated = next((c for c in candidates if c['id'] == candidate_id), None)

    return updated


@app.delete("/api/candidates/{candidate_id}", tags=["Kandidaten"])
async def delete_candidate(candidate_id: int):
    """Löscht einen Kandidaten und alle seine Stimmen"""
    success = db.delete_candidate(candidate_id)

    if not success:
        raise HTTPException(status_code=404, detail="Kandidat nicht gefunden")

    # Benachrichtige WebSocket-Clients
    await ws_manager.broadcast_candidates_update()

    # Sende aktualisierte Ergebnisse
    results = db.get_results()
    total_votes = db.get_total_votes()
    await ws_manager.broadcast_results(results, total_votes)

    return {"success": True, "message": "Kandidat gelöscht"}


# === VOTING-ENDPOINTS ===

@app.post("/api/vote", response_model=VoteResponse, tags=["Voting"])
async def cast_vote(vote: VoteRequest, request: Request):
    """
    Gibt eine Stimme ab
    Jeder Client kann nur einmal pro Runde abstimmen
    Verwendet IP-Adresse als Client-Identifier
    """
    # Extrahiere IP-Adresse aus dem Request
    client_ip = request.client.host
    success = db.cast_vote(client_ip, vote.candidate_id)

    if not success:
        return VoteResponse(
            success=False,
            message="Sie haben bereits abgestimmt oder der Kandidat existiert nicht"
        )

    # Hole Kandidatenname für Broadcast
    candidates = db.get_candidates()
    candidate = next((c for c in candidates if c['id'] == vote.candidate_id), None)

    if candidate:
        await ws_manager.broadcast_vote_cast(vote.candidate_id, candidate['name'])

    # Sende aktualisierte Ergebnisse
    results = db.get_results()
    total_votes = db.get_total_votes()
    await ws_manager.broadcast_results(results, total_votes)

    return VoteResponse(
        success=True,
        message="Ihre Stimme wurde erfolgreich registriert"
    )


@app.post("/api/vote/check", response_model=VoteCheckResponse, tags=["Voting"])
async def check_vote_status(request: VoteCheckRequest, fastapi_request: Request):
    """Prüft ob ein Client bereits abgestimmt hat"""
    # Extrahiere IP-Adresse aus dem Request
    client_ip = fastapi_request.client.host
    has_voted = db.has_voted(client_ip)
    return VoteCheckResponse(has_voted=has_voted)


# === ERGEBNIS-ENDPOINTS ===

@app.get("/api/results", response_model=ResultsSummary, tags=["Ergebnisse"])
async def get_results():
    """Gibt die aktuellen Abstimmungsergebnisse zurück"""
    results = db.get_results()
    total_votes = db.get_total_votes()

    vote_results = [
        VoteResult(
            candidate_id=r['candidate_id'],
            candidate_name=r['candidate_name'],
            description=r.get('description', ''),
            vote_count=r['vote_count']
        )
        for r in results
    ]

    return ResultsSummary(
        results=vote_results,
        total_votes=total_votes
    )


# === ADMIN-ENDPOINTS ===

@app.post("/api/admin/reset", response_model=ResetResponse, tags=["Admin"])
async def reset_votes():
    """
    Setzt alle Stimmen zurück
    Kandidaten bleiben erhalten, alle Votes werden gelöscht
    """
    db.reset_votes()

    # Benachrichtige alle Clients
    await ws_manager.broadcast_reset()

    # Sende leere Ergebnisse
    results = db.get_results()
    total_votes = db.get_total_votes()
    await ws_manager.broadcast_results(results, total_votes)

    return ResetResponse(
        success=True,
        message="Alle Stimmen wurden zurückgesetzt"
    )


@app.post("/api/admin/unlock", response_model=UnlockResponse, tags=["Admin"])
async def unlock_clients():
    """
    Entsperrt alle Clients für eine neue Abstimmungsrunde
    Votes bleiben erhalten
    """
    db.unlock_clients()

    # Benachrichtige alle Clients
    await ws_manager.broadcast_unlock()

    return UnlockResponse(
        success=True,
        message="Alle Clients wurden entsperrt"
    )


@app.get("/api/admin/status", response_model=ServerStatus, tags=["Admin"])
async def get_server_status():
    """Gibt den aktuellen Server-Status zurück"""
    candidates = db.get_candidates()
    total_votes = db.get_total_votes()

    return ServerStatus(
        running=True,
        total_candidates=len(candidates),
        total_votes=total_votes,
        port=8000
    )


# === SETTINGS-ENDPOINTS ===

@app.get("/api/settings/vote-title", tags=["Settings"])
async def get_vote_title():
    """Gibt den aktuellen Wahl-title zurück"""
    title = db.get_setting("vote_title")
    return {"title": title or "made with ♥ by @enl1qhtnd"}


@app.post("/api/settings/vote-title", tags=["Settings"])
async def set_vote_title(title: str):
    """Setzt den Wahl-title"""
    if not title or len(title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")

    db.set_setting("vote_title", title.strip())
    return {"success": True, "title": title.strip()}


# === EXCEL-EXPORT ===

@app.get("/api/export", tags=["Export"])
async def export_results():
    """
    Exportiert die Abstimmungsergebnisse als Excel-Datei
    """
    # Erstelle Workbook
    wb = Workbook()

    # Sheet 1: Zusammenfassung
    ws_summary = wb.active
    ws_summary.title = "Zusammenfassung"
    ws_summary.append(["Kandidat", "Beschreibung", "Stimmen"])

    results = db.get_results()
    for result in results:
        ws_summary.append([
            result['candidate_name'],
            result.get('description', ''),
            result['vote_count']
        ])

    # Sheet 2: Detaillierte Votes
    ws_details = wb.create_sheet("Detaillierte Votes")
    ws_details.append(["Vote ID", "Kandidat", "Client ID", "Zeitstempel"])

    votes = db.get_all_votes_detailed()
    for vote in votes:
        ws_details.append([
            vote['vote_id'],
            vote['candidate_name'],
            vote['client_id'],
            vote['timestamp']
        ])

    # Speichere Datei
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"abstimmung_ergebnisse_{timestamp}.xlsx"
    
    # Verwende temporäres Verzeichnis (Windows-kompatibel)
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)

    wb.save(filepath)

    # Sende Datei
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


# === WEBSOCKET ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket-Endpoint für Live-Updates
    Clients erhalten automatisch Updates bei Änderungen
    """
    await ws_manager.connect(websocket)

    try:
        # Sende initiale Daten
        results = db.get_results()
        total_votes = db.get_total_votes()
        await websocket.send_json({
            "type": "initial_data",
            "data": {
                "results": results,
                "total_votes": total_votes
            }
        })

        # Halte Verbindung offen
        while True:
            # Warte auf Client-Nachrichten (optional)
            data = await websocket.receive_text()
            # Könnte für Ping/Pong verwendet werden

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Fehler: {e}")
        await ws_manager.disconnect(websocket)


# === HEALTH CHECK ===

@app.get("/", tags=["System"])
async def root():
    """Health-Check Endpoint"""
    return {
        "status": "online",
        "service": "easyWahl Poll API",
        "version": "1.0.0"
    }


# === SERVER-FUNKTION (für GUI) ===

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Startet den FastAPI-Server
    Wird von der Admin-GUI aufgerufen
    """
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Direkter Start für Testing
    run_server()
