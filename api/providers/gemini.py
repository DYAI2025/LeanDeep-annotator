"""Gemini semantic provider (uses google-genai SDK)."""

from __future__ import annotations

import json
import logging

from ..semantic import SemanticProfile, SemanticProvider, TextUnit
from .base import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("leandeep.semantic.gemini")


class GeminiSemanticProvider:
    """Google Gemini provider for semantic profiling."""

    def __init__(self, api_key: str | None, model_name: str = "gemini-1.5-flash-8b"):
        self._enabled = False
        self._client = None
        self._model_name = model_name
        self._api_key = api_key

        if api_key:
            try:
                from google import genai  # noqa: F401 — verify import works
                self._enabled = True
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    def is_available(self) -> bool:
        return self._enabled and bool(self._api_key)

    async def profile(
        self,
        units: list[TextUnit],
        language: str = "de",
    ) -> list[SemanticProfile]:
        if not self.is_available():
            return []

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)
            prompt = self._build_prompt(units, language)

            response = await client.aio.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            return self._parse_response(response.text, units)
        except Exception as e:
            logger.warning(f"Gemini profile failed: {e}")
            return []

    def _build_prompt(self, units: list[TextUnit], language: str) -> str:
        units_text = [(u.index, u.text) for u in units]
        return build_user_prompt(units_text, language)

    def _parse_response(
        self, raw_json: str, units: list[TextUnit]
    ) -> list[SemanticProfile]:
        data = json.loads(raw_json)
        if not isinstance(data, list):
            data = [data]

        span_map = {u.index: u.span for u in units}

        profiles = []
        for item in data:
            idx = item.get("index", 0)
            span = span_map.get(idx, (0, 0))
            profiles.append(SemanticProfile(
                intent=item.get("intent", "unknown"),
                intent_confidence=0.9,
                register=item.get("register", "informell"),
                emotion_primary=item.get("emotion_primary", "neutral"),
                emotion_secondary=item.get("emotion_secondary"),
                ironie=item.get("ironie", False),
                ironie_confidence=item.get("ironie_confidence", 0.0),
                selbst_fremd=item.get("selbst_fremd", "unpersoenlich"),
                beziehungsdynamik=item.get("beziehungsdynamik", "neutral"),
                pre_context=item.get("pre_context"),
                tension=item.get("tension", 0.0),
                source="llm",
                text_span=span,
            ))

        return profiles
