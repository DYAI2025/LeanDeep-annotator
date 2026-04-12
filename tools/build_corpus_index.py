"""Build index.json for the Gold Standard Corpus."""

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path


def scan_corpus_dir(corpus_dir: str) -> list[dict]:
    """Scan corpus subdirectories and load all GS-*.json dialogues."""
    dialogues = []
    base = Path(corpus_dir)
    for subdir in ["real", "amod", "simulated"]:
        d = base / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("GS-*.json")):
            data = json.loads(f.read_text())
            # Store relative path for the index
            data["_path"] = f"{subdir}/{f.name}"
            dialogues.append(data)
    return dialogues


def build_index_from_dialogues(dialogues: list[dict]) -> dict:
    """Build the index structure from loaded dialogues."""
    sources = Counter(d["source"] for d in dialogues)
    languages = Counter(d["language"] for d in dialogues)
    themes = Counter(d["theme"] for d in dialogues)
    review_statuses = Counter(
        d.get("annotations", {}).get("review_status", "unknown") for d in dialogues
    )

    total_messages = sum(
        d.get("metadata", {}).get("message_count", 0) for d in dialogues
    )
    total_chars = sum(d.get("metadata", {}).get("total_chars", 0) for d in dialogues)

    return {
        "version": "1.0",
        "schema": "../schema/dialog_schema.json",
        "created": str(date.today()),
        "stats": {
            "total": len(dialogues),
            "total_messages": total_messages,
            "total_chars": total_chars,
            "by_source": dict(sources),
            "by_language": dict(languages),
            "by_theme": dict(sorted(themes.items())),
            "by_review_status": dict(review_statuses),
        },
        "dialogues": [
            {
                "id": d["id"],
                "path": d.get("_path", f"{d['source']}/{d['id']}.json"),
                "source": d["source"],
                "language": d["language"],
                "theme": d["theme"],
                "message_count": d.get("metadata", {}).get("message_count", 0),
                "review_status": d.get("annotations", {}).get(
                    "review_status", "unknown"
                ),
            }
            for d in dialogues
        ],
    }


def main():
    corpus_dir = sys.argv[1] if len(sys.argv) > 1 else "build/eval/corpus"
    dialogues = scan_corpus_dir(corpus_dir)
    index = build_index_from_dialogues(dialogues)

    output = Path(corpus_dir) / "index.json"
    output.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"Index built: {index['stats']['total']} dialogues → {output}")
    for key, val in index["stats"].items():
        if key.startswith("by_"):
            print(f"  {key}: {val}")


if __name__ == "__main__":
    main()
