"""
SQLite Datenbank-Manager für das Poll-System
Verwaltet Kandidaten, Stimmen und Client-Status
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import threading


class Database:
    def __init__(self, db_path: str = "poll.db"):
        """Initialisiert die Datenbank und erstellt Tabellen"""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _get_connection(self):
        """Erstellt eine neue Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Erstellt die Datenbanktabellen falls nicht vorhanden"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Kandidaten-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Stimmen-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    client_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
                )
            """)

            # Client-Tabelle (verhindert Mehrfachabstimmung)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_identifier TEXT UNIQUE NOT NULL,
                    has_voted BOOLEAN DEFAULT FALSE,
                    last_vote_time TIMESTAMP
                )
            """)

            # Settings-Tabelle (für konfigurierbare Texte)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Setze Standard-Slogan falls nicht vorhanden
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                ("vote_slogan", "Deine Stimme zählt!")
            )

            conn.commit()
            conn.close()

    # === KANDIDATEN-VERWALTUNG ===

    def add_candidate(self, name: str, description: str = "") -> int:
        """Fügt einen neuen Kandidaten hinzu"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO candidates (name, description) VALUES (?, ?)",
                (name, description)
            )
            candidate_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return candidate_id

    def get_candidates(self) -> List[Dict]:
        """Gibt alle Kandidaten zurück"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def update_candidate(self, candidate_id: int, name: str, description: str = "") -> bool:
        """Aktualisiert einen Kandidaten"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE candidates SET name = ?, description = ? WHERE id = ?",
                (name, description, candidate_id)
            )
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0

    def delete_candidate(self, candidate_id: int) -> bool:
        """Löscht einen Kandidaten und alle seine Stimmen"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Erst Stimmen löschen
            cursor.execute("DELETE FROM votes WHERE candidate_id = ?", (candidate_id,))
            # Dann Kandidat löschen
            cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0

    # === VOTING ===

    def cast_vote(self, client_id: str, candidate_id: int) -> bool:
        """
        Gibt eine Stimme ab, wenn der Client noch nicht abgestimmt hat
        Returns: True wenn erfolgreich, False wenn bereits abgestimmt
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Prüfe ob Client bereits abgestimmt hat
            cursor.execute(
                "SELECT has_voted FROM clients WHERE client_identifier = ?",
                (client_id,)
            )
            result = cursor.fetchone()

            if result and result['has_voted']:
                conn.close()
                return False

            # Prüfe ob Kandidat existiert
            cursor.execute("SELECT id FROM candidates WHERE id = ?", (candidate_id,))
            if not cursor.fetchone():
                conn.close()
                return False

            # Stimme registrieren
            cursor.execute(
                "INSERT INTO votes (candidate_id, client_id) VALUES (?, ?)",
                (candidate_id, client_id)
            )

            # Client als "hat abgestimmt" markieren
            if result:
                cursor.execute(
                    "UPDATE clients SET has_voted = TRUE, last_vote_time = ? WHERE client_identifier = ?",
                    (datetime.now(), client_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO clients (client_identifier, has_voted, last_vote_time) VALUES (?, TRUE, ?)",
                    (client_id, datetime.now())
                )

            conn.commit()
            conn.close()
            return True

    def has_voted(self, client_id: str) -> bool:
        """Prüft ob ein Client bereits abgestimmt hat"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT has_voted FROM clients WHERE client_identifier = ?",
                (client_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return result['has_voted'] if result else False

    # === ERGEBNISSE ===

    def get_results(self) -> List[Dict]:
        """
        Gibt die Abstimmungsergebnisse zurück
        Format: [{candidate_id, candidate_name, description, vote_count}]
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id as candidate_id,
                    c.name as candidate_name,
                    c.description,
                    COUNT(v.id) as vote_count
                FROM candidates c
                LEFT JOIN votes v ON c.id = v.candidate_id
                GROUP BY c.id
                ORDER BY vote_count DESC, c.name
            """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def get_total_votes(self) -> int:
        """Gibt die Gesamtanzahl der Stimmen zurück"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM votes")
            result = cursor.fetchone()
            conn.close()
            return result['total'] if result else 0

    # === ADMIN-FUNKTIONEN ===

    def reset_votes(self):
        """Löscht alle Stimmen und setzt Client-Status zurück"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM votes")
            cursor.execute("UPDATE clients SET has_voted = FALSE, last_vote_time = NULL")
            conn.commit()
            conn.close()

    def unlock_clients(self):
        """
        Entsperrt alle Clients für eine neue Abstimmungsrunde
        WICHTIG: Stimmen bleiben erhalten, nur der Client-Status wird zurückgesetzt
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE clients SET has_voted = FALSE")
            conn.commit()
            conn.close()

    # === SETTINGS-VERWALTUNG ===

    def get_setting(self, key: str) -> Optional[str]:
        """Liest eine Einstellung aus der Datenbank"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()
            return result['value'] if result else None

    def set_setting(self, key: str, value: str):
        """Setzt eine Einstellung in der Datenbank"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            conn.close()

    def get_all_votes_detailed(self) -> List[Dict]:
        """
        Gibt alle Stimmen mit Details zurück (für Excel-Export)
        Format: [{vote_id, candidate_name, client_id, timestamp}]
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    v.id as vote_id,
                    c.name as candidate_name,
                    v.client_id,
                    v.timestamp
                FROM votes v
                JOIN candidates c ON v.candidate_id = c.id
                ORDER BY v.timestamp DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
