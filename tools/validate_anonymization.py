"""Anonymization validator for dialogue JSON files.

Validates that dialogue files have been properly anonymized by checking
metadata status and scanning message texts for residual PII (names,
phone numbers, email addresses).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from tools.anonymize_dialogue import detect_pii

# ~100 most common German first names (case-sensitive)
_GERMAN_NAMES: set[str] = {
    "Alexander", "Andrea", "Andreas", "Anja", "Anna", "Annett", "Antje",
    "Barbara", "Bernd", "Birgit", "Brigitte",
    "Carmen", "Carsten", "Christian", "Christina", "Christine", "Christoph",
    "Claudia", "Cornelia",
    "Daniel", "Daniela", "Dennis", "Diana", "Dieter", "Dirk", "Doreen",
    "Eva",
    "Florian", "Frank", "Franziska",
    "Gabriele", "Hans", "Heike", "Holger",
    "Ines", "Ingo",
    "Jan", "Jana", "Jens", "Jessica", "Joerg", "Julia", "Juergen",
    "Kai", "Karen", "Karin", "Karsten", "Katharina", "Kathrin", "Katja",
    "Katrin", "Kerstin", "Klaus",
    "Lars", "Lisa", "Lukas",
    "Manfred", "Manuela", "Marc", "Marcel", "Marco", "Marcus", "Maria",
    "Mario", "Markus", "Martin", "Martina", "Matthias", "Melanie",
    "Michael", "Monika",
    "Nadine", "Nicole", "Norbert",
    "Oliver",
    "Patrick", "Paul", "Peter", "Petra",
    "Ralf", "Regina", "Rene", "Robert", "Roland", "Rolf",
    "Sabine", "Sandra", "Sascha", "Sebastian", "Silke", "Simone",
    "Sonja", "Stefan", "Stefanie", "Steffen", "Stephanie", "Susanne",
    "Sven",
    "Tanja", "Thomas", "Thorsten", "Tobias", "Torsten",
    "Udo", "Ulrike", "Ursula", "Uwe",
    "Volker",
    "Werner", "Wolfgang",
}

# Terms that look like names but are therapeutic/technical vocabulary
_THERAPEUTIC_ALLOWLIST: set[str] = {
    "Ego", "State", "Borderline", "Trauma", "Hypnose", "Ketamin",
    "Therapie", "Psychotherapie", "Verhaltenstherapie", "Tiefenpsychologie",
    "EMDR", "PTBS", "Dissoziation", "Schizophrenie", "Depression",
    "Angst", "Bipolar", "Narzissmus", "Psychose", "Panik",
    "Diagnostik", "Intervention", "Resilienz", "Achtsamkeit",
    "Mentalisierung", "Affektregulation", "Suizidalitaet",
}

# Pseudonym patterns that should not be flagged
_PSEUDONYM_RE = re.compile(
    r"^(?:P\d+|\[[\w_]+\])$"
)

# Name boundary pattern: match whole words only
_NAME_BOUNDARY = re.compile(
    r"(?<![A-Za-zÄÖÜäöüß-])({names})(?![A-Za-zÄÖÜäöüß-])".format(
        names="|".join(re.escape(n) for n in sorted(_GERMAN_NAMES, key=lambda x: -len(x)))
    )
)


def _scan_names(text: str) -> list[dict[str, Any]]:
    """Find German first names in text, excluding therapeutic terms."""
    findings: list[dict[str, Any]] = []
    for match in _NAME_BOUNDARY.finditer(text):
        name = match.group()
        if name in _THERAPEUTIC_ALLOWLIST:
            continue
        # Skip if embedded in a compound word with hyphens (e.g., "Ego-State-Therapie")
        findings.append({
            "type": "name",
            "match": name,
            "start": match.start(),
            "end": match.end(),
        })
    return findings


def validate_dialogue(dialogue: dict[str, Any]) -> list[str]:
    """Validate that a dialogue JSON has been properly anonymized.

    Args:
        dialogue: Dialogue dict with 'metadata' and 'messages' keys.

    Returns:
        List of error strings. Empty list means the dialogue is valid.
    """
    errors: list[str] = []

    # Check metadata.anonymization exists
    metadata = dialogue.get("metadata", {})
    anon = metadata.get("anonymization")
    if anon is None:
        errors.append("Missing 'metadata.anonymization' field.")
        return errors

    # Check status
    status = anon.get("status", "")
    if status == "raw":
        errors.append("Dialogue has status 'raw' — not anonymized.")
        return errors

    # Synthetic dialogues skip PII checks (never contained real data)
    if status == "synthetic":
        return errors

    # For 'anonymized' status, scan all message texts for residual PII
    messages = dialogue.get("messages", [])
    for i, msg in enumerate(messages):
        text = msg.get("text", "")
        if not text:
            continue

        # Check for names
        name_findings = _scan_names(text)
        for finding in name_findings:
            errors.append(
                f"msg[{i}]: Possible name '{finding['match']}' found at position {finding['start']}."
            )

        # Check for phone/email using detect_pii from anonymize_dialogue
        pii_findings = detect_pii(text)
        for finding in pii_findings:
            if finding["type"] in ("email", "phone"):
                errors.append(
                    f"msg[{i}]: {finding['type'].capitalize()} pattern '{finding['match']}' "
                    f"found at position {finding['start']}."
                )

    return errors


def validate_corpus_dir(dir_path: str) -> dict[str, list[str]]:
    """Validate all GS-*.json files in a directory.

    Args:
        dir_path: Path to directory containing gold standard dialogue files.

    Returns:
        Dict mapping filename to list of errors (empty list = valid).
    """
    results: dict[str, list[str]] = {}
    corpus_dir = Path(dir_path)

    if not corpus_dir.is_dir():
        return {dir_path: [f"Directory not found: {dir_path}"]}

    for json_file in sorted(corpus_dir.glob("GS-*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                dialogue = json.load(f)
            results[json_file.name] = validate_dialogue(dialogue)
        except json.JSONDecodeError as exc:
            results[json_file.name] = [f"Invalid JSON: {exc}"]
        except Exception as exc:
            results[json_file.name] = [f"Error reading file: {exc}"]

    return results


def main() -> None:
    """CLI entry point: validate corpus directory."""
    if len(sys.argv) < 2:
        print("Usage: python tools/validate_anonymization.py <corpus_dir>")
        sys.exit(1)

    dir_path = sys.argv[1]
    results = validate_corpus_dir(dir_path)

    if not results:
        print(f"No GS-*.json files found in {dir_path}")
        sys.exit(1)

    has_errors = False
    for filename, errors in results.items():
        if errors:
            has_errors = True
            print(f"FAIL  {filename}")
            for error in errors:
                print(f"      - {error}")
        else:
            print(f"PASS  {filename}")

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
