"""
WebSocket-Manager für Live-Updates der Abstimmungsergebnisse
Sendet automatisch Updates an alle verbundenen Clients
"""

from fastapi import WebSocket
from typing import List, Set
import json
import asyncio


class WebSocketManager:
    def __init__(self):
        """Initialisiert den WebSocket-Manager"""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Nimmt eine neue WebSocket-Verbindung an"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        print(f"Client verbunden. Aktive Verbindungen: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Entfernt eine WebSocket-Verbindung"""
        async with self._lock:
            self.active_connections.discard(websocket)
        print(f"Client getrennt. Aktive Verbindungen: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Sendet eine Nachricht an alle verbundenen Clients
        Entfernt automatisch disconnected Clients
        """
        async with self._lock:
            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Fehler beim Senden an Client: {e}")
                    disconnected.add(connection)

            # Entferne disconnected clients
            self.active_connections -= disconnected

            if disconnected:
                print(f"{len(disconnected)} Clients entfernt. Aktive: {len(self.active_connections)}")

    async def broadcast_results(self, results: List[dict], total_votes: int):
        """
        Sendet Abstimmungsergebnisse an alle Clients
        """
        message = {
            "type": "results_update",
            "data": {
                "results": results,
                "total_votes": total_votes
            }
        }
        await self.broadcast(message)

    async def broadcast_vote_cast(self, candidate_id: int, candidate_name: str):
        """
        Benachrichtigt alle Clients über eine neue Stimme
        """
        message = {
            "type": "vote_cast",
            "data": {
                "candidate_id": candidate_id,
                "candidate_name": candidate_name
            }
        }
        await self.broadcast(message)

    async def broadcast_reset(self):
        """
        Benachrichtigt alle Clients über ein Reset
        """
        message = {
            "type": "reset",
            "data": {
                "message": "Die Abstimmung wurde zurückgesetzt"
            }
        }
        await self.broadcast(message)

    async def broadcast_unlock(self):
        """
        Benachrichtigt alle Clients über ein Unlock
        """
        message = {
            "type": "unlock",
            "data": {
                "message": "Neue Abstimmungsrunde gestartet - Sie können erneut abstimmen"
            }
        }
        await self.broadcast(message)

    async def broadcast_candidates_update(self):
        """
        Benachrichtigt alle Clients über eine Änderung der Kandidaten
        """
        message = {
            "type": "candidates_update",
            "data": {
                "message": "Kandidatenliste wurde aktualisiert"
            }
        }
        await self.broadcast(message)

    def get_active_connections_count(self) -> int:
        """Gibt die Anzahl aktiver Verbindungen zurück"""
        return len(self.active_connections)
