"""
Transcript format parser for LeanDeep.

Supports:
- WhatsApp: [DD.MM.YY, HH:MM:SS] Name: text
- Timestamped: HH:MM Name: text  or  HH:MM - Name: text
- Standard: Name: text
- Bracket role: [Name]: text  or  [Name] text
- Unknown fallback: alternating A/B

Also provides AI-based diarization via Gemini for unlabeled transcripts.
"""

from __future__ import annotations

import json
import re


# ---------------------------------------------------------------------------
# Regex patterns for format detection
# ---------------------------------------------------------------------------

# WhatsApp: [12.03.26, 14:23:45] Name: text
_WHATSAPP_RE = re.compile(
    r"^\[\d{1,2}\.\d{1,2}\.\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?\]\s*(.+?):\s*(.*)",
    re.IGNORECASE,
)

# Timestamped: 14:23 Name: text  or  14:23 - Name: text
_TIMESTAMPED_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?\s+(?:-\s+)?(.+?):\s*(.*)"
)

# Bracket role: [Name]: text  or  [Name] text
_BRACKET_RE = re.compile(r"^\[([^\]]+)\](?::\s*|\s+)(.*)")

# Standard colon role: Name: text  (1–25 chars, unicode-aware)
_STANDARD_RE = re.compile(
    r"^([A-Za-z0-9_\s\u00C0-\u024F]{1,25})\s*:\s+(.*)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_transcript(text: str) -> tuple[list[dict], str]:
    """
    Parse a raw transcript string into a list of message dicts.

    Returns:
        (messages, format_detected) where messages are {role: str, text: str}
        and format_detected is one of:
        "whatsapp" | "timestamped" | "bracket" | "standard" | "unknown_alternating"
    """
    lines = [l.rstrip() for l in text.splitlines()]
    lines = [l for l in lines if l.strip()]  # drop blank lines

    if not lines:
        return [], "unknown_alternating"

    # Try each format in priority order
    for fmt, pattern in [
        ("whatsapp", _WHATSAPP_RE),
        ("timestamped", _TIMESTAMPED_RE),
        ("bracket", _BRACKET_RE),
        ("standard", _STANDARD_RE),
    ]:
        messages = _try_parse(lines, pattern)
        if messages and len(messages) >= 1:
            # Accept format if at least 50% of lines matched with a role
            roles_found = sum(1 for m in messages if m["role"] != "__continuation__")
            total = len(messages)
            if roles_found / max(total, 1) >= 0.4:
                # Collapse continuation lines
                return _collapse_continuations(messages), fmt

    # Fallback: alternating A/B
    messages = [
        {"role": "A" if i % 2 == 0 else "B", "text": line.strip()}
        for i, line in enumerate(lines)
    ]
    return messages, "unknown_alternating"


async def diarize_with_ai(text: str, model) -> list[dict]:
    """
    Use Gemini to split an unlabeled transcript into speaker turns.

    Returns a list of {role, text} dicts. Falls back to alternating A/B on failure.
    """
    prompt = (
        "You are a transcript diarization assistant. "
        "The following text is an unlabeled conversation. "
        "Split it into speaker turns and assign each turn a speaker label "
        "(use descriptive names like 'Speaker 1', 'Speaker 2', or infer names from context). "
        "Return ONLY a JSON array with objects {\"role\": \"...\", \"text\": \"...\"}, "
        "one object per turn. No explanation, no markdown, just the JSON array.\n\n"
        f"Transcript:\n{text}"
    )

    try:
        response = await _call_model(model, prompt)
        raw = response.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(
            isinstance(m, dict) and "role" in m and "text" in m for m in parsed
        ):
            return [{"role": str(m["role"]), "text": str(m["text"])} for m in parsed]
    except Exception:
        pass

    # Fallback: alternating A/B
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return [
        {"role": "A" if i % 2 == 0 else "B", "text": line}
        for i, line in enumerate(lines)
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _try_parse(lines: list[str], pattern: re.Pattern) -> list[dict]:
    """Attempt to parse all lines with the given role-extraction pattern."""
    messages = []
    for line in lines:
        m = pattern.match(line)
        if m:
            role = m.group(1).strip()
            content = m.group(2).strip() if len(m.groups()) >= 2 else ""
            messages.append({"role": role, "text": content})
        else:
            # Could be a continuation of the previous message
            messages.append({"role": "__continuation__", "text": line.strip()})
    return messages


def _collapse_continuations(messages: list[dict]) -> list[dict]:
    """Merge __continuation__ entries into the preceding message."""
    result: list[dict] = []
    for msg in messages:
        if msg["role"] == "__continuation__":
            if result:
                result[-1]["text"] += "\n" + msg["text"]
            else:
                # No preceding message — treat as unknown speaker
                result.append({"role": "Unknown", "text": msg["text"]})
        else:
            result.append({"role": msg["role"], "text": msg["text"]})
    return result


async def _call_model(model, prompt: str) -> str:
    """Call the Gemini model asynchronously (handles both sync and async generate_content)."""
    import asyncio
    import inspect

    result = model.generate_content(prompt)
    if inspect.isawaitable(result):
        result = await result
    # Gemini SDK returns a GenerateContentResponse with .text property
    if hasattr(result, "text"):
        return result.text
    return str(result)
