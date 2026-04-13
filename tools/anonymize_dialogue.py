"""Anonymization tool for therapy dialogue JSON files.

Removes personally identifying information (PII) while preserving
therapeutic terminology and marker-relevant language.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any

# Therapeutic terms that must never be anonymized
THERAPEUTIC_TERMS = {
    "Ego-State",
    "Ketamin",
    "Borderline",
    "Hypnose",
    "Trauma",
    "EMDR",
    "PTBS",
    "Dissoziation",
    "Schizophrenie",
    "Depression",
    "Angststörung",
    "Bipolar",
    "Narzissmus",
    "Psychose",
    "Suizidalität",
    "Selbstverletzung",
    "Panikattacke",
    "Zwangsstörung",
    "Essstörung",
    "Bulimie",
    "Anorexie",
    "ADHS",
    "Autismus",
    "Therapie",
    "Psychotherapie",
    "Verhaltenstherapie",
    "Tiefenpsychologie",
    "Übertragung",
    "Gegenübertragung",
    "Resilienz",
    "Achtsamkeit",
    "Mentalisierung",
    "Affektregulation",
}

# Regex patterns for PII detection
_PHONE_RE = re.compile(r"\+?\d[\d\s\-/]{7,}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_AGE_RE = re.compile(r"\b(\d{1,3})\s*[-]?\s*(Jahre?|jaehrig|jährig)\b", re.IGNORECASE)


def anonymize_text(
    text: str,
    names: dict[str, str] | None = None,
    places: dict[str, str] | None = None,
) -> str:
    """Replace PII in text while preserving therapeutic terminology.

    Args:
        text: The input text to anonymize.
        names: Mapping of real names to pseudonyms (case-sensitive).
        places: Mapping of place names to placeholders.

    Returns:
        Anonymized text with PII replaced.
    """
    result = text

    # Replace names (case-sensitive, longest first to avoid partial matches)
    if names:
        for name, replacement in sorted(names.items(), key=lambda x: -len(x[0])):
            result = result.replace(name, replacement)

    # Replace places (case-sensitive, longest first)
    if places:
        for place, replacement in sorted(places.items(), key=lambda x: -len(x[0])):
            result = result.replace(place, replacement)

    # Replace age patterns before phone numbers (ages are shorter digit sequences)
    result = _AGE_RE.sub("[Alter]", result)

    # Replace emails
    result = _EMAIL_RE.sub("[E-Mail]", result)

    # Replace phone numbers
    result = _PHONE_RE.sub("[Telefon]", result)

    return result


def anonymize_dialogue(
    dialogue: dict[str, Any],
    names: dict[str, str] | None = None,
    places: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Anonymize all message texts in a dialogue, preserving structure.

    Args:
        dialogue: Dialogue dict with 'messages' list and 'metadata' dict.
        names: Mapping of real names to pseudonyms.
        places: Mapping of place names to placeholders.

    Returns:
        Deep copy of the dialogue with anonymized texts and
        anonymization metadata set.
    """
    result = copy.deepcopy(dialogue)

    # Compute original hash from concatenated raw texts
    raw_texts = "".join(msg["text"] for msg in result["messages"])
    original_hash = hashlib.sha256(raw_texts.encode("utf-8")).hexdigest()

    # Anonymize each message
    for msg in result["messages"]:
        msg["text"] = anonymize_text(msg["text"], names=names, places=places)

    # Determine method based on what was provided
    methods = []
    if names:
        methods.append("name_replacement")
    if places:
        methods.append("place_replacement")
    method = methods[0] if methods else "pattern_replacement"

    # Set anonymization metadata
    result.setdefault("metadata", {})
    result["metadata"]["anonymization"] = {
        "status": "anonymized",
        "method": method,
        "original_hash": original_hash,
    }

    return result


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Detect PII patterns in text without modifying it.

    Args:
        text: The text to scan for PII.

    Returns:
        List of dicts with keys: type, match, start, end.
    """
    findings: list[dict[str, Any]] = []

    for match in _EMAIL_RE.finditer(text):
        findings.append({
            "type": "email",
            "match": match.group(),
            "start": match.start(),
            "end": match.end(),
        })

    for match in _PHONE_RE.finditer(text):
        findings.append({
            "type": "phone",
            "match": match.group(),
            "start": match.start(),
            "end": match.end(),
        })

    for match in _AGE_RE.finditer(text):
        findings.append({
            "type": "age",
            "match": match.group(),
            "start": match.start(),
            "end": match.end(),
        })

    # Sort by position
    findings.sort(key=lambda f: f["start"])
    return findings
