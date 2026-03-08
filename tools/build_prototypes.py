"""Build embedding prototypes for all markers with sufficient examples.

Usage:
    python3 tools/build_prototypes.py [--model MODEL] [--min-examples N]

Reads: build/markers_normalized/marker_registry.json
Writes: build/marker_prototypes.npz
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Build marker embedding prototypes")
    parser.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--min-examples", type=int, default=10)
    parser.add_argument("--registry", default="build/markers_normalized/marker_registry.json")
    parser.add_argument("--output", default="build/marker_prototypes.npz")
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer

    print(f"Loading model: {args.model}")
    model = SentenceTransformer(args.model)

    print(f"Loading registry: {args.registry}")
    registry = json.loads(Path(args.registry).read_text())

    ids = []
    vectors = []
    skipped = 0

    for marker in registry["markers"]:
        mid = marker["id"]
        examples = marker.get("examples", {})

        # Collect positive examples (try both field naming conventions)
        positives = (
            examples.get("positive", []) or
            examples.get("positive_de", []) or []
        )
        negatives = (
            examples.get("negative", []) or
            examples.get("negative_de", []) or []
        )

        if len(positives) < args.min_examples:
            skipped += 1
            continue

        # Compute centroids
        pos_emb = model.encode(positives, normalize_embeddings=True)
        centroid_pos = pos_emb.mean(axis=0)

        if len(negatives) >= 5:
            neg_emb = model.encode(negatives, normalize_embeddings=True)
            centroid_neg = neg_emb.mean(axis=0)
            prototype = centroid_pos - 0.3 * centroid_neg
        else:
            prototype = centroid_pos

        # Normalize
        prototype = prototype / np.linalg.norm(prototype)

        ids.append(mid)
        vectors.append(prototype)

    ids_arr = np.array(ids)
    vecs_arr = np.array(vectors, dtype=np.float32)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.output, ids=ids_arr, vectors=vecs_arr)

    print(f"Built {len(ids)} prototypes, skipped {skipped} (< {args.min_examples} examples)")
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
