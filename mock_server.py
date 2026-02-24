#!/usr/bin/env python3
"""
LeanDeep Mock API Server — Realistic fixture data for all 11 endpoints.

Start:  python3 mock_server.py [--port 8420]

Scenario switching via header X-Mock-Scenario or query ?scenario=
  - therapy_repair (default): Therapiesitzung mit Repair-Verlauf
  - conflict_escalation: Paarkonflikt mit Eskalation
  - single_text: Fuer /v1/analyze, 3 Marker-Detektionen
"""

from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

_start_time = time.time()

app = FastAPI(
    title="LeanDeep Mock API",
    version="5.1-LD5-mock",
    description="Mock server for frontend development — no engine, no markers_rated, no ruamel.yaml.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scenario(request: Request) -> str:
    return (
        request.headers.get("X-Mock-Scenario")
        or request.query_params.get("scenario")
        or "therapy_repair"
    )


def _meta(text_length: int, n_markers: int, layers: list[str], ms: float = 1.2) -> dict:
    return {
        "processing_ms": ms,
        "version": "5.1-LD5",
        "text_length": text_length,
        "markers_detected": n_markers,
        "layers_scanned": layers,
    }


# ---------------------------------------------------------------------------
# 20 Sample Markers (8 ATO, 6 SEM, 4 CLU, 2 MEMA)
# ---------------------------------------------------------------------------

SAMPLE_MARKERS: list[dict[str, Any]] = [
    # --- ATO (8) ---
    {
        "id": "ATO_HESITATION", "layer": "ATO", "lang": "de",
        "description": "Zoegerungsmarker: Fuellwoerter, Satzabbrueche, Unsicherheitssignale",
        "frame": {"valence": -0.1, "arousal": 0.2, "dominance": -0.2},
        "patterns": [{"type": "regex", "value": r"\b(aehm|hmm|also|naja)\b"}],
        "examples": {"positive": ["Aehm, ich weiss nicht so recht..."], "negative": ["Ich bin mir sicher."]},
        "tags": ["hesitation", "filler"], "rating": 1, "family": "uncertainty", "multiplier": 1.0,
    },
    {
        "id": "ATO_SELF_BLAME", "layer": "ATO", "lang": "de",
        "description": "Selbstbeschuldigung: Uebernahme von Schuld ohne externe Ursache",
        "frame": {"valence": -0.5, "arousal": 0.3, "dominance": -0.4},
        "patterns": [{"type": "regex", "value": r"\b(meine schuld|ich bin schuld|liegt an mir)\b"}],
        "examples": {"positive": ["Das ist alles meine Schuld."], "negative": ["Du bist schuld."]},
        "tags": ["self-blame", "guilt"], "rating": 1, "family": "self_attribution", "multiplier": 1.2,
    },
    {
        "id": "ATO_REPAIR_BID", "layer": "ATO", "lang": "de",
        "description": "Reparaturversuch: Aktiver Versuch, Beziehungsriss zu kitten",
        "frame": {"valence": 0.4, "arousal": 0.3, "dominance": 0.2},
        "patterns": [{"type": "regex", "value": r"\b(tut mir leid|entschuldigung|verzeih)\b"}],
        "examples": {"positive": ["Es tut mir leid, das wollte ich nicht."], "negative": ["Mir egal."]},
        "tags": ["repair", "apology"], "rating": 1, "family": "repair", "multiplier": 1.3,
    },
    {
        "id": "ATO_CONTEMPT", "layer": "ATO", "lang": "de",
        "description": "Verachtungssignal: Abwertung, Ueberlegenheit, Sarkasmus",
        "frame": {"valence": -0.6, "arousal": 0.5, "dominance": 0.5},
        "patterns": [{"type": "regex", "value": r"\b(typisch|laecherlich|wie immer)\b"}],
        "examples": {"positive": ["Typisch, das war ja klar."], "negative": ["Das ueberrascht mich."]},
        "tags": ["contempt", "gottman"], "rating": 1, "family": "contempt", "multiplier": 1.5,
    },
    {
        "id": "ATO_STONEWALLING", "layer": "ATO", "lang": "de",
        "description": "Mauern: Kommunikationsverweigerung, emotionaler Rueckzug",
        "frame": {"valence": -0.3, "arousal": -0.4, "dominance": -0.1},
        "patterns": [{"type": "regex", "value": r"\b(keine lust|mir egal|lass mich)\b"}],
        "examples": {"positive": ["Mir egal, mach was du willst."], "negative": ["Lass uns reden."]},
        "tags": ["stonewalling", "withdrawal"], "rating": 1, "family": "avoidance", "multiplier": 1.4,
    },
    {
        "id": "ATO_VALIDATION", "layer": "ATO", "lang": "de",
        "description": "Validierung: Anerkennung der Gefuehle des Gegenueber",
        "frame": {"valence": 0.5, "arousal": 0.1, "dominance": 0.0},
        "patterns": [{"type": "regex", "value": r"\b(ich verstehe|das ist nachvollziehbar|deine gefuehle)\b"}],
        "examples": {"positive": ["Ich verstehe, dass dich das verletzt."], "negative": ["Stell dich nicht so an."]},
        "tags": ["validation", "empathy"], "rating": 1, "family": "empathy", "multiplier": 1.1,
    },
    {
        "id": "ATO_DEFLECTION", "layer": "ATO", "lang": "de",
        "description": "Ablenkung: Themenwechsel zur Konfliktvermeidung",
        "frame": {"valence": -0.1, "arousal": 0.1, "dominance": 0.2},
        "patterns": [{"type": "regex", "value": r"\b(aber das ist|davon abgesehen|anderes thema)\b"}],
        "examples": {"positive": ["Aber das ist jetzt nicht das Thema."], "negative": ["Bleiben wir beim Thema."]},
        "tags": ["deflection", "avoidance"], "rating": 2, "family": "avoidance", "multiplier": 1.0,
    },
    {
        "id": "ATO_DEMAND", "layer": "ATO", "lang": "de",
        "description": "Forderung: Direktive Aufforderung mit Druckaufbau",
        "frame": {"valence": -0.3, "arousal": 0.6, "dominance": 0.6},
        "patterns": [{"type": "regex", "value": r"\b(du musst|ich verlange|sofort)\b"}],
        "examples": {"positive": ["Du musst dich aendern!"], "negative": ["Koenntest du vielleicht..."]},
        "tags": ["demand", "pressure"], "rating": 1, "family": "control", "multiplier": 1.3,
    },
    # --- SEM (6) ---
    {
        "id": "SEM_GUILT_TRIP", "layer": "SEM", "lang": "de",
        "description": "Schuldgefuehle erzeugen: Kombination aus Vorwurf und emotionalem Druck",
        "frame": {"valence": -0.5, "arousal": 0.4, "dominance": 0.3},
        "patterns": [{"type": "regex", "value": r"\b(wegen dir|deinetwegen|du machst mich)\b"}],
        "examples": {"positive": ["Wegen dir bin ich so unglücklich."], "negative": ["Ich fuehle mich traurig."]},
        "tags": ["guilt_trip", "manipulation"], "rating": 1, "family": "manipulation", "multiplier": 1.4,
        "composed_of": {"require": ["ATO_SELF_BLAME"]},
    },
    {
        "id": "SEM_EMOTIONAL_FLOODING", "layer": "SEM", "lang": "de",
        "description": "Emotionale Ueberflutung: Ueberwaeltigung durch Gefuehlsintensitaet",
        "frame": {"valence": -0.4, "arousal": 0.8, "dominance": -0.5},
        "patterns": [{"type": "regex", "value": r"\b(ich kann nicht mehr|alles zu viel|ueberfordert)\b"}],
        "examples": {"positive": ["Ich kann nicht mehr, alles ist zu viel!"], "negative": ["Ich komme klar."]},
        "tags": ["flooding", "overwhelm"], "rating": 1, "family": "dysregulation", "multiplier": 1.2,
    },
    {
        "id": "SEM_REPAIR_ATTEMPT", "layer": "SEM", "lang": "de",
        "description": "Strukturierter Reparaturversuch mit Verantwortungsuebernahme",
        "frame": {"valence": 0.5, "arousal": 0.2, "dominance": 0.1},
        "patterns": [{"type": "regex", "value": r"\b(ich moechte.*verstehen|lass uns.*reden)\b"}],
        "examples": {"positive": ["Ich moechte verstehen, was dich verletzt hat."], "negative": ["Vergiss es einfach."]},
        "tags": ["repair", "structured"], "rating": 1, "family": "repair", "multiplier": 1.3,
        "composed_of": {"require": ["ATO_REPAIR_BID", "ATO_VALIDATION"]},
    },
    {
        "id": "SEM_DEMAND_WITHDRAW", "layer": "SEM", "lang": "de",
        "description": "Forderung-Rueckzug-Muster: Ein Partner fordert, der andere mauert",
        "frame": {"valence": -0.4, "arousal": 0.3, "dominance": 0.0},
        "patterns": [{"type": "regex", "value": r"\b(red endlich|sprich mit mir.*egal)\b"}],
        "examples": {"positive": ["Red endlich mit mir! — Mir egal."], "negative": ["Lass uns in Ruhe reden."]},
        "tags": ["demand_withdraw", "gottman"], "rating": 1, "family": "conflict_pattern", "multiplier": 1.5,
        "composed_of": {"require": ["ATO_DEMAND", "ATO_STONEWALLING"]},
    },
    {
        "id": "SEM_GASLIGHTING", "layer": "SEM", "lang": "de",
        "description": "Gaslighting: Realitaetsverzerrung und Infragestellen der Wahrnehmung",
        "frame": {"valence": -0.7, "arousal": 0.3, "dominance": 0.7},
        "patterns": [{"type": "regex", "value": r"\b(das bildest du dir ein|das war nie so|du uebertreibst)\b"}],
        "examples": {"positive": ["Das bildest du dir ein, das war nie so."], "negative": ["Ich erinnere mich anders."]},
        "tags": ["gaslighting", "manipulation"], "rating": 1, "family": "manipulation", "multiplier": 1.8,
    },
    {
        "id": "SEM_SECURE_BASE", "layer": "SEM", "lang": "de",
        "description": "Sichere-Basis-Signal: Verfuegbarkeit und emotionale Sicherheit",
        "frame": {"valence": 0.6, "arousal": 0.0, "dominance": 0.1},
        "patterns": [{"type": "regex", "value": r"\b(ich bin da|du kannst.*zaehlen|immer fuer dich)\b"}],
        "examples": {"positive": ["Ich bin da fuer dich, egal was passiert."], "negative": ["Kuemmer dich selbst."]},
        "tags": ["secure_base", "attachment"], "rating": 1, "family": "attachment", "multiplier": 1.2,
    },
    # --- CLU (4) ---
    {
        "id": "CLU_ESCALATION_SPIRAL", "layer": "CLU", "lang": "de",
        "description": "Eskalationsspirale: Mehrere aufeinander aufbauende Konfliktsignale",
        "frame": {"valence": -0.6, "arousal": 0.7, "dominance": 0.2},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["escalation", "spiral"], "rating": 1, "family": "conflict_dynamics", "multiplier": 1.6,
        "composed_of": {"require": ["ATO_CONTEMPT", "ATO_DEMAND", "SEM_GUILT_TRIP"]},
    },
    {
        "id": "CLU_REPAIR_SEQUENCE", "layer": "CLU", "lang": "de",
        "description": "Reparatursequenz: Aufeinanderfolge von Repair-Markern ueber mehrere Nachrichten",
        "frame": {"valence": 0.5, "arousal": 0.2, "dominance": 0.1},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["repair", "sequence"], "rating": 1, "family": "repair_dynamics", "multiplier": 1.4,
        "composed_of": {"require": ["ATO_REPAIR_BID", "SEM_REPAIR_ATTEMPT"]},
    },
    {
        "id": "CLU_WITHDRAWAL_PATTERN", "layer": "CLU", "lang": "de",
        "description": "Rueckzugsmuster: Wiederholtes Mauern und Deflection ueber die Sitzung",
        "frame": {"valence": -0.3, "arousal": -0.3, "dominance": -0.2},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["withdrawal", "pattern"], "rating": 1, "family": "avoidance_dynamics", "multiplier": 1.3,
        "composed_of": {"require": ["ATO_STONEWALLING", "ATO_DEFLECTION"]},
    },
    {
        "id": "CLU_SECRET_BONDING", "layer": "CLU", "lang": "de",
        "description": "Geheime Verbundenheit: Verdeckte Allianzbildung ueber Selbstoffenbarung",
        "frame": {"valence": 0.3, "arousal": 0.2, "dominance": -0.1},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["bonding", "self_disclosure"], "rating": 2, "family": "bonding", "multiplier": 1.1,
        "composed_of": {"require": ["ATO_VALIDATION", "SEM_SECURE_BASE"]},
    },
    # --- MEMA (2) ---
    {
        "id": "MEMA_RELATIONSHIP_CRISIS", "layer": "MEMA", "lang": "de",
        "description": "Beziehungskrise: Meta-Diagnose basierend auf Eskalation + Withdrawal",
        "frame": {"valence": -0.7, "arousal": 0.5, "dominance": -0.1},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["crisis", "meta"], "rating": 1, "family": "meta_diagnosis", "multiplier": 2.0,
        "composed_of": {"require": ["CLU_ESCALATION_SPIRAL", "CLU_WITHDRAWAL_PATTERN"]},
    },
    {
        "id": "MEMA_THERAPEUTIC_PROGRESS", "layer": "MEMA", "lang": "de",
        "description": "Therapeutischer Fortschritt: Repair dominiert, Eskalation nimmt ab",
        "frame": {"valence": 0.6, "arousal": 0.1, "dominance": 0.2},
        "patterns": [], "examples": {"positive": [], "negative": []},
        "tags": ["progress", "meta"], "rating": 1, "family": "meta_diagnosis", "multiplier": 1.8,
        "composed_of": {"require": ["CLU_REPAIR_SEQUENCE"]},
    },
]

_markers_by_id = {m["id"]: m for m in SAMPLE_MARKERS}

# ---------------------------------------------------------------------------
# Scenario Fixtures
# ---------------------------------------------------------------------------

THERAPY_REPAIR_MESSAGES = [
    {"role": "client", "text": "Ich weiss nicht... aehm, es ist alles so schwer gerade."},
    {"role": "therapist", "text": "Ich verstehe, dass dich das belastet. Magst du mir mehr erzaehlen?"},
    {"role": "client", "text": "Es ist meine Schuld, ich haette frueher etwas sagen muessen."},
    {"role": "therapist", "text": "Das ist nachvollziehbar, aber du bist nicht allein schuld. Lass uns das gemeinsam anschauen."},
    {"role": "client", "text": "Es tut mir leid, dass ich letzte Woche so ausgerastet bin."},
    {"role": "therapist", "text": "Das war mutig. Ich bin da fuer dich, egal was passiert."},
]

CONFLICT_ESCALATION_MESSAGES = [
    {"role": "A", "text": "Typisch, das war ja wieder klar mit dir."},
    {"role": "B", "text": "Mir egal, mach was du willst."},
    {"role": "A", "text": "Wegen dir bin ich so unglücklich! Du musst dich endlich aendern!"},
    {"role": "B", "text": "Lass mich in Ruhe, ich kann nicht mehr."},
    {"role": "A", "text": "Das bildest du dir ein, das war nie so schlimm."},
    {"role": "B", "text": "Ich kann nicht mehr, alles ist zu viel gerade."},
]

# VAD trajectories (6 points per scenario, handcrafted for visible chart trends)
VAD_THERAPY_REPAIR = [
    {"valence": -0.3, "arousal": 0.4, "dominance": -0.2},
    {"valence": 0.2, "arousal": 0.1, "dominance": 0.1},
    {"valence": -0.5, "arousal": 0.5, "dominance": -0.4},
    {"valence": 0.1, "arousal": 0.2, "dominance": 0.0},
    {"valence": 0.3, "arousal": 0.3, "dominance": 0.1},
    {"valence": 0.5, "arousal": 0.1, "dominance": 0.2},
]

VAD_CONFLICT_ESCALATION = [
    {"valence": -0.4, "arousal": 0.5, "dominance": 0.4},
    {"valence": -0.2, "arousal": -0.3, "dominance": -0.1},
    {"valence": -0.7, "arousal": 0.8, "dominance": 0.5},
    {"valence": -0.4, "arousal": -0.4, "dominance": -0.3},
    {"valence": -0.8, "arousal": 0.4, "dominance": 0.7},
    {"valence": -0.6, "arousal": 0.7, "dominance": -0.5},
]

# Prosody features (6 emotions from 17 structural features)
def _prosody(caps: float, excl: float, elong: float, short: bool) -> dict:
    return {
        "caps_ratio": caps, "exclamation_count": excl, "question_count": 0,
        "ellipsis_count": 1 if elong > 0 else 0, "emoji_count": 0,
        "word_count": 12, "avg_word_length": 4.5, "sentence_count": 2,
        "avg_sentence_length": 6, "repetition_ratio": 0.1,
        "punctuation_density": 0.08, "uppercase_words": int(caps * 12),
        "short_message": short, "elongation_count": elong,
        "stutter_count": 0, "hedging_count": 1 if not short else 0,
        "intensifier_count": 0,
    }


def _emotions_therapy() -> list[dict]:
    return [
        {"scores": {"SADNESS": 0.45, "ANXIETY": 0.30, "ANGER": 0.05, "JOY": 0.05, "SURPRISE": 0.05, "DISGUST": 0.10},
         "dominant": "SADNESS", "dominant_score": 0.45, "prosody": _prosody(0.0, 0, 1, False)},
        {"scores": {"SADNESS": 0.10, "ANXIETY": 0.05, "ANGER": 0.0, "JOY": 0.35, "SURPRISE": 0.05, "DISGUST": 0.0},
         "dominant": "JOY", "dominant_score": 0.35, "prosody": _prosody(0.0, 0, 0, False)},
        {"scores": {"SADNESS": 0.55, "ANXIETY": 0.20, "ANGER": 0.05, "JOY": 0.0, "SURPRISE": 0.0, "DISGUST": 0.05},
         "dominant": "SADNESS", "dominant_score": 0.55, "prosody": _prosody(0.0, 0, 0, False)},
        {"scores": {"SADNESS": 0.10, "ANXIETY": 0.05, "ANGER": 0.0, "JOY": 0.30, "SURPRISE": 0.05, "DISGUST": 0.0},
         "dominant": "JOY", "dominant_score": 0.30, "prosody": _prosody(0.0, 0, 0, False)},
        {"scores": {"SADNESS": 0.20, "ANXIETY": 0.10, "ANGER": 0.0, "JOY": 0.25, "SURPRISE": 0.10, "DISGUST": 0.0},
         "dominant": "JOY", "dominant_score": 0.25, "prosody": _prosody(0.0, 0, 0, False)},
        {"scores": {"SADNESS": 0.05, "ANXIETY": 0.0, "ANGER": 0.0, "JOY": 0.50, "SURPRISE": 0.05, "DISGUST": 0.0},
         "dominant": "JOY", "dominant_score": 0.50, "prosody": _prosody(0.0, 0, 0, False)},
    ]


def _emotions_conflict() -> list[dict]:
    return [
        {"scores": {"SADNESS": 0.05, "ANXIETY": 0.10, "ANGER": 0.55, "JOY": 0.0, "SURPRISE": 0.05, "DISGUST": 0.30},
         "dominant": "ANGER", "dominant_score": 0.55, "prosody": _prosody(0.0, 1, 0, True)},
        {"scores": {"SADNESS": 0.15, "ANXIETY": 0.10, "ANGER": 0.20, "JOY": 0.0, "SURPRISE": 0.0, "DISGUST": 0.15},
         "dominant": "ANGER", "dominant_score": 0.20, "prosody": _prosody(0.0, 0, 0, True)},
        {"scores": {"SADNESS": 0.10, "ANXIETY": 0.05, "ANGER": 0.65, "JOY": 0.0, "SURPRISE": 0.0, "DISGUST": 0.20},
         "dominant": "ANGER", "dominant_score": 0.65, "prosody": _prosody(0.0, 2, 0, False)},
        {"scores": {"SADNESS": 0.40, "ANXIETY": 0.30, "ANGER": 0.10, "JOY": 0.0, "SURPRISE": 0.0, "DISGUST": 0.05},
         "dominant": "SADNESS", "dominant_score": 0.40, "prosody": _prosody(0.0, 0, 0, True)},
        {"scores": {"SADNESS": 0.05, "ANXIETY": 0.10, "ANGER": 0.40, "JOY": 0.0, "SURPRISE": 0.10, "DISGUST": 0.35},
         "dominant": "ANGER", "dominant_score": 0.40, "prosody": _prosody(0.0, 0, 0, False)},
        {"scores": {"SADNESS": 0.50, "ANXIETY": 0.35, "ANGER": 0.05, "JOY": 0.0, "SURPRISE": 0.0, "DISGUST": 0.05},
         "dominant": "SADNESS", "dominant_score": 0.50, "prosody": _prosody(0.0, 1, 1, False)},
    ]


# Conversation markers per scenario
THERAPY_CONV_MARKERS = [
    {"id": "ATO_HESITATION", "layer": "ATO", "confidence": 0.92, "description": "Zoegerungsmarker",
     "message_indices": [0], "family": "uncertainty", "multiplier": 1.0,
     "matches": [{"pattern": r"\baehm\b", "span": [16, 20], "matched_text": "aehm"}]},
    {"id": "ATO_VALIDATION", "layer": "ATO", "confidence": 0.88, "description": "Validierung",
     "message_indices": [1], "family": "empathy", "multiplier": 1.1,
     "matches": [{"pattern": r"\bich verstehe\b", "span": [0, 12], "matched_text": "Ich verstehe"}]},
    {"id": "ATO_SELF_BLAME", "layer": "ATO", "confidence": 0.91, "description": "Selbstbeschuldigung",
     "message_indices": [2], "family": "self_attribution", "multiplier": 1.2,
     "matches": [{"pattern": r"\bmeine schuld\b", "span": [7, 20], "matched_text": "meine Schuld"}]},
    {"id": "ATO_REPAIR_BID", "layer": "ATO", "confidence": 0.95, "description": "Reparaturversuch",
     "message_indices": [4], "family": "repair", "multiplier": 1.3,
     "matches": [{"pattern": r"\btut mir leid\b", "span": [3, 15], "matched_text": "tut mir leid"}]},
    {"id": "SEM_REPAIR_ATTEMPT", "layer": "SEM", "confidence": 0.84, "description": "Strukturierter Reparaturversuch",
     "message_indices": [3, 4], "family": "repair", "multiplier": 1.3, "matches": []},
    {"id": "SEM_SECURE_BASE", "layer": "SEM", "confidence": 0.80, "description": "Sichere-Basis-Signal",
     "message_indices": [5], "family": "attachment", "multiplier": 1.2,
     "matches": [{"pattern": r"\bich bin da\b", "span": [14, 24], "matched_text": "Ich bin da"}]},
    {"id": "CLU_REPAIR_SEQUENCE", "layer": "CLU", "confidence": 0.72, "description": "Reparatursequenz",
     "message_indices": [3, 4, 5], "family": "repair_dynamics", "multiplier": 1.4, "matches": []},
    {"id": "MEMA_THERAPEUTIC_PROGRESS", "layer": "MEMA", "confidence": 0.65, "description": "Therapeutischer Fortschritt",
     "message_indices": [0, 1, 2, 3, 4, 5], "family": "meta_diagnosis", "multiplier": 1.8, "matches": []},
]

CONFLICT_CONV_MARKERS = [
    {"id": "ATO_CONTEMPT", "layer": "ATO", "confidence": 0.94, "description": "Verachtungssignal",
     "message_indices": [0], "family": "contempt", "multiplier": 1.5,
     "matches": [{"pattern": r"\btypisch\b", "span": [0, 7], "matched_text": "Typisch"}]},
    {"id": "ATO_STONEWALLING", "layer": "ATO", "confidence": 0.90, "description": "Mauern",
     "message_indices": [1], "family": "avoidance", "multiplier": 1.4,
     "matches": [{"pattern": r"\bmir egal\b", "span": [0, 8], "matched_text": "Mir egal"}]},
    {"id": "ATO_DEMAND", "layer": "ATO", "confidence": 0.93, "description": "Forderung",
     "message_indices": [2], "family": "control", "multiplier": 1.3,
     "matches": [{"pattern": r"\bdu musst\b", "span": [36, 44], "matched_text": "Du musst"}]},
    {"id": "SEM_GUILT_TRIP", "layer": "SEM", "confidence": 0.87, "description": "Schuldgefuehle erzeugen",
     "message_indices": [2], "family": "manipulation", "multiplier": 1.4,
     "matches": [{"pattern": r"\bwegen dir\b", "span": [0, 9], "matched_text": "Wegen dir"}]},
    {"id": "SEM_GASLIGHTING", "layer": "SEM", "confidence": 0.82, "description": "Gaslighting",
     "message_indices": [4], "family": "manipulation", "multiplier": 1.8,
     "matches": [{"pattern": r"\bdas bildest du dir ein\b", "span": [0, 22], "matched_text": "Das bildest du dir ein"}]},
    {"id": "SEM_EMOTIONAL_FLOODING", "layer": "SEM", "confidence": 0.85, "description": "Emotionale Ueberflutung",
     "message_indices": [5], "family": "dysregulation", "multiplier": 1.2,
     "matches": [{"pattern": r"\bich kann nicht mehr\b", "span": [0, 19], "matched_text": "Ich kann nicht mehr"}]},
    {"id": "CLU_ESCALATION_SPIRAL", "layer": "CLU", "confidence": 0.78, "description": "Eskalationsspirale",
     "message_indices": [0, 2, 4], "family": "conflict_dynamics", "multiplier": 1.6, "matches": []},
    {"id": "CLU_WITHDRAWAL_PATTERN", "layer": "CLU", "confidence": 0.68, "description": "Rueckzugsmuster",
     "message_indices": [1, 3], "family": "avoidance_dynamics", "multiplier": 1.3, "matches": []},
    {"id": "MEMA_RELATIONSHIP_CRISIS", "layer": "MEMA", "confidence": 0.61, "description": "Beziehungskrise",
     "message_indices": [0, 1, 2, 3, 4, 5], "family": "meta_diagnosis", "multiplier": 2.0, "matches": []},
]

SINGLE_TEXT_MARKERS = [
    {"id": "ATO_HESITATION", "layer": "ATO", "confidence": 0.89,
     "description": "Zoegerungsmarker", "family": "uncertainty", "multiplier": 1.0,
     "matches": [{"pattern": r"\baehm\b", "span": [5, 9], "matched_text": "aehm"}]},
    {"id": "ATO_SELF_BLAME", "layer": "ATO", "confidence": 0.85,
     "description": "Selbstbeschuldigung", "family": "self_attribution", "multiplier": 1.2,
     "matches": [{"pattern": r"\bmeine schuld\b", "span": [22, 35], "matched_text": "meine Schuld"}]},
    {"id": "SEM_GUILT_TRIP", "layer": "SEM", "confidence": 0.72,
     "description": "Schuldgefuehle erzeugen", "family": "manipulation", "multiplier": 1.4,
     "matches": []},
]

# ---------------------------------------------------------------------------
# Persona Store (in-memory)
# ---------------------------------------------------------------------------

_PRE_SEEDED_TOKEN = "00000000-0000-0000-0000-000000000001"
_now_iso = datetime.now(timezone.utc).isoformat()

_personas: dict[str, dict] = {
    _PRE_SEEDED_TOKEN: {
        "token": _PRE_SEEDED_TOKEN,
        "created_at": "2026-02-20T10:00:00+00:00",
        "stats": {
            "session_count": 3,
            "total_messages": 18,
            "first_session": "2026-02-20T10:00:00+00:00",
            "last_session": "2026-02-22T14:30:00+00:00",
        },
        "ewma": {
            "A": {"valence": -0.15, "arousal": 0.35, "dominance": 0.10, "message_count": 9, "sessions_seen": 3},
            "B": {"valence": 0.20, "arousal": 0.10, "dominance": 0.05, "message_count": 9, "sessions_seen": 3},
        },
        "episodes": [
            {
                "id": "ep_001", "type": "escalation_cluster", "session": 1,
                "duration_messages": 4, "markers_involved": ["ATO_CONTEMPT", "ATO_DEMAND", "SEM_GUILT_TRIP"],
                "vad_delta": {"valence": -0.4, "arousal": 0.3},
                "state_at_entry": {"trust": 0.5, "conflict": 0.3, "deesc": 0.2},
                "state_at_exit": {"trust": 0.2, "conflict": 0.7, "deesc": 0.1},
            },
            {
                "id": "ep_002", "type": "repair_trend", "session": 2,
                "duration_messages": 3, "markers_involved": ["ATO_REPAIR_BID", "SEM_REPAIR_ATTEMPT"],
                "vad_delta": {"valence": 0.5, "arousal": -0.2},
                "state_at_entry": {"trust": 0.3, "conflict": 0.5, "deesc": 0.2},
                "state_at_exit": {"trust": 0.6, "conflict": 0.2, "deesc": 0.5},
            },
            {
                "id": "ep_003", "type": "stabilization", "session": 3,
                "duration_messages": 6, "markers_involved": ["SEM_SECURE_BASE", "ATO_VALIDATION"],
                "vad_delta": {"valence": 0.2, "arousal": -0.1},
                "state_at_entry": {"trust": 0.6, "conflict": 0.2, "deesc": 0.5},
                "state_at_exit": {"trust": 0.7, "conflict": 0.1, "deesc": 0.6},
            },
        ],
        "predictions": {
            "shift_counts": {"repair": 5, "escalation": 3, "volatility": 1, "withdrawal": 2},
            "shift_prior": {"repair": 0.45, "escalation": 0.27, "volatility": 0.09, "withdrawal": 0.18},
            "shift_given_valence_quartile": {
                "Q1": {"repair": 0.6, "escalation": 0.2, "withdrawal": 0.2},
                "Q2": {"repair": 0.4, "escalation": 0.3, "withdrawal": 0.3},
                "Q3": {"repair": 0.3, "escalation": 0.5, "withdrawal": 0.2},
                "Q4": {"repair": 0.2, "escalation": 0.6, "withdrawal": 0.2},
            },
            "top_transition_pairs": [
                ["escalation", "repair", 3],
                ["repair", "stabilization", 2],
                ["withdrawal", "escalation", 1],
            ],
        },
    }
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# GET /v1/health
@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "5.1-LD5",
        "markers_loaded": len(SAMPLE_MARKERS),
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


# POST /v1/analyze
@app.post("/v1/analyze")
async def analyze_text(request: Request):
    body = await request.json()
    text = body.get("text", "")
    scenario = _scenario(request)

    markers = SINGLE_TEXT_MARKERS if scenario == "single_text" else SINGLE_TEXT_MARKERS
    return {
        "markers": markers,
        "meta": _meta(len(text), len(markers), ["ATO", "SEM"]),
    }


# POST /v1/analyze/conversation
@app.post("/v1/analyze/conversation")
async def analyze_conversation(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    scenario = _scenario(request)

    if scenario == "conflict_escalation":
        markers = CONFLICT_CONV_MARKERS
    else:
        markers = THERAPY_CONV_MARKERS

    text_len = sum(len(m.get("text", "")) for m in messages)
    temporal = [
        {"pattern_type": "recurring", "marker_id": markers[0]["id"],
         "first_seen": 0, "last_seen": len(messages) - 1, "frequency": 2, "trend": "stable"},
    ]

    return {
        "markers": markers,
        "temporal_patterns": temporal,
        "meta": _meta(text_len, len(markers), ["ATO", "SEM", "CLU", "MEMA"], ms=3.4),
    }


# POST /v1/analyze/dynamics
@app.post("/v1/analyze/dynamics")
async def analyze_dynamics(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    persona_token = body.get("persona_token")
    scenario = _scenario(request)

    is_conflict = scenario == "conflict_escalation"
    markers = CONFLICT_CONV_MARKERS if is_conflict else THERAPY_CONV_MARKERS
    vad = VAD_CONFLICT_ESCALATION if is_conflict else VAD_THERAPY_REPAIR
    emotions = _emotions_conflict() if is_conflict else _emotions_therapy()

    text_len = sum(len(m.get("text", "")) for m in messages)

    # UED metrics
    if is_conflict:
        ued = {
            "home_base": {"valence": -0.5, "arousal": 0.4, "dominance": 0.1},
            "variability": {"valence": 0.25, "arousal": 0.35},
            "instability": {"valence": 0.30, "arousal": 0.40},
            "rise_rate": 0.65, "recovery_rate": 0.20, "density": 0.78,
        }
        state = {"trust": 0.15, "conflict": 0.82, "deesc": 0.08, "contributing_markers": 9}
    else:
        ued = {
            "home_base": {"valence": 0.1, "arousal": 0.25, "dominance": 0.0},
            "variability": {"valence": 0.30, "arousal": 0.15},
            "instability": {"valence": 0.15, "arousal": 0.10},
            "rise_rate": 0.35, "recovery_rate": 0.70, "density": 0.52,
        }
        state = {"trust": 0.68, "conflict": 0.18, "deesc": 0.62, "contributing_markers": 8}

    # Speaker baselines
    roles = list({m.get("role", "A") for m in messages}) or ["A", "B"]
    speakers = {}
    for i, role in enumerate(roles[:2]):
        v_base = -0.3 if (is_conflict and i == 0) else 0.2
        speakers[role] = {
            "message_count": max(1, len(messages) // 2),
            "baseline_final": {"valence": v_base, "arousal": 0.3 - i * 0.2, "dominance": 0.1},
            "valence_mean": v_base + 0.05,
            "valence_range": 0.6 if is_conflict else 0.4,
        }
    deltas: list[dict | None] = []
    for idx in range(min(len(messages), 6)):
        role = messages[idx].get("role", roles[idx % len(roles)])
        dv = vad[idx]["valence"] - (vad[idx - 1]["valence"] if idx > 0 else 0)
        da = vad[idx]["arousal"] - (vad[idx - 1]["arousal"] if idx > 0 else 0)
        shift = None
        if dv > 0.3:
            shift = "repair"
        elif dv < -0.3:
            shift = "escalation"
        deltas.append({
            "speaker": role, "delta_v": round(dv, 2), "delta_a": round(da, 2),
            "baseline_v": speakers.get(role, speakers[roles[0]])["baseline_final"]["valence"],
            "baseline_a": speakers.get(role, speakers[roles[0]])["baseline_final"]["arousal"],
            "shift": shift,
        })

    speaker_baselines = {"speakers": speakers, "per_message_delta": deltas}

    temporal = [
        {"pattern_type": "recurring", "marker_id": markers[0]["id"],
         "first_seen": 0, "last_seen": 5, "frequency": 2, "trend": "stable"},
        {"pattern_type": "emerging", "marker_id": markers[-1]["id"],
         "first_seen": 3, "last_seen": 5, "frequency": 1, "trend": "increasing"},
    ]

    # Persona session summary
    persona_session = None
    if persona_token and persona_token in _personas:
        p = _personas[persona_token]
        persona_session = {
            "session_number": p["stats"]["session_count"] + 1,
            "warm_start_applied": True,
            "new_episodes": [],
            "state_snapshot": {"trust": state["trust"], "conflict": state["conflict"], "deesc": state["deesc"]},
            "prediction_available": p["stats"]["session_count"] >= 3,
        }

    return {
        "markers": markers,
        "message_vad": vad[:len(messages)] if messages else vad,
        "message_emotions": emotions[:len(messages)] if messages else emotions,
        "ued_metrics": ued,
        "state_indices": state,
        "speaker_baselines": speaker_baselines,
        "temporal_patterns": temporal,
        "persona_session": persona_session,
        "meta": _meta(text_len, len(markers), ["ATO", "SEM", "CLU", "MEMA"], ms=5.8),
    }


# POST /v1/analyze/interpret
@app.post("/v1/analyze/interpret")
async def analyze_interpret(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    scenario = _scenario(request)
    is_conflict = scenario == "conflict_escalation"

    text_len = sum(len(m.get("text", "")) for m in messages)

    if is_conflict:
        semiotic_map = {
            "ATO_CONTEMPT": {"peirce": "index", "signifikat": "Verachtung/Ueberlegenheit", "cultural_frame": "Gottman", "framing_type": "abwertung"},
            "ATO_STONEWALLING": {"peirce": "index", "signifikat": "Emotionaler Rueckzug", "cultural_frame": "Gottman", "framing_type": "vermeidung"},
            "ATO_DEMAND": {"peirce": "index", "signifikat": "Dominanz/Forderung", "cultural_frame": "", "framing_type": "kontrollnarrative"},
            "SEM_GUILT_TRIP": {"peirce": "symbol", "signifikat": "Verdeckte Einflussnahme", "cultural_frame": "Sozialpsychologie", "framing_type": "kontrollnarrative"},
            "SEM_GASLIGHTING": {"peirce": "symbol", "signifikat": "Realitaetsverzerrung", "cultural_frame": "Sozialpsychologie", "framing_type": "kontrollnarrative"},
            "SEM_EMOTIONAL_FLOODING": {"peirce": "icon", "signifikat": "Emotionale Ueberwaeltigung", "cultural_frame": "Emotionsregulation", "framing_type": "ueberflutung"},
            "CLU_ESCALATION_SPIRAL": {"peirce": "index", "signifikat": "Eskalationsdynamik", "cultural_frame": "Gottman", "framing_type": "eskalation"},
            "CLU_WITHDRAWAL_PATTERN": {"peirce": "index", "signifikat": "Rueckzugsmuster", "cultural_frame": "Gottman", "framing_type": "vermeidung"},
            "MEMA_RELATIONSHIP_CRISIS": {"peirce": "symbol", "signifikat": "Meta-Organismusdiagnose", "cultural_frame": "Systemisch", "framing_type": "meta"},
        }
        framings = [
            {"framing_type": "kontrollnarrative", "label": "Kontroll-/Manipulations-Framing",
             "intensity": 0.93, "evidence_markers": ["ATO_DEMAND", "SEM_GUILT_TRIP", "SEM_GASLIGHTING"],
             "message_indices": [2, 4]},
            {"framing_type": "abwertung", "label": "Abwertungsmodus (Verachtung/Sarkasmus)",
             "intensity": 0.94, "evidence_markers": ["ATO_CONTEMPT"],
             "message_indices": [0]},
            {"framing_type": "eskalation", "label": "Eskalationsdynamik",
             "intensity": 0.78, "evidence_markers": ["CLU_ESCALATION_SPIRAL"],
             "message_indices": [0, 2, 4]},
            {"framing_type": "vermeidung", "label": "Vermeidungs-/Rueckzugsmodus",
             "intensity": 0.90, "evidence_markers": ["ATO_STONEWALLING", "CLU_WITHDRAWAL_PATTERN"],
             "message_indices": [1, 3]},
            {"framing_type": "ueberflutung", "label": "Emotionale Ueberflutung",
             "intensity": 0.85, "evidence_markers": ["SEM_EMOTIONAL_FLOODING"],
             "message_indices": [5]},
            {"framing_type": "meta", "label": "Meta-Organismusdiagnose",
             "intensity": 0.61, "evidence_markers": ["MEMA_RELATIONSHIP_CRISIS"],
             "message_indices": [0, 1, 2, 3, 4, 5]},
        ]
        dominant = "abwertung"
        n_markers = 9
    else:
        semiotic_map = {
            "ATO_HESITATION": {"peirce": "icon", "signifikat": "Zoegern/Ambivalenz", "cultural_frame": "", "framing_type": "unsicherheit"},
            "ATO_VALIDATION": {"peirce": "icon", "signifikat": "Einfuehlung/Validierung", "cultural_frame": "Rogers", "framing_type": "empathie"},
            "ATO_SELF_BLAME": {"peirce": "index", "signifikat": "Selbstbeschuldigung", "cultural_frame": "", "framing_type": "schuld"},
            "ATO_REPAIR_BID": {"peirce": "index", "signifikat": "Beziehungswiederherstellung", "cultural_frame": "Gottman", "framing_type": "reparatur"},
            "SEM_REPAIR_ATTEMPT": {"peirce": "index", "signifikat": "Beziehungswiederherstellung", "cultural_frame": "Gottman", "framing_type": "reparatur"},
            "SEM_SECURE_BASE": {"peirce": "symbol", "signifikat": "Sichere-Basis-Signal", "cultural_frame": "Bowlby", "framing_type": "bindung"},
            "CLU_REPAIR_SEQUENCE": {"peirce": "index", "signifikat": "Reparatursequenz", "cultural_frame": "Gottman", "framing_type": "reparatur"},
            "MEMA_THERAPEUTIC_PROGRESS": {"peirce": "symbol", "signifikat": "Meta-Organismusdiagnose", "cultural_frame": "Systemisch", "framing_type": "meta"},
        }
        framings = [
            {"framing_type": "reparatur", "label": "Reparatur-/Wiederherstellungsmodus",
             "intensity": 0.95, "evidence_markers": ["ATO_REPAIR_BID", "SEM_REPAIR_ATTEMPT", "CLU_REPAIR_SEQUENCE"],
             "message_indices": [3, 4, 5]},
            {"framing_type": "empathie", "label": "Empathie-/Validierungsmodus",
             "intensity": 0.88, "evidence_markers": ["ATO_VALIDATION"],
             "message_indices": [1]},
            {"framing_type": "schuld", "label": "Schuld-/Selbstattributions-Framing",
             "intensity": 0.91, "evidence_markers": ["ATO_SELF_BLAME"],
             "message_indices": [2]},
            {"framing_type": "unsicherheit", "label": "Unsicherheits-/Ambivalenz-Framing",
             "intensity": 0.92, "evidence_markers": ["ATO_HESITATION"],
             "message_indices": [0]},
            {"framing_type": "bindung", "label": "Bindungs-/Sicherheitssignal",
             "intensity": 0.80, "evidence_markers": ["SEM_SECURE_BASE"],
             "message_indices": [5]},
            {"framing_type": "meta", "label": "Meta-Organismusdiagnose",
             "intensity": 0.65, "evidence_markers": ["MEMA_THERAPEUTIC_PROGRESS"],
             "message_indices": [0, 1, 2, 3, 4, 5]},
        ]
        dominant = "reparatur"
        n_markers = 8

    if is_conflict:
        findings = {
            "narrative": "Kontroll- und Eskalationssignale (9 Marker) praegen den Austausch. Muster wie Contempt, Demand, Guilt Trip deuten auf eine zunehmend verhaertete Dynamik hin. Vermeidungs- und Rueckzugsmuster (2 Marker) sind praesent. Stonewalling, Withdrawal Pattern signalisieren emotionale Distanzierung.",
            "key_points": [
                "Abwertungsmodus: 1 Marker, 94% Intensitaet",
                "Kontroll-/Manipulations-Framing: 3 Marker, 93% Intensitaet",
                "Vermeidungs-/Rueckzugsmodus: 2 Marker, 90% Intensitaet",
                "Demand-Withdraw-Muster erkennbar",
            ],
            "relational_pattern": "Es zeigt sich ein Demand-Withdraw-Muster: Waehrend eine Seite eskaliert, zieht sich die andere zurueck — ein klassischer Teufelskreis.",
            "bias_check": None,
        }
    else:
        findings = {
            "narrative": "Reparatursignale (3 Marker) zeigen Versuche der Wiederherstellung. Repair Bid, Repair Attempt, Repair Sequence deuten auf aktive Beziehungsarbeit hin. Empathie- und Validierungssignale (1 Marker) zeigen einfuehlsame Anteile.",
            "key_points": [
                "Reparatur-/Wiederherstellungsmodus: 3 Marker, 95% Intensitaet",
                "Unsicherheits-/Ambivalenz-Framing: 1 Marker, 92% Intensitaet",
                "Schuld-/Selbstattributions-Framing: 1 Marker, 91% Intensitaet",
                "Empathie und Reparatur dominieren — konstruktive Kommunikation",
            ],
            "relational_pattern": "Empathie und Reparatur dominieren — konstruktive Kommunikation mit echten Verstaendigungsversuchen.",
            "bias_check": None,
        }

    return {
        "framings": framings,
        "semiotic_map": semiotic_map,
        "dominant_framing": dominant,
        "findings": findings,
        "meta": _meta(text_len, n_markers, ["ATO", "SEM", "CLU", "MEMA"], ms=4.2),
    }


# POST /v1/personas
@app.post("/v1/personas")
async def create_persona():
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    _personas[token] = {
        "token": token,
        "created_at": now,
        "stats": {"session_count": 0, "total_messages": 0, "first_session": now, "last_session": now},
        "ewma": {},
        "episodes": [],
        "predictions": {"shift_counts": {}, "shift_prior": {}, "shift_given_valence_quartile": {}, "top_transition_pairs": []},
    }
    return {"token": token, "created_at": now}


# GET /v1/personas/{token}
@app.get("/v1/personas/{token}")
async def get_persona(token: str):
    if token not in _personas:
        raise HTTPException(status_code=404, detail="Persona not found")
    return _personas[token]


# DELETE /v1/personas/{token}
@app.delete("/v1/personas/{token}")
async def delete_persona(token: str):
    if token not in _personas:
        raise HTTPException(status_code=404, detail="Persona not found")
    _personas.pop(token)
    return {"status": "deleted", "token": token}


# GET /v1/personas/{token}/predict
@app.get("/v1/personas/{token}/predict")
async def predict_persona(token: str):
    if token not in _personas:
        raise HTTPException(status_code=404, detail="Persona not found")
    p = _personas[token]
    sc = p["stats"]["session_count"]
    preds = p.get("predictions", {})
    total_shifts = sum(preds.get("shift_counts", {}).values())

    if total_shifts < 5:
        return {"token": token, "session_count": sc, "predictions": None, "confidence": "insufficient_data"}

    confidence = "high" if sc >= 10 else ("medium" if sc >= 5 else "low")
    return {"token": token, "session_count": sc, "predictions": preds, "confidence": confidence}


# GET /v1/markers
@app.get("/v1/markers")
async def list_markers(
    layer: str | None = None,
    family: str | None = None,
    tag: str | None = None,
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    filtered = SAMPLE_MARKERS
    if layer:
        filtered = [m for m in filtered if m["layer"] == layer.upper()]
    if family:
        filtered = [m for m in filtered if m.get("family") == family]
    if tag:
        filtered = [m for m in filtered if tag in m.get("tags", [])]
    if search:
        s = search.lower()
        filtered = [m for m in filtered if s in m["id"].lower() or s in m.get("description", "").lower()]

    total = len(filtered)
    page = filtered[offset:offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "markers": page}


# GET /v1/markers/{marker_id}
@app.get("/v1/markers/{marker_id}")
async def get_marker(marker_id: str):
    m = _markers_by_id.get(marker_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Marker '{marker_id}' not found")
    return m


# GET /v1/engine/config
@app.get("/v1/engine/config")
async def get_engine_config():
    layers = {"ATO": 0, "SEM": 0, "CLU": 0, "MEMA": 0}
    for m in SAMPLE_MARKERS:
        layers[m["layer"]] += 1

    return {
        "version": "5.1-LD5",
        "total_markers": len(SAMPLE_MARKERS),
        "layers": layers,
        "families": {
            "uncertainty": {"weight": 1.0, "description": "Unsicherheitssignale"},
            "repair": {"weight": 1.3, "description": "Reparaturversuche und Beziehungswiederherstellung"},
            "contempt": {"weight": 1.5, "description": "Verachtung und Abwertung (Gottman)"},
            "manipulation": {"weight": 1.4, "description": "Manipulative Kommunikationsmuster"},
            "avoidance": {"weight": 1.2, "description": "Vermeidung und Rueckzug"},
            "attachment": {"weight": 1.2, "description": "Bindungssignale und sichere Basis"},
            "control": {"weight": 1.3, "description": "Kontrolle und Forderungen"},
            "dysregulation": {"weight": 1.2, "description": "Emotionale Dysregulation"},
        },
        "ewma": {
            "alpha": 0.3,
            "description": "Exponentially Weighted Moving Average fuer Persona-Baselines",
            "warm_start_sessions": 2,
        },
        "ars": {
            "description": "Adaptive Response Scoring",
            "compositionality_weights": {
                "deterministic": 1.0, "contextual": 0.70, "emergent": 0.50,
            },
        },
        "bias_protection": {
            "min_match_length": 3,
            "vad_congruence_gate": True,
            "description": "3-char minimum + VAD quantum collapse gate",
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="LeanDeep Mock API Server")
    parser.add_argument("--port", type=int, default=8420, help="Port (default: 8420)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host (default: 0.0.0.0)")
    args = parser.parse_args()

    print(f"\n  LeanDeep Mock Server starting on http://localhost:{args.port}")
    print(f"  Scenarios: therapy_repair (default), conflict_escalation, single_text")
    print(f"  Switch via: X-Mock-Scenario header or ?scenario= query param")
    print(f"  Pre-seeded persona: {_PRE_SEEDED_TOKEN}")
    print(f"  {len(SAMPLE_MARKERS)} sample markers (8 ATO, 6 SEM, 4 CLU, 2 MEMA)\n")

    uvicorn.run(app, host=args.host, port=args.port)
