"""Gemini semantic provider."""

from __future__ import annotations

import json
import logging

from ..semantic import SemanticProfile, SemanticProvider, TextUnit
from .base import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("leandeep.semantic.gemini")


class GeminiSemanticProvider:
    """Google Gemini provider for semantic profiling."""

    def __init__(self, api_key: str | None, model_name: str = "gemini-2.0-flash"):
        self._enabled = False
        self._model = None

        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(
                    model_name,
                    system_instruction=SYSTEM_PROMPT,
                )
                self._enabled = True
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    def is_available(self) -> bool:
        return self._enabled and self._model is not None

    async def profile(
        self,
        units: list[TextUnit],
        language: str = "de",
    ) -> list[SemanticProfile]:
        if not self.is_available():
            return []

        prompt = self._build_prompt(units, language)

        response = await self._model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        return self._parse_response(response.text, units)

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
