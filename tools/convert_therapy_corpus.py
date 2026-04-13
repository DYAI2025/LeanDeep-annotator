#!/usr/bin/env python3
"""Convert therapy transcripts into LeanDeep-compatible eval corpus format.

Supports:
  1. Whisper/diarization JSON (segments with speaker + timestamps)
  2. SRT-style text transcripts (timestamp --> speaker format)
  3. Amod combined_dataset JSONL (Context/Response pairs)

Output: Gold-standard corpus JSON compatible with tools/eval_semantic_framing.py

Usage:
    # Convert KAH EGOSTATE transcript
    python tools/convert_therapy_corpus.py \
        --input dialoge-therapie/"KAH EGOSTATE.m4a.json" \
        --format whisper-json \
        --id GS-KAH-001 \
        --output build/eval/gold_standard.json

    # Convert Amod dataset (deduplicated)
    python tools/convert_therapy_corpus.py \
        --input dialoge-therapie/combined_dataset.json \
        --format amod-jsonl \
        --output build/eval/amod_corpus.json \
        --limit 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def convert_whisper_json(path: str, dialogue_id: str) -> dict:
    """Convert Whisper/diarization JSON to LeanDeep messages format.

    Groups consecutive segments by the same speaker into single messages.
    Preserves timestamps as metadata.
    """
    with open(path) as f:
        data = json.load(f)

    segments = data.get("segments", [])
    if not segments:
        print(f"ERROR: No segments in {path}", file=sys.stderr)
        sys.exit(1)

    messages: list[dict] = []
    current_speaker = None
    current_text = ""
    current_start = 0.0

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        speaker_info = seg.get("speaker", {})
        speaker_id = speaker_info.get("name", "Unknown") if isinstance(speaker_info, dict) else str(speaker_info)
        start_time = seg.get("start_time", 0.0)

        if speaker_id == current_speaker:
            current_text += " " + text
        else:
            if current_speaker and current_text.strip():
                messages.append({
                    "role": _normalize_speaker(current_speaker),
                    "text": current_text.strip(),
                    "start_time": current_start,
                })
            current_speaker = speaker_id
            current_text = text
            current_start = start_time

    # Flush last message
    if current_speaker and current_text.strip():
        messages.append({
            "role": _normalize_speaker(current_speaker),
            "text": current_text.strip(),
            "start_time": current_start,
        })

    # Detect language from content
    de_markers = sum(1 for m in messages[:20] if any(w in m["text"].lower() for w in ["ich ", "und ", "nicht ", "aber ", "das "]))
    language = "de" if de_markers > len(messages[:20]) * 0.3 else "en"

    duration = segments[-1].get("end_time", 0.0) if segments else 0.0
    speakers = sorted({m["role"] for m in messages})

    return {
        "id": dialogue_id,
        "messages": messages,
        "language": language,
        "metadata": {
            "source": Path(path).name,
            "duration_seconds": round(duration, 1),
            "speakers": speakers,
            "message_count": len(messages),
            "total_chars": sum(len(m["text"]) for m in messages),
        },
        "rater_a": _empty_annotation(),
        "rater_b": _empty_annotation(),
        "notes": "Converted from Whisper/diarization JSON. Annotations pending.",
    }


def convert_amod_jsonl(path: str, limit: int = 100) -> list[dict]:
    """Convert Amod combined_dataset JSONL to LeanDeep messages format.

    Deduplicates by Context, takes first `limit` unique entries.
    Each Context/Response pair becomes a 2-message dialogue.
    """
    entries = []
    seen_contexts: set[str] = set()

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            ctx = entry.get("Context", "").strip()
            resp = entry.get("Response", "").strip()
            if not ctx or not resp or ctx in seen_contexts:
                continue
            seen_contexts.add(ctx)
            entries.append({"context": ctx, "response": resp})
            if len(entries) >= limit:
                break

    dialogues = []
    for i, entry in enumerate(entries):
        dialogues.append({
            "id": f"GS-AMOD-{i+1:03d}",
            "messages": [
                {"role": "Client", "text": entry["context"]},
                {"role": "Therapist", "text": entry["response"]},
            ],
            "language": "en",
            "metadata": {
                "source": "Amod/mental_health_counseling_conversations",
                "message_count": 2,
            },
            "rater_a": _empty_annotation(),
            "rater_b": _empty_annotation(),
            "notes": "Converted from Amod dataset. Annotations pending.",
        })

    return dialogues


def _normalize_speaker(raw: str) -> str:
    """Normalize speaker labels to short role identifiers."""
    mapping = {
        "Speaker 0": "S0",
        "Speaker 1": "S1",
        "Speaker 2": "S2",
        "Speaker 3": "S3",
        "Speaker 4": "S4",
    }
    return mapping.get(raw, raw)


def _empty_annotation() -> dict:
    """Return an empty annotation template for a rater."""
    return {
        "tone": "",
        "themes": [],
        "relational_dynamics": "",
        "intent": "",
        "emotional_tenor": 0.0,
        "context_validity": 0.0,
        "offline_context_risk": 0.0,
    }


def build_corpus(dialogues: list[dict], existing_path: str | None = None) -> dict:
    """Build or extend a gold-standard corpus JSON.

    If existing_path is provided and the file exists, appends new dialogues
    (skipping IDs that already exist).
    """
    existing_dialogues = []
    if existing_path:
        p = Path(existing_path)
        if p.exists():
            with open(p) as f:
                existing = json.load(f)
            existing_dialogues = existing.get("dialogues", [])

    existing_ids = {d["id"] for d in existing_dialogues}
    new_dialogues = [d for d in dialogues if d["id"] not in existing_ids]

    all_dialogues = existing_dialogues + new_dialogues

    return {
        "_doc": "Gold Standard Corpus for ASM-ki-semantic-framing-sufficient verification.",
        "_format_version": "1.0",
        "_dimensions": {
            "tone": "Free text label. Normalized to lowercase.",
            "themes": "List of theme labels. Multi-label F1.",
            "relational_dynamics": "Free text label.",
            "intent": "Free text label.",
            "emotional_tenor": "Float -1.0 to 1.0.",
            "context_validity": "Float 0.0 to 1.0.",
            "offline_context_risk": "Float 0.0 to 1.0.",
        },
        "dialogues": all_dialogues,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert therapy transcripts to LeanDeep eval format")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--format", required=True, choices=["whisper-json", "amod-jsonl"],
                        help="Input format")
    parser.add_argument("--id", default="GS-001", help="Dialogue ID (for whisper-json)")
    parser.add_argument("--output", required=True, help="Output corpus JSON path")
    parser.add_argument("--limit", type=int, default=100, help="Max entries (for amod-jsonl)")
    parser.add_argument("--append", action="store_true",
                        help="Append to existing corpus instead of overwriting")
    args = parser.parse_args()

    if args.format == "whisper-json":
        dialogue = convert_whisper_json(args.input, args.id)
        dialogues = [dialogue]
        print(f"Converted 1 dialogue: {dialogue['id']} ({dialogue['metadata']['message_count']} messages, "
              f"{dialogue['metadata']['duration_seconds']}s, {dialogue['language']})")
    elif args.format == "amod-jsonl":
        dialogues = convert_amod_jsonl(args.input, limit=args.limit)
        print(f"Converted {len(dialogues)} dialogues from Amod dataset (deduplicated, limit={args.limit})")

    existing = args.output if args.append else None
    corpus = build_corpus(dialogues, existing_path=existing)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    print(f"Corpus written to {args.output} ({len(corpus['dialogues'])} total dialogues)")


if __name__ == "__main__":
    main()
