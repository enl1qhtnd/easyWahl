"""
Pydantic Models für API-Validierung und Serialisierung
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# === KANDIDATEN ===

class CandidateCreate(BaseModel):
    """Model für das Erstellen eines neuen Kandidaten"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)


class CandidateUpdate(BaseModel):
    """Model für das Aktualisieren eines Kandidaten"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)


class Candidate(BaseModel):
    """Model für einen Kandidaten (Response)"""
    id: int
    name: str
    description: Optional[str] = ""
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# === VOTING ===

class VoteRequest(BaseModel):
    """Model für eine Stimmabgabe"""
    client_id: str = Field(..., min_length=1, max_length=500)
    candidate_id: int = Field(..., gt=0)


class VoteCheckRequest(BaseModel):
    """Model für die Prüfung ob ein Client bereits abgestimmt hat"""
    client_id: str = Field(..., min_length=1, max_length=500)


class VoteCheckResponse(BaseModel):
    """Response für Vote-Check"""
    has_voted: bool


class VoteResponse(BaseModel):
    """Response nach erfolgreicher Stimmabgabe"""
    success: bool
    message: str


# === ERGEBNISSE ===

class VoteResult(BaseModel):
    """Model für Abstimmungsergebnisse"""
    candidate_id: int
    candidate_name: str
    description: Optional[str] = ""
    vote_count: int


class ResultsSummary(BaseModel):
    """Zusammenfassung aller Ergebnisse"""
    results: list[VoteResult]
    total_votes: int


# === ADMIN ===

class ResetResponse(BaseModel):
    """Response nach Reset-Operation"""
    success: bool
    message: str


class UnlockResponse(BaseModel):
    """Response nach Unlock-Operation"""
    success: bool
    message: str


class ServerStatus(BaseModel):
    """Server-Status Information"""
    running: bool
    total_candidates: int
    total_votes: int
    port: int = 8000


# === EXCEL EXPORT ===

class VoteDetailExport(BaseModel):
    """Detaillierte Vote-Information für Export"""
    vote_id: int
    candidate_name: str
    client_id: str
    timestamp: str
