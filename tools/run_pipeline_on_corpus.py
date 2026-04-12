"""Run the LeanDeep pipeline on each Gold Standard Corpus dialogue.

Produces prediction files that can be compared against corpus annotations
by tools/eval_gold_standard.py.

Usage:
    uv run python3 tools/run_pipeline_on_corpus.py --corpus-dir build/eval/corpus/ --output build/eval/predictions/
    uv run python3 tools/run_pipeline_on_corpus.py --corpus-dir build/eval/corpus/ --output build/eval/predictions/ --limit 5
"""

import argparse
import json
import sys
import time
from pathlib import Path


def load_corpus_dialogues(corpus_dir: str) -> list[dict]:
    """Load all GS-*.json dialogues from corpus subdirectories."""
    dialogues = []
    base = Path(corpus_dir)
    for subdir in ["real", "amod", "simulated"]:
        d = base / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("GS-*.json")):
            data = json.loads(f.read_text())
            dialogues.append(data)
    return dialogues


def run_pipeline(dialogue: dict) -> dict | None:
    """Run the LeanDeep pipeline on a single dialogue via TestClient.

    Returns the pipeline response dict, or None on failure.
    """
    try:
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        # Build request from dialogue messages
        messages = [{"role": m.get("role", "Client"), "text": m["text"]}
                    for m in dialogue["messages"]]

        response = client.post("/v1/analyze/conversation", json={
            "messages": messages,
            "semantic_mode": "off",  # offline mode, no LLM needed
        })

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ERROR {response.status_code}: {response.text[:200]}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Run LeanDeep pipeline on corpus dialogues")
    parser.add_argument("--corpus-dir", default="build/eval/corpus/", help="Corpus directory")
    parser.add_argument("--output", default="build/eval/predictions/", help="Output directory for predictions")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of dialogues (0 = all)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    dialogues = load_corpus_dialogues(args.corpus_dir)
    if args.limit > 0:
        dialogues = dialogues[:args.limit]

    print(f"Running pipeline on {len(dialogues)} dialogues...")

    success = 0
    failed = 0
    total_ms = 0

    for i, dialogue in enumerate(dialogues):
        did = dialogue["id"]
        print(f"  [{i+1}/{len(dialogues)}] {did}...", end=" ", flush=True)

        start = time.time()
        result = run_pipeline(dialogue)
        elapsed_ms = (time.time() - start) * 1000

        if result is not None:
            # Save prediction
            pred_path = output_dir / f"{did}.json"
            pred_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"OK ({elapsed_ms:.0f}ms)")
            success += 1
            total_ms += elapsed_ms
        else:
            print("FAILED")
            failed += 1

    print(f"\nDone: {success} success, {failed} failed")
    if success > 0:
        print(f"Avg latency: {total_ms / success:.0f}ms")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
