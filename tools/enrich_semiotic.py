#!/usr/bin/env python3
"""
Semiotic Enrichment Tool for LeanDeep Marker System.

Adds Peirce classification, signifikat, cultural_frame, and framing_type
to marker YAML files based on marker ID keywords, tags, and layer.

Reads from:  build/markers_normalized/marker_registry.json
Writes to:   build/markers_rated/{1_approved,2_good}/{ATO,SEM,CLU,MEMA}/*.yaml

Usage:
    python3 tools/enrich_semiotic.py              # dry-run (default), print stats
    python3 tools/enrich_semiotic.py --apply      # write semiotic to source YAML files
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / "build" / "markers_normalized" / "marker_registry.json"
RATED_DIR = REPO / "build" / "markers_rated"
TIER_MAP = {1: "1_approved", 2: "2_good"}

# ---------------------------------------------------------------------------
# YAML setup (matches project convention)
# ---------------------------------------------------------------------------

yaml_rw = YAML()
yaml_rw.preserve_quotes = True
yaml_rw.allow_duplicate_keys = True
yaml_rw.default_flow_style = None
yaml_rw.width = 200
yaml_rw.allow_unicode = True

# ---------------------------------------------------------------------------
# Comprehensive keyword -> framing classification
# ---------------------------------------------------------------------------
# Priority-ordered: first match wins. Each entry is:
#   (keywords_in_id_or_tags, {peirce, framing_type, signifikat, cultural_frame})
# Keywords are matched case-insensitively against the marker ID and tags.

CLASSIFICATION_RULES = [
    # === ESKALATION (conflict, anger, aggression, blame, criticism) ===
    (["CONTEMPT", "VERACHTUNG"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Verachtung/Ueberlegenheit", "cultural_frame": "Gottman"}),
    (["CRITICISM", "KRITIK"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Destruktive Kritik", "cultural_frame": "Gottman"}),
    (["STONEWALLING", "MAUERN"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Mauern/Blockade", "cultural_frame": "Gottman"}),
    (["DEFENSIVENESS", "DEFENSIVE"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Abwehr/Rechtfertigung", "cultural_frame": "Gottman"}),
    (["GOTTMAN"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Gottman-Konfliktsignal", "cultural_frame": "Gottman"}),
    (["ACCUSATION", "ANKLAGE", "BLAME_SHIFT", "BLAME"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Schuldzuweisung/Anklage", "cultural_frame": "Gottman"}),
    (["ANGER", "WUT", "RAGE", "AGGRESS"],
     {"peirce": "icon", "framing_type": "eskalation", "signifikat": "Aerger/Wut", "cultural_frame": "Emotionsregulation"}),
    (["ESCALATION", "ESKALATION", "HEATED", "PROVOK"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Eskalation/Konfliktsteigerung", "cultural_frame": "Gottman"}),
    (["CONFLICT", "KONFLIKT", "FIGHT", "STREIT"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Konfliktdynamik", "cultural_frame": "Gottman"}),
    (["DEMAND", "FORDERUNG", "ULTIMATUM", "THREAT", "DROH"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Forderung/Drohung", "cultural_frame": ""}),
    (["HOSTILE", "FEINDSELIG"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Feindseligkeit", "cultural_frame": "Gottman"}),
    (["SARKASM", "SARCASM", "IRONI"],
     {"peirce": "index", "framing_type": "abwertung", "signifikat": "Sarkasmus/Ironie als Waffe", "cultural_frame": ""}),
    (["BELITTL", "HERABSETZ", "INSULT"],
     {"peirce": "index", "framing_type": "abwertung", "signifikat": "Herabsetzung/Beleidigung", "cultural_frame": ""}),
    (["ABSOLUTIZ", "ABSOLUTE", "IMMER", "NEVER_ALWAYS", "SUPERLATIV"],
     {"peirce": "symbol", "framing_type": "polarisierung", "signifikat": "Absolutheit/Schwarz-Weiss", "cultural_frame": ""}),
    (["POLARISI", "GENERALIZ"],
     {"peirce": "symbol", "framing_type": "polarisierung", "signifikat": "Polarisierung/Verallgemeinerung", "cultural_frame": ""}),
    (["INTERRUPT", "UNTERBRECH"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Unterbrechung/Redeentzug", "cultural_frame": ""}),

    # === KONTROLLNARRATIVE (manipulation, gaslighting, control, power) ===
    (["GASLIGHT"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Realitaetsverzerrung", "cultural_frame": "Sozialpsychologie"}),
    (["MANIPULAT"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Verdeckte Einflussnahme", "cultural_frame": "Sozialpsychologie"}),
    (["CONTROL", "KONTROLL"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Kontrolle/Dominanz", "cultural_frame": "Sozialpsychologie"}),
    (["POWER", "DOMINAN", "MACHT"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Machtausuebung", "cultural_frame": "Sozialpsychologie"}),
    (["DOUBLE_BIND", "DOPPELBIND"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Doppelbindung", "cultural_frame": "Bateson"}),
    (["PASSIVE_AGGRESS"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Passive Aggression", "cultural_frame": ""}),
    (["TRIANGULAT"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Triangulation", "cultural_frame": "Sozialpsychologie"}),
    (["COERCI", "NOTIG", "ZWANG"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Noetigung/Zwang", "cultural_frame": ""}),
    (["DEPENDENCY", "ABHANGIG"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Abhaengigkeit erzeugen", "cultural_frame": ""}),
    (["BIAS", "ANCHORING", "FRAMING"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Kognitive Verzerrung/Framing", "cultural_frame": "Sozialpsychologie"}),

    # === REPARATUR (repair, apology, reconciliation) ===
    (["REPAIR", "REPARATUR"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Beziehungsreparatur", "cultural_frame": "Gottman"}),
    (["APOLOGY", "ENTSCHULD", "SORRY"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Entschuldigung/Reue", "cultural_frame": "Gottman"}),
    (["FORGIV", "VERZEIH", "RECONCIL"],
     {"peirce": "symbol", "framing_type": "reparatur", "signifikat": "Vergebung/Versoehnung", "cultural_frame": ""}),
    (["COMPROM", "KOMPROMISS"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Kompromissbereitschaft", "cultural_frame": ""}),
    (["DEESKALAT", "DEESCALAT"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Deeskalation", "cultural_frame": ""}),
    (["BRIDGE", "BRUECK"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Brueckenbildung", "cultural_frame": ""}),
    (["RESPONSIB", "VERANTWORT"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Verantwortungsuebernahme", "cultural_frame": ""}),

    # === VERMEIDUNG (avoidance, withdrawal, distancing) ===
    (["AVOIDANC", "VERMEID"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Vermeidungsverhalten", "cultural_frame": ""}),
    (["WITHDRAW", "RUECKZUG", "DISENGAG"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Emotionaler Rueckzug", "cultural_frame": ""}),
    (["DEFLECT", "ABLENK"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Ablenkung/Ausweichen", "cultural_frame": ""}),
    (["DISTANC", "ENTFERN"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Distanzierung", "cultural_frame": ""}),
    (["SILENT", "SCHWEIG", "SHUT"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Schweigen/Verstummen", "cultural_frame": ""}),
    (["ABSENCE", "ABWESEN"],
     {"peirce": "icon", "framing_type": "vermeidung", "signifikat": "Abwesenheit/Leere", "cultural_frame": ""}),
    (["DRIFT", "TOPIC_SHIFT"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Themenwechsel/Abdriften", "cultural_frame": ""}),
    (["FLAT", "AFFECT_FLAT"],
     {"peirce": "icon", "framing_type": "vermeidung", "signifikat": "Flacher Affekt", "cultural_frame": "Emotionsregulation"}),
    (["MINIMAL", "MICRO", "ACK_MICRO"],
     {"peirce": "icon", "framing_type": "vermeidung", "signifikat": "Minimal-Antwort/Mikrobestaetigung", "cultural_frame": ""}),

    # === BINDUNG (attachment, bonding, love, trust, safety) ===
    (["ATTACHMENT", "BINDUNG"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Bindungsmuster", "cultural_frame": "Bowlby"}),
    (["BONDING", "VERBUND"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Verbundenheitssignal", "cultural_frame": "Bowlby"}),
    (["LOVE", "LIEBE", "AFFECTION", "ZUNEIG", "DEVOTION"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Liebe/Zuneigung", "cultural_frame": ""}),
    (["TRUST", "VERTRAU"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Vertrauen", "cultural_frame": "Bowlby"}),
    (["SAFETY", "SICHER"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Sicherheitssignal", "cultural_frame": "Bowlby"}),
    (["COMMITMENT", "VERPFLICHT", "LOYALT"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Engagement/Verbindlichkeit", "cultural_frame": ""}),
    (["INTIMAC", "CLOSENESS", "NAEHE"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Naehe/Intimitaet", "cultural_frame": "Bowlby"}),
    (["SUPPORT", "UNTERSTUETZ"],
     {"peirce": "index", "framing_type": "bindung", "signifikat": "Unterstuetzung/Beistand", "cultural_frame": ""}),
    (["WARMTH", "WAERME"],
     {"peirce": "icon", "framing_type": "bindung", "signifikat": "Waerme/Herzlichkeit", "cultural_frame": ""}),
    (["RITUAL"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Beziehungsritual", "cultural_frame": ""}),
    (["PRESENCE", "PRAESENZ"],
     {"peirce": "icon", "framing_type": "bindung", "signifikat": "Praesenz/Anwesenheit", "cultural_frame": ""}),
    (["SHARED", "GEMEINSAM"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Geteilte Erfahrung", "cultural_frame": ""}),

    # === UEBERFLUTUNG (dysregulation, flooding, overwhelm, depression, grief) ===
    (["DYSREG", "FLOOD", "OVERWHELM", "UEBERFLUT"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Emotionale Ueberwaeltigung", "cultural_frame": "Emotionsregulation"}),
    (["DEPRESSION", "DEPRESS"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Depressive Zeichen", "cultural_frame": "Klinische Psychologie"}),
    (["SADNESS", "TRAUER", "GRIEF", "LOSS", "VERLUST"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Trauer/Verlust", "cultural_frame": ""}),
    (["PANIC", "PANIK", "CRISIS", "KRISE"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Panik/Krise", "cultural_frame": "Emotionsregulation"}),
    (["BREAKDOWN", "ZUSAMMENBRUCH"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Zusammenbruch", "cultural_frame": "Emotionsregulation"}),
    (["ABANDON", "VERLASSEN"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Verlassenheitsangst", "cultural_frame": "Bowlby"}),
    (["SUICID", "SELBSTVERL", "SELF_HARM"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Suizidale/Selbstverletzende Signale", "cultural_frame": "Klinische Psychologie"}),

    # === UNSICHERHEIT (uncertainty, hesitation, ambivalence, fear, anxiety) ===
    (["FEAR", "ANGST", "ANXIETY"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Angst/Bedrohungserleben", "cultural_frame": ""}),
    (["UNCERTAINTY", "UNSICHER"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Unsicherheit", "cultural_frame": ""}),
    (["AMBIVAL", "ZWIESPALT"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Ambivalenz/Zwiespalt", "cultural_frame": ""}),
    (["HESITAT", "ZOEGER"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Zoegern/Unentschlossenheit", "cultural_frame": ""}),
    (["DOUBT", "ZWEIFEL", "CONFUSION"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Zweifel/Verwirrung", "cultural_frame": ""}),
    (["PARADOX", "WIDERSPRUCH"],
     {"peirce": "symbol", "framing_type": "unsicherheit", "signifikat": "Paradoxie/Widerspruch", "cultural_frame": ""}),

    # === SCHULD (guilt, shame, self-blame) ===
    (["GUILT", "SCHULD"],
     {"peirce": "index", "framing_type": "schuld", "signifikat": "Schuld/Schuldgefuehle", "cultural_frame": ""}),
    (["SHAME", "SCHAM"],
     {"peirce": "icon", "framing_type": "schuld", "signifikat": "Scham", "cultural_frame": ""}),
    (["SELF_BLAME", "SELBSTVORWURF", "SELF_ATTRIBUTION"],
     {"peirce": "index", "framing_type": "schuld", "signifikat": "Selbstbeschuldigung", "cultural_frame": ""}),
    (["REGRET", "REUE", "REMORSE"],
     {"peirce": "icon", "framing_type": "schuld", "signifikat": "Reue/Bedauern", "cultural_frame": ""}),

    # === EMPATHIE (empathy, validation, joy, gratitude, humor) ===
    (["EMPATHY", "EMPATHIE", "EINFUEHL"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Einfuehlung/Empathie", "cultural_frame": "Rogers"}),
    (["VALIDAT", "ANERKEN"],
     {"peirce": "index", "framing_type": "empathie", "signifikat": "Validierung/Anerkennung", "cultural_frame": "Rogers"}),
    (["LISTEN", "ZUHOER", "ATTENTION"],
     {"peirce": "index", "framing_type": "empathie", "signifikat": "Aufmerksames Zuhoeren", "cultural_frame": "Rogers"}),
    (["ACCEPT", "AKZEPT"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Akzeptanz", "cultural_frame": "Rogers"}),
    (["GRATITUDE", "DANKBAR"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Dankbarkeit", "cultural_frame": ""}),
    (["JOY", "FREUD", "GLUECK", "HAPPINESS"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Freude/Glueck", "cultural_frame": ""}),
    (["HUMOR", "LACHEN", "IRONY_POSITIVE"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Humor/Leichtigkeit", "cultural_frame": ""}),
    (["COMPASSION", "MITGEFUEHL"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Mitgefuehl", "cultural_frame": "Rogers"}),
    (["REASSUR", "BERUHIG"],
     {"peirce": "index", "framing_type": "empathie", "signifikat": "Beruhigung/Rueckversicherung", "cultural_frame": ""}),
    (["AFFIRM", "BESTAETI"],
     {"peirce": "index", "framing_type": "empathie", "signifikat": "Bestaetigungssignal", "cultural_frame": ""}),
    (["POSITIVE", "OPTIMIS", "HOPE"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Positive Grundhaltung", "cultural_frame": ""}),
    (["ENCOURAGEMENT", "ERMUTIG"],
     {"peirce": "index", "framing_type": "empathie", "signifikat": "Ermutigung", "cultural_frame": ""}),

    # === META (meta-diagnosis, organism, system-level) ===
    (["META_", "ORGANIS", "SYSTEM_"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Meta-Organismusdiagnose", "cultural_frame": "Systemisch"}),
    (["SPIRAL"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Beziehungsspirale", "cultural_frame": "Systemisch"}),
    (["STAGE", "PHASE"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Beziehungsphase", "cultural_frame": ""}),
    (["PERSONA"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Persoenlichkeitsmuster", "cultural_frame": ""}),
    (["DYNAMIC"],
     {"peirce": "index", "framing_type": "meta", "signifikat": "Beziehungsdynamik", "cultural_frame": "Systemisch"}),
    (["DIAGNOSIS", "DIAGNOS"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Diagnostisches Signal", "cultural_frame": "Klinische Psychologie"}),
    (["INTUITION"],
     {"peirce": "icon", "framing_type": "meta", "signifikat": "Cluster-Intuition", "cultural_frame": ""}),

    # === Broader categories for remaining markers ===
    (["SELF_DISCLOS", "OFFENBAR"],
     {"peirce": "index", "framing_type": "bindung", "signifikat": "Selbstoffenbarung", "cultural_frame": ""}),
    (["BOUNDAR", "GRENZ"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Grenzsetzung", "cultural_frame": ""}),
    (["NEED", "BEDUERFN"],
     {"peirce": "icon", "framing_type": "bindung", "signifikat": "Beduerfnisausdruck", "cultural_frame": ""}),
    (["ROLE", "SWITCH"],
     {"peirce": "index", "framing_type": "meta", "signifikat": "Rollenwechsel/-dynamik", "cultural_frame": "Systemisch"}),
    (["DECISION", "ENTSCHEID"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Entscheidungssignal", "cultural_frame": ""}),
    (["NARRAT", "STORY", "ERZAEHL"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Narratives Muster", "cultural_frame": ""}),
    (["ISOLATION"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Isolation/Rueckzug", "cultural_frame": ""}),
    (["RISK", "RISIKO"],
     {"peirce": "index", "framing_type": "unsicherheit", "signifikat": "Risikowahrnehmung", "cultural_frame": ""}),
    (["CLAIM", "ANSPRUCH"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Anspruchshaltung", "cultural_frame": ""}),
    (["NEGAT"],
     {"peirce": "icon", "framing_type": "eskalation", "signifikat": "Verneinung/Ablehnung", "cultural_frame": ""}),
    (["DESIRE", "WUNSCH", "LONGING", "SEHNSUCHT"],
     {"peirce": "icon", "framing_type": "bindung", "signifikat": "Sehnsucht/Verlangen", "cultural_frame": ""}),
    (["QUESTION", "FRAG"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Fragehaltung/Suchbewegung", "cultural_frame": ""}),
    (["EXPLAIN", "ERKLAER", "REASON"],
     {"peirce": "symbol", "framing_type": "reparatur", "signifikat": "Erklaerungsversuch", "cultural_frame": ""}),
    (["ASSERT", "BESTIMM"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Bestimmtheit/Assertion", "cultural_frame": ""}),
    (["RESIGN", "AUFGAB"],
     {"peirce": "icon", "framing_type": "vermeidung", "signifikat": "Resignation", "cultural_frame": ""}),
    (["SURPRIS", "UEBERRASCH"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Ueberraschung", "cultural_frame": ""}),
    (["DISGUST", "EKEL"],
     {"peirce": "icon", "framing_type": "abwertung", "signifikat": "Ekel/Abscheu", "cultural_frame": ""}),
    (["ACHIEVEMENT", "LEISTUNG", "DRIVE", "AGENCY", "ACTION"],
     {"peirce": "index", "framing_type": "kontrollnarrative", "signifikat": "Handlungsorientierung/Leistung", "cultural_frame": ""}),
    (["LEARNING", "LERN", "GROWTH"],
     {"peirce": "icon", "framing_type": "reparatur", "signifikat": "Lernbereitschaft/Wachstum", "cultural_frame": ""}),
    (["COORDINATION", "KOOPERAT"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Kooperation/Koordination", "cultural_frame": ""}),
    (["FINANCE", "GELD", "MONEY"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Finanzielles Druckmittel", "cultural_frame": ""}),
    (["EXTERN"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Externe Attribution", "cultural_frame": ""}),
]

# ---------------------------------------------------------------------------
# Myth mapping: framing_type -> cultural myth (Barthes secondary system)
# Each myth names the invisible narrative that a framing category naturalizes.
# ---------------------------------------------------------------------------

FRAMING_MYTHS = {
    "eskalation": "Konflikt ist unvermeidbar — wer kaempft, hat zumindest Recht",
    "kontrollnarrative": "Wer die Deutungshoheit hat, hat die Macht — Kontrolle tarnt sich als Fuersorge",
    "reparatur": "Kommunikation loest alles — reden heilt, schweigen zerstoert",
    "vermeidung": "Rueckzug schuetzt — wer sich entzieht, vermeidet Schlimmeres",
    "unsicherheit": "Zweifel ist Schwaeche — wer zoegert, verliert",
    "bindung": "Liebe verpflichtet — Naehe ist Beweis, Distanz ist Verrat",
    "ueberflutung": "Emotionen sind unkontrollierbar — Ueberwaeltigung ist Authentizitaet",
    "schuld": "Schuld bindet — wer schuldig ist, schuldet Wiedergutmachung",
    "empathie": "Verstehen heisst zustimmen — Empathie fordert Parteinahme",
    "abwertung": "Ueberlegenheit schuetzt — wer abwertet, vermeidet eigene Verletzlichkeit",
    "polarisierung": "Es gibt nur Schwarz und Weiss — Differenzierung ist Schwaeche",
    "meta": "Beziehung ist ein Organismus — Muster wiederholen sich unausweichlich",
}

# Layer-based fallbacks (last resort)
LAYER_DEFAULTS = {
    "ATO":  {"peirce": "icon",   "framing_type": "unsicherheit",  "signifikat": "Atomares Signal", "cultural_frame": ""},
    "SEM":  {"peirce": "index",  "framing_type": "unsicherheit",  "signifikat": "Semantisches Muster", "cultural_frame": ""},
    "CLU":  {"peirce": "index",  "framing_type": "meta",          "signifikat": "Cluster-Muster", "cultural_frame": ""},
    "MEMA": {"peirce": "symbol", "framing_type": "meta",          "signifikat": "Meta-Diagnose", "cultural_frame": "Systemisch"},
}


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def classify_marker(marker_id: str, layer: str, tags: list[str] | None,
                    existing_semiotic: dict | None) -> dict:
    """Classify a marker's semiotic properties.

    Two-pass matching: first check marker ID only (primary), then
    check ID + tags combined (secondary). ID matching takes priority
    because tags can contain generic terms that cause misclassification.

    Preserves existing semiotic fields (mode, level, object, connotation,
    interpretant). Only sets peirce, signifikat, cultural_frame, framing_type
    if not already set.

    Returns the merged semiotic dict.
    """
    result = dict(existing_semiotic) if existing_semiotic else {}

    # If peirce already set, only add myth if missing, then return
    if result.get("peirce"):
        if "myth" not in result or not result["myth"]:
            ft = result.get("framing_type", "")
            result["myth"] = FRAMING_MYTHS.get(ft, "")
        return result

    mid_upper = marker_id.upper()
    tag_str = " ".join((tags or [])).upper()

    # Pass 1: Match against marker ID only (primary — most reliable)
    defaults = None
    for keywords, props in CLASSIFICATION_RULES:
        if any(kw in mid_upper for kw in keywords):
            defaults = dict(props)
            break

    # Pass 2: Match against ID + tags combined (secondary — broader reach)
    if defaults is None and tag_str:
        search = mid_upper + " " + tag_str
        for keywords, props in CLASSIFICATION_RULES:
            if any(kw in search for kw in keywords):
                defaults = dict(props)
                break

    # Fallback to layer defaults
    if defaults is None:
        defaults = dict(LAYER_DEFAULTS.get(layer, LAYER_DEFAULTS["ATO"]))

    # Merge — don't overwrite existing fields
    for key in ("peirce", "signifikat", "framing_type", "cultural_frame"):
        if key not in result or not result[key]:
            result[key] = defaults.get(key, "")

    # Add myth based on framing_type (only if not already set)
    if "myth" not in result or not result["myth"]:
        ft = result.get("framing_type", "")
        result["myth"] = FRAMING_MYTHS.get(ft, "")

    return result


# ---------------------------------------------------------------------------
# YAML file I/O (same pattern as enrich_vad.py)
# ---------------------------------------------------------------------------

def find_yaml_path(marker_id: str, layer: str, rating: int) -> Path | None:
    """Resolve the source YAML path for a marker in build/markers_rated/."""
    tier = TIER_MAP.get(rating)
    if tier is None:
        for t in TIER_MAP.values():
            p = RATED_DIR / t / layer / f"{marker_id}.yaml"
            if p.exists():
                return p
        return None
    p = RATED_DIR / tier / layer / f"{marker_id}.yaml"
    if p.exists():
        return p
    for t in TIER_MAP.values():
        p = RATED_DIR / t / layer / f"{marker_id}.yaml"
        if p.exists():
            return p
    return None


def write_semiotic_to_yaml(yaml_path: Path, semiotic: dict, force: bool = False) -> bool:
    """Write semiotic block to a YAML file.

    Returns True if write succeeded, False on error.
    If force=False, preserves existing semiotic fields and only adds new ones.
    If force=True, overwrites peirce/signifikat/framing_type/cultural_frame.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml_rw.load(f)
    except Exception as e:
        print(f"  WARNING: Could not read {yaml_path.name}: {e}", file=sys.stderr)
        return False

    if isinstance(data, list) or data is None:
        return False

    existing = data.get("semiotic") or {}
    if isinstance(existing, dict):
        merged = dict(existing)
        force_keys = {"peirce", "signifikat", "framing_type", "cultural_frame"}
        for k, v in semiotic.items():
            if force and k in force_keys:
                merged[k] = v  # Force overwrite
            elif k not in merged or not merged[k]:
                merged[k] = v  # Only add if missing
    else:
        merged = semiotic

    data["semiotic"] = merged

    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml_rw.dump(data, f)
        return True
    except Exception as e:
        print(f"  WARNING: Could not write {yaml_path.name}: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def print_summary(enriched: list, already_set: int, not_found: int, errors: int):
    """Print semiotic enrichment summary."""
    if not enriched:
        print("No markers enriched.")
        return

    by_framing = defaultdict(int)
    by_peirce = defaultdict(int)
    by_layer = defaultdict(int)

    for item in enriched:
        by_framing[item["framing_type"]] += 1
        by_peirce[item["peirce"]] += 1
        by_layer[item["layer"]] += 1

    print("\n" + "=" * 70)
    print("Semiotic Enrichment Summary")
    print("=" * 70)

    print(f"\nPeirce Classification:")
    for k in sorted(by_peirce.keys()):
        print(f"  {k:<10} {by_peirce[k]:>5}")

    print(f"\nFraming Types:")
    for k in sorted(by_framing.keys(), key=lambda x: -by_framing[x]):
        print(f"  {k:<22} {by_framing[k]:>5}")

    print(f"\nLayer Breakdown:")
    for k in sorted(by_layer.keys()):
        print(f"  {k:<6} {by_layer[k]:>5}")

    print(f"\n{'Total enriched:':<22} {len(enriched)}")
    print(f"{'Already had peirce:':<22} {already_set}")
    print(f"{'YAML not found:':<22} {not_found}")
    print(f"{'Write errors:':<22} {errors}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Semiotic Enrichment Tool for LeanDeep Marker System"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write semiotic values to source YAML files (default: dry-run)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing peirce classification")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    markers = registry.get("markers", {})
    print(f"Loaded {len(markers)} markers from registry")

    enriched = []
    already_set = 0
    not_found = 0
    errors = 0
    written = 0

    for marker_id, data in markers.items():
        layer = data.get("layer", "")
        tags = data.get("tags", [])
        existing_semiotic = data.get("semiotic")

        # Check if peirce already set (unless --force)
        has_peirce = isinstance(existing_semiotic, dict) and existing_semiotic.get("peirce")
        needs_myth = not (isinstance(existing_semiotic, dict) and existing_semiotic.get("myth"))

        if not args.force and has_peirce and not needs_myth:
            already_set += 1
            continue

        # If --force, clear peirce so classify_marker can reclassify
        if args.force and isinstance(existing_semiotic, dict):
            existing_semiotic = {k: v for k, v in existing_semiotic.items()
                                 if k not in ("peirce", "signifikat", "framing_type", "cultural_frame")}
        elif has_peirce and needs_myth:
            # Only add myth to existing semiotic, don't reclassify
            pass

        semiotic = classify_marker(marker_id, layer, tags, existing_semiotic)

        enriched.append({
            "id": marker_id,
            "layer": layer,
            "peirce": semiotic.get("peirce", ""),
            "framing_type": semiotic.get("framing_type", ""),
            "signifikat": semiotic.get("signifikat", ""),
        })

        if args.apply:
            rating = data.get("rating", 1)
            yaml_path = find_yaml_path(marker_id, layer, rating)
            if yaml_path is None:
                not_found += 1
            else:
                ok = write_semiotic_to_yaml(yaml_path, semiotic, force=args.force)
                if ok:
                    written += 1
                else:
                    errors += 1

    print_summary(enriched, already_set, not_found, errors)

    if args.apply:
        print(f"\nWrote semiotic to {written} YAML files.")
    else:
        print(f"\nDry-run: {len(enriched)} markers would be enriched. Use --apply to write.")


if __name__ == "__main__":
    main()
