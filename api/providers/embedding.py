"""Embedding-based semantic fallback provider."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from ..semantic import SemanticProfile, TextUnit

logger = logging.getLogger("leandeep.semantic.embedding")


class EmbeddingProvider:
    """Fallback provider using sentence embeddings + marker prototypes."""

    def __init__(
        self,
        prototypes_path: str = "build/marker_prototypes.npz",
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        threshold: float = 0.45,
    ):
        self._threshold = threshold
        self._model = None
        self._proto_ids: np.ndarray | None = None
        self._proto_vecs: np.ndarray | None = None

        path = Path(prototypes_path)
        if path.exists():
            try:
                data = np.load(path, allow_pickle=True)
                self._proto_ids = data["ids"]
                self._proto_vecs = data["vectors"]
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(model_name)
            except Exception as e:
                logger.warning(f"Embedding provider init failed: {e}")

    def is_available(self) -> bool:
        return self._model is not None and self._proto_vecs is not None

    async def profile(
        self, units: list[TextUnit], language: str = "de"
    ) -> list[SemanticProfile]:
        if not self.is_available():
            return []

        texts = [u.text for u in units]
        embeddings = self._model.encode(texts, normalize_embeddings=True)

        profiles = []
        for i, (unit, emb) in enumerate(zip(units, embeddings)):
            # Cosine similarity (vectors are normalized)
            sims = emb @ self._proto_vecs.T
            top_mask = sims >= self._threshold
            whitelist = list(self._proto_ids[top_mask])
            top_score = float(sims.max()) if len(sims) > 0 else 0.0

            p = SemanticProfile(
                intent="unknown",
                intent_confidence=0.0,
                register="informell",
                emotion_primary="neutral",
                emotion_secondary=None,
                ironie=False,
                ironie_confidence=0.0,
                selbst_fremd="unpersoenlich",
                beziehungsdynamik="neutral",
                pre_context=None,
                tension=min(1.0, top_score),
                source="embedding",
                text_span=unit.span,
            )
            # Attach whitelist as internal attribute for the semantic gate
            p._marker_whitelist = set(whitelist)
            profiles.append(p)

        return profiles
