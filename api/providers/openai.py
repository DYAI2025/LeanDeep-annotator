"""OpenAI semantic provider."""

from __future__ import annotations

import json
import logging

from ..semantic import SemanticProfile, TextUnit
from .base import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("leandeep.semantic.openai")


class OpenAISemanticProvider:

    def __init__(self, api_key: str | None, model_name: str = "gpt-4o-mini"):
        self._enabled = False
        self._client = None
        self._model = model_name

        if api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=api_key)
                self._enabled = True
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")

    def is_available(self) -> bool:
        return self._enabled and self._client is not None

    async def profile(self, units: list[TextUnit], language: str = "de") -> list[SemanticProfile]:
        if not self.is_available():
            return []

        prompt = build_user_prompt([(u.index, u.text) for u in units], language)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw = response.choices[0].message.content
        return self._parse(raw, units)

    def _parse(self, raw: str, units: list[TextUnit]) -> list[SemanticProfile]:
        data = json.loads(raw)
        if isinstance(data, dict) and "profiles" in data:
            data = data["profiles"]
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
