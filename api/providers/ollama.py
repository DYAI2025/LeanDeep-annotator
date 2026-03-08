"""Ollama (local LLM) semantic provider."""

from __future__ import annotations

import json
import logging

from ..semantic import SemanticProfile, TextUnit
from .base import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("leandeep.semantic.ollama")


class OllamaSemanticProvider:

    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self._model = model_name
        self._base_url = base_url
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import urllib.request
            urllib.request.urlopen(f"{self._base_url}/api/tags", timeout=2)
            self._available = True
        except Exception:
            self._available = False
        return self._available

    async def profile(self, units: list[TextUnit], language: str = "de") -> list[SemanticProfile]:
        if not self.is_available():
            return []

        import httpx
        prompt = build_user_prompt([(u.index, u.text) for u in units], language)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]

        return self._parse(raw, units)

    def _parse(self, raw: str, units: list[TextUnit]) -> list[SemanticProfile]:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
        span_map = {u.index: u.span for u in units}
        return [
            SemanticProfile(
                intent=d.get("intent", "unknown"),
                intent_confidence=0.9,
                register=d.get("register", "informell"),
                emotion_primary=d.get("emotion_primary", "neutral"),
                emotion_secondary=d.get("emotion_secondary"),
                ironie=d.get("ironie", False),
                ironie_confidence=d.get("ironie_confidence", 0.0),
                selbst_fremd=d.get("selbst_fremd", "unpersoenlich"),
                beziehungsdynamik=d.get("beziehungsdynamik", "neutral"),
                pre_context=d.get("pre_context"),
                tension=d.get("tension", 0.0),
                source="llm",
                text_span=span_map.get(d.get("index", i), (0, 0)),
            )
            for i, d in enumerate(data)
        ]
