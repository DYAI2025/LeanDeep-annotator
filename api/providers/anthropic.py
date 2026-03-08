"""Anthropic semantic provider."""

from __future__ import annotations

import json
import logging

from ..semantic import SemanticProfile, TextUnit
from .base import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("leandeep.semantic.anthropic")


class AnthropicSemanticProvider:

    def __init__(self, api_key: str | None, model_name: str = "claude-haiku-4-5-20251001"):
        self._enabled = False
        self._client = None
        self._model = model_name

        if api_key:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=api_key)
                self._enabled = True
            except Exception as e:
                logger.warning(f"Anthropic init failed: {e}")

    def is_available(self) -> bool:
        return self._enabled and self._client is not None

    async def profile(self, units: list[TextUnit], language: str = "de") -> list[SemanticProfile]:
        if not self.is_available():
            return []

        prompt = build_user_prompt([(u.index, u.text) for u in units], language)

        response = await self._client.messages.create(
            model=self._model,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.1,
        )

        raw = response.content[0].text
        return self._parse(raw, units)

    def _parse(self, raw: str, units: list[TextUnit]) -> list[SemanticProfile]:
        if raw.strip().startswith("```"):
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
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
