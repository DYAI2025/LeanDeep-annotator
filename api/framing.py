"""
Semantic Framing Layer for LeanDeep 6.0.

Generates a dialogue-level SemanticFrame (7 dimensions) using LLM providers.
Runs in parallel with ATO detection per the architecture.

The SemanticFrame contextualizes interpretation:
  - tone, themes, relational_dynamics, intent, emotional_tenor
  - context_validity: how self-contained the dialogue is
  - offline_context_risk: how much depends on invisible external context

See: REQ-F-semantic-framing, DEC-semantic-guided-multi-perspective-architecture
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

from .config import settings
from .semantic_frame import SemanticFrame

logger = logging.getLogger("leandeep.framing")

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

FRAMING_SYSTEM_PROMPT = """\
You are a semantic analysis engine for dialogue interpretation.
Your task is to generate a structured semantic frame for the given dialogue.
You MUST return valid JSON with exactly these 7 fields — no additional fields."""

FRAMING_USER_PROMPT = """\
Analyze this dialogue and extract a semantic frame.

Dialogue:
{dialogue_text}

Return a JSON object with these exact fields:

1. "tone": 2-3 adjectives describing overall conversational tone
   Examples: "hesitant, uncertain", "aggressive, demanding", "open, collaborative"

2. "themes": list of primary topic clusters (2-5 items)
   Examples: ["self-doubt", "decision-making"], ["trust-building", "negotiation"]

3. "relational_dynamics": description of relationship pattern (single string)
   Examples: "seeking-support", "adversarial", "exploratory", "power-imbalanced"

4. "intent": primary conversational goal/intent (single string)
   Examples: "information-seeking", "persuasion", "connection", "conflict-resolution"

5. "emotional_tenor": continuous score from -1.0 (very negative) to +1.0 (very positive)

6. "context_validity": score 0.0-1.0
   How many references within the dialogue are internally resolvable?
   1.0 = all references self-contained, 0.0 = nothing self-explanatory

7. "offline_context_risk": score 0.0-1.0
   What percentage of emotional/logical tensions likely originate from invisible context?
   1.0 = almost all tensions point to hidden context, 0.0 = all explained within dialogue

Return ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class _FrameCache:
    """In-memory frame cache with TTL. Keyed by dialogue text hash."""

    def __init__(self, ttl_seconds: int = 86400, max_size: int = 10000):
        self._store: dict[str, tuple[SemanticFrame, float]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    @staticmethod
    def _key(messages: list[dict]) -> str:
        text = "\n".join(f"{m.get('role', '')}: {m.get('text', '')}" for m in messages)
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, messages: list[dict]) -> SemanticFrame | None:
        key = self._key(messages)
        entry = self._store.get(key)
        if entry is None:
            return None
        frame, ts = entry
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        return frame

    def put(self, messages: list[dict], frame: SemanticFrame) -> None:
        if len(self._store) >= self._max_size:
            # Evict oldest entry
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]
        key = self._key(messages)
        self._store[key] = (frame, time.time())

    def invalidate(self) -> None:
        self._store.clear()


_cache = _FrameCache()


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class SemanticFrameGenerator:
    """Generates dialogue-level SemanticFrame using Gemini (or configured provider)."""

    def __init__(self):
        self.enabled = bool(settings.google_api_key)
        self._model = None  # genai.GenerativeModel instance

        if self.enabled:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self._model = genai.GenerativeModel(settings.reasoning_model)
            except ImportError:
                logger.warning("google-generativeai not installed. Semantic framing disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for framing: {e}")
                self.enabled = False

    async def generate(
        self,
        messages: list[dict],
        language: str = "de",
    ) -> SemanticFrame | None:
        """Generate a SemanticFrame for the entire dialogue.

        Returns cached frame if available. Returns None if no LLM is configured.
        """
        if not self.enabled or not self._model:
            return None

        # Check cache
        cached = _cache.get(messages)
        if cached is not None:
            logger.debug("Frame cache hit")
            return cached

        dialogue_text = self._format_dialogue(messages)
        prompt = FRAMING_USER_PROMPT.format(dialogue_text=dialogue_text)

        try:
            raw_json = await self._call_llm(prompt)
            frame = self._parse_response(raw_json)
            _cache.put(messages, frame)
            return frame

        except Exception as e:
            logger.warning(f"Semantic framing failed: {e}")
            return None

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM asynchronously and return raw JSON response text."""
        full_prompt = f"{FRAMING_SYSTEM_PROMPT}\n\n{prompt}"
        response = await self._model.generate_content_async(
            full_prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text

    def _format_dialogue(self, messages: list[dict]) -> str:
        return "\n".join(
            f"{m.get('role', '?')}: {m.get('text', '')}"
            for m in messages
        )

    def _parse_response(self, raw_json: str) -> SemanticFrame:
        data = json.loads(raw_json)
        return SemanticFrame(
            tone=str(data.get("tone", "")),
            themes=data.get("themes", []),
            relational_dynamics=str(data.get("relational_dynamics", "")),
            intent=str(data.get("intent", "")),
            emotional_tenor=_clamp(float(data.get("emotional_tenor", 0.0)), -1.0, 1.0),
            context_validity=_clamp(float(data.get("context_validity", 0.5)), 0.0, 1.0),
            offline_context_risk=_clamp(float(data.get("offline_context_risk", 0.5)), 0.0, 1.0),
        )


def _clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def get_frame_cache() -> _FrameCache:
    """Access the module-level frame cache (for invalidation on registry reload)."""
    return _cache


# Module-level singleton (matches pattern used by narrative.py)
frame_generator = SemanticFrameGenerator()
