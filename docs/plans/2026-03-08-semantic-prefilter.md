# Semantic Pre-Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a semantic profiling layer (Layer 0) before the detection engine that uses LLM or embedding fallback to produce 8-dimension profiles, enabling nuance-aware marker gating.

**Architecture:** Provider-agnostic SemanticProfiler produces SemanticProfile per text unit. Engine gets a new Semantic Gate between ATO detection and VAD gate. Embedding prototypes serve as offline fallback.

**Tech Stack:** Python 3.12, FastAPI, pydantic, google-generativeai, openai, anthropic, sentence-transformers, numpy

**Design Doc:** `docs/plans/2026-03-08-semantic-prefilter-design.md`

---

### Task 1: SemanticProfile Schema + Provider Protocol

**Files:**
- Create: `api/semantic.py`
- Modify: `api/models.py` (add response models)
- Test: `tests/test_semantic.py`

**Step 1: Write the failing test**

```python
# tests/test_semantic.py
"""Tests for SemanticProfile and provider protocol."""

def test_semantic_profile_creation():
    from api.semantic import SemanticProfile
    p = SemanticProfile(
        intent="vorwurf",
        intent_confidence=0.9,
        register="intim",
        emotion_primary="wut",
        emotion_secondary="trauer",
        ironie=False,
        ironie_confidence=0.05,
        selbst_fremd="selbst",
        beziehungsdynamik="naehe_suche",
        pre_context="Wiederholter Vertrauensbruch",
        tension=0.72,
        source="llm",
        text_span=(0, 50),
    )
    assert p.intent == "vorwurf"
    assert p.tension == 0.72
    assert p.source == "llm"


def test_semantic_profile_defaults():
    from api.semantic import SemanticProfile
    p = SemanticProfile(
        intent="neutral",
        intent_confidence=0.5,
        register="informell",
        emotion_primary="neutral",
        emotion_secondary=None,
        ironie=False,
        ironie_confidence=0.0,
        selbst_fremd="unpersoenlich",
        beziehungsdynamik="neutral",
        pre_context=None,
        tension=0.0,
        source="none",
        text_span=(0, 10),
    )
    assert p.emotion_secondary is None
    assert p.pre_context is None


def test_semantic_profiler_fallback_chain():
    """Profiler with no providers should return empty profiles with source='none'."""
    from api.semantic import SemanticProfiler, TextUnit
    profiler = SemanticProfiler(providers=[])
    units = [TextUnit(text="Hallo Welt", index=0, span=(0, 10))]
    import asyncio
    profiles = asyncio.run(profiler.profile(units, language="de"))
    assert len(profiles) == 1
    assert profiles[0].source == "none"


def test_text_unit_from_single_text():
    from api.semantic import TextUnit
    units = TextUnit.from_text("Erster Satz. Zweiter Satz. Dritter Satz.")
    assert len(units) >= 2
    assert units[0].text.strip().startswith("Erster")


def test_text_unit_from_messages():
    from api.semantic import TextUnit
    messages = [
        {"role": "A", "text": "Hallo wie gehts"},
        {"role": "B", "text": "Gut und dir"},
    ]
    units = TextUnit.from_messages(messages)
    assert len(units) == 2
    assert units[0].index == 0
    assert units[1].index == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_semantic.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'api.semantic'`

**Step 3: Write minimal implementation**

```python
# api/semantic.py
"""
Semantic Profiling Layer (Layer 0) for LeanDeep 6.0.

Produces 8-dimension SemanticProfiles per text unit using
LLM providers (primary) or embedding prototypes (fallback).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("leandeep.semantic")


# ---------------------------------------------------------------------------
# SemanticProfile
# ---------------------------------------------------------------------------

VALID_INTENTS = {
    "vorwurf", "bitte", "rechtfertigung", "frage",
    "feststellung", "drohung", "reparatur", "smalltalk", "neutral", "unknown",
}

VALID_REGISTERS = {
    "intim", "informell", "formal", "technisch", "therapeutisch",
}

VALID_EMOTIONS = {
    "wut", "trauer", "angst", "freude", "verachtung",
    "ueberraschung", "ekel", "neutral",
}

VALID_SELBST_FREMD = {"selbst", "fremd", "unpersoenlich"}

VALID_BEZIEHUNGSDYNAMIK = {
    "naehe_suche", "distanzierung", "kontrolle",
    "unterwerfung", "kooperation", "neutral",
}


@dataclass
class SemanticProfile:
    """Semantic profile for a single text unit (sentence or message)."""

    intent: str
    intent_confidence: float
    register: str
    emotion_primary: str
    emotion_secondary: str | None
    ironie: bool
    ironie_confidence: float
    selbst_fremd: str
    beziehungsdynamik: str
    pre_context: str | None
    tension: float
    source: str          # "llm", "embedding", "none"
    text_span: tuple[int, int]

    @staticmethod
    def empty(span: tuple[int, int] = (0, 0)) -> SemanticProfile:
        """Return a neutral/empty profile (no semantic data available)."""
        return SemanticProfile(
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
            tension=0.0,
            source="none",
            text_span=span,
        )


# ---------------------------------------------------------------------------
# TextUnit
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


@dataclass
class TextUnit:
    """A chunk of text to be profiled (sentence or message)."""

    text: str
    index: int
    span: tuple[int, int]

    @staticmethod
    def from_text(text: str) -> list[TextUnit]:
        """Split single text into sentence-level units."""
        parts = _SENTENCE_SPLIT.split(text.strip())
        units = []
        offset = 0
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            start = text.find(part, offset)
            if start == -1:
                start = offset
            end = start + len(part)
            units.append(TextUnit(text=part, index=i, span=(start, end)))
            offset = end
        return units if units else [TextUnit(text=text, index=0, span=(0, len(text)))]

    @staticmethod
    def from_messages(messages: list[dict]) -> list[TextUnit]:
        """Create one TextUnit per message."""
        units = []
        offset = 0
        for i, msg in enumerate(messages):
            t = msg.get("text", "")
            units.append(TextUnit(text=t, index=i, span=(offset, offset + len(t))))
            offset += len(t) + 1
        return units


# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class SemanticProvider(Protocol):
    """Interface that every LLM/embedding provider implements."""

    async def profile(
        self,
        units: list[TextUnit],
        language: str,
    ) -> list[SemanticProfile]:
        ...

    def is_available(self) -> bool:
        ...


# ---------------------------------------------------------------------------
# SemanticProfiler (orchestrator)
# ---------------------------------------------------------------------------

class SemanticProfiler:
    """Orchestrates semantic profiling with fallback chain."""

    def __init__(self, providers: list[SemanticProvider] | None = None):
        self.providers = providers or []

    async def profile(
        self,
        units: list[TextUnit],
        language: str = "de",
    ) -> list[SemanticProfile]:
        """Profile text units using first available provider."""
        for provider in self.providers:
            if provider.is_available():
                try:
                    result = await provider.profile(units, language)
                    if result and len(result) == len(units):
                        return result
                except Exception as e:
                    logger.warning(f"Provider {type(provider).__name__} failed: {e}")
                    continue

        # No provider available -> empty profiles
        return [SemanticProfile.empty(u.span) for u in units]
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_semantic.py -v`
Expected: 5 PASS

**Step 5: Commit**

```bash
git add api/semantic.py tests/test_semantic.py
git commit -m "feat: add SemanticProfile schema, TextUnit, and SemanticProfiler with provider protocol"
```

---

### Task 2: Gemini Provider

**Files:**
- Create: `api/providers/__init__.py`
- Create: `api/providers/base.py`
- Create: `api/providers/gemini.py`
- Modify: `api/config.py` (add semantic settings)
- Test: `tests/test_providers.py`

**Step 1: Write the failing test**

```python
# tests/test_providers.py
"""Tests for semantic providers."""
import json


def test_gemini_provider_prompt_construction():
    """Test that the Gemini provider builds correct prompts."""
    from api.providers.gemini import GeminiSemanticProvider
    from api.semantic import TextUnit
    provider = GeminiSemanticProvider.__new__(GeminiSemanticProvider)
    provider._model = None
    provider._enabled = False
    units = [
        TextUnit(text="Du hoerst mir nie zu!", index=0, span=(0, 21)),
        TextUnit(text="Das stimmt nicht.", index=1, span=(22, 39)),
    ]
    prompt = provider._build_prompt(units, "de")
    assert "[0]" in prompt
    assert "[1]" in prompt
    assert "Du hoerst mir nie zu!" in prompt
    assert "intent" in prompt
    assert "tension" in prompt


def test_gemini_provider_parse_response():
    """Test JSON response parsing into SemanticProfiles."""
    from api.providers.gemini import GeminiSemanticProvider
    from api.semantic import TextUnit
    provider = GeminiSemanticProvider.__new__(GeminiSemanticProvider)
    units = [TextUnit(text="Test", index=0, span=(0, 4))]
    raw = json.dumps([{
        "index": 0,
        "intent": "feststellung",
        "register": "informell",
        "emotion_primary": "neutral",
        "emotion_secondary": None,
        "ironie": False,
        "ironie_confidence": 0.0,
        "selbst_fremd": "unpersoenlich",
        "beziehungsdynamik": "neutral",
        "pre_context": None,
        "tension": 0.1,
    }])
    profiles = provider._parse_response(raw, units)
    assert len(profiles) == 1
    assert profiles[0].intent == "feststellung"
    assert profiles[0].source == "llm"
    assert profiles[0].text_span == (0, 4)


def test_gemini_provider_not_available_without_key():
    from api.providers.gemini import GeminiSemanticProvider
    provider = GeminiSemanticProvider(api_key=None, model_name="gemini-2.0-flash")
    assert provider.is_available() is False


def test_provider_registry():
    from api.providers import build_provider_chain
    chain = build_provider_chain(
        provider_name=None,
        api_key=None,
        model_name=None,
    )
    # With no key, should still return a list (possibly empty or embedding-only)
    assert isinstance(chain, list)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# api/providers/__init__.py
"""Semantic provider registry."""

from __future__ import annotations

from ..semantic import SemanticProvider


def build_provider_chain(
    provider_name: str | None,
    api_key: str | None,
    model_name: str | None,
) -> list[SemanticProvider]:
    """Build an ordered list of providers based on configuration."""
    chain: list[SemanticProvider] = []

    if provider_name and api_key:
        if provider_name == "gemini":
            from .gemini import GeminiSemanticProvider
            chain.append(GeminiSemanticProvider(api_key=api_key, model_name=model_name or "gemini-2.0-flash"))
        elif provider_name == "openai":
            from .openai import OpenAISemanticProvider
            chain.append(OpenAISemanticProvider(api_key=api_key, model_name=model_name or "gpt-4o-mini"))
        elif provider_name == "anthropic":
            from .anthropic import AnthropicSemanticProvider
            chain.append(AnthropicSemanticProvider(api_key=api_key, model_name=model_name or "claude-haiku-4-5-20251001"))
        elif provider_name == "ollama":
            from .ollama import OllamaSemanticProvider
            chain.append(OllamaSemanticProvider(model_name=model_name or "llama3"))

    # Embedding fallback is always last (added when prototypes exist)
    # from .embedding import EmbeddingProvider
    # chain.append(EmbeddingProvider())

    return chain
```

```python
# api/providers/base.py
"""Base prompt template shared by all LLM providers."""

SYSTEM_PROMPT = """Du bist ein psycholinguistischer Analyst. Analysiere jeden Textabschnitt und gib ein strukturiertes semantisches Profil zurueck. Antworte ausschliesslich in JSON (Array)."""

def build_user_prompt(units_text: list[tuple[int, str]], language: str) -> str:
    """Build the user prompt with numbered text units."""
    lines = [f"[{idx}] \"{text}\"" for idx, text in units_text]
    texts_block = "\n".join(lines)

    return f"""Analysiere folgende Texteinheiten (Sprache: {language}):

{texts_block}

Gib pro Einheit ein JSON-Objekt zurueck mit genau diesen Feldern:
- index: int (die Nummer der Texteinheit)
- intent: "vorwurf"|"bitte"|"rechtfertigung"|"frage"|"feststellung"|"drohung"|"reparatur"|"smalltalk"|"neutral"
- register: "intim"|"informell"|"formal"|"technisch"|"therapeutisch"
- emotion_primary: "wut"|"trauer"|"angst"|"freude"|"verachtung"|"ueberraschung"|"ekel"|"neutral"
- emotion_secondary: gleiche Liste oder null
- ironie: boolean
- ironie_confidence: 0.0-1.0
- selbst_fremd: "selbst"|"fremd"|"unpersoenlich"
- beziehungsdynamik: "naehe_suche"|"distanzierung"|"kontrolle"|"unterwerfung"|"kooperation"|"neutral"
- pre_context: kurze kausale Hypothese (1 Satz, was vorher passiert sein muss) oder null
- tension: 0.0-1.0 (grundunabhaengige Spannungsintensitaet)

Antworte NUR mit dem JSON-Array, kein Markdown, kein Text drumherum."""
```

```python
# api/providers/gemini.py
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

        # Index lookup for spans
        span_map = {u.index: u.span for u in units}

        profiles = []
        for item in data:
            idx = item.get("index", 0)
            span = span_map.get(idx, (0, 0))
            profiles.append(SemanticProfile(
                intent=item.get("intent", "unknown"),
                intent_confidence=0.9,  # LLM doesn't self-report this reliably
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
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_providers.py -v`
Expected: 4 PASS

**Step 5: Commit**

```bash
git add api/providers/ tests/test_providers.py
git commit -m "feat: add Gemini semantic provider with prompt construction and JSON parsing"
```

---

### Task 3: OpenAI + Anthropic + Ollama Providers

**Files:**
- Create: `api/providers/openai.py`
- Create: `api/providers/anthropic.py`
- Create: `api/providers/ollama.py`
- Test: `tests/test_providers.py` (extend)

**Step 1: Write the failing test**

```python
# Append to tests/test_providers.py

def test_openai_provider_not_available_without_key():
    from api.providers.openai import OpenAISemanticProvider
    provider = OpenAISemanticProvider(api_key=None)
    assert provider.is_available() is False


def test_anthropic_provider_not_available_without_key():
    from api.providers.anthropic import AnthropicSemanticProvider
    provider = AnthropicSemanticProvider(api_key=None)
    assert provider.is_available() is False


def test_ollama_provider_default_unavailable():
    from api.providers.ollama import OllamaSemanticProvider
    provider = OllamaSemanticProvider(model_name="llama3", base_url="http://localhost:99999")
    assert provider.is_available() is False
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementations**

All three follow the same pattern as Gemini: init with key, build prompt via `base.py`, parse JSON response. The key difference is the SDK used for the API call.

```python
# api/providers/openai.py
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
        # OpenAI json_object may wrap in a key
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
```

```python
# api/providers/anthropic.py
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
        # Anthropic may wrap in markdown code block
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
```

```python
# api/providers/ollama.py
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
                    "format": "json",
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]

        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
        span_map = {u.index: u.span for u in units}
        return [
            SemanticProfile(
                intent=d.get("intent", "unknown"),
                intent_confidence=0.8,
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
```

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_providers.py -v`
Expected: 7 PASS

**Step 5: Commit**

```bash
git add api/providers/openai.py api/providers/anthropic.py api/providers/ollama.py tests/test_providers.py
git commit -m "feat: add OpenAI, Anthropic, and Ollama semantic providers"
```

---

### Task 4: Config + Provider Initialization

**Files:**
- Modify: `api/config.py` (add semantic settings)
- Modify: `api/main.py` (initialize profiler at startup)
- Test: `tests/test_semantic.py` (extend)

**Step 1: Write the failing test**

```python
# Append to tests/test_semantic.py

def test_config_has_semantic_settings():
    from api.config import settings
    assert hasattr(settings, "semantic_provider")
    assert hasattr(settings, "semantic_api_key")
    assert hasattr(settings, "semantic_model")
    assert settings.semantic_provider is None  # default: no provider


def test_profiler_from_config_no_key():
    """With no API key configured, profiler should still work (empty profiles)."""
    from api.semantic import SemanticProfiler, TextUnit
    from api.providers import build_provider_chain
    chain = build_provider_chain(provider_name=None, api_key=None, model_name=None)
    profiler = SemanticProfiler(providers=chain)
    import asyncio
    units = [TextUnit(text="Test", index=0, span=(0, 4))]
    profiles = asyncio.run(profiler.profile(units))
    assert len(profiles) == 1
    assert profiles[0].source == "none"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_semantic.py::test_config_has_semantic_settings -v`
Expected: FAIL with `AttributeError`

**Step 3: Update config.py**

Add to `api/config.py` inside the `Settings` class, after the reasoning settings:

```python
    # Semantic Profiling (Layer 0)
    semantic_provider: str | None = None       # gemini|openai|anthropic|ollama
    semantic_api_key: str | None = None        # Provider API key
    semantic_model: str | None = None          # Model name override
```

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_semantic.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add api/config.py tests/test_semantic.py
git commit -m "feat: add semantic provider settings to config"
```

---

### Task 5: semantic_affinity Marker Field

**Files:**
- Modify: `api/engine.py` (`MarkerDef` dataclass)
- Modify: `tools/normalize_schema.py` (pass through field)
- Test: `tests/test_semantic.py` (extend)

**Step 1: Write the failing test**

```python
# Append to tests/test_semantic.py

def test_marker_def_has_semantic_affinity():
    from api.engine import MarkerDef
    m = MarkerDef(
        id="TEST", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={
            "intents": ["vorwurf"],
            "intents_exclude": ["smalltalk"],
            "emotions": ["wut"],
            "register_exclude": ["technisch"],
            "tension_min": 0.3,
            "ironie_suppress": True,
        },
    )
    assert m.semantic_affinity["intents"] == ["vorwurf"]
    assert m.semantic_affinity["ironie_suppress"] is True


def test_marker_def_semantic_affinity_defaults_none():
    from api.engine import MarkerDef
    m = MarkerDef(
        id="TEST", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
    )
    assert m.semantic_affinity is None
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_semantic.py::test_marker_def_has_semantic_affinity -v`
Expected: FAIL with `TypeError: unexpected keyword argument 'semantic_affinity'`

**Step 3: Add field to MarkerDef**

In `api/engine.py`, find the `MarkerDef` dataclass and add:

```python
    semantic_affinity: dict | None = None
```

In `api/engine.py` `_build_marker_def`, add after `gating_conflict`:

```python
            semantic_affinity=data.get("semantic_affinity"),
```

In `tools/normalize_schema.py`, ensure `semantic_affinity` is passed through to the registry (read the file first to find the exact location).

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_semantic.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add api/engine.py tools/normalize_schema.py tests/test_semantic.py
git commit -m "feat: add semantic_affinity field to MarkerDef"
```

---

### Task 6: Semantic Gate in Engine

**Files:**
- Modify: `api/engine.py` (add `_apply_semantic_gate` method)
- Test: `tests/test_semantic_gate.py`

**Step 1: Write the failing test**

```python
# tests/test_semantic_gate.py
"""Tests for the semantic gate in the detection engine."""

def test_semantic_gate_suppresses_wrong_intent():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="smalltalk", intent_confidence=0.9,
        register="informell", emotion_primary="neutral",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="unpersoenlich", beziehungsdynamik="neutral",
        pre_context=None, tension=0.1, source="llm", text_span=(0, 10),
    )

    # Create a fake detection for a marker with intent exclusion
    det = Detection(
        marker_id="TEST_GATE", layer="ATO", confidence=0.8,
        matches=[], message_indices=[0],
    )

    # Temporarily add a marker with semantic_affinity
    eng.markers["TEST_GATE"] = MarkerDef(
        id="TEST_GATE", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={
            "intents": ["vorwurf", "drohung"],
            "intents_exclude": ["smalltalk"],
        },
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 0, "Should suppress marker when intent is excluded"


def test_semantic_gate_passes_matching_intent():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="vorwurf", intent_confidence=0.9,
        register="intim", emotion_primary="wut",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="selbst", beziehungsdynamik="distanzierung",
        pre_context="Wiederholter Konflikt", tension=0.8,
        source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_PASS", layer="ATO", confidence=0.8,
        matches=[], message_indices=[0],
    )

    eng.markers["TEST_PASS"] = MarkerDef(
        id="TEST_PASS", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={
            "intents": ["vorwurf", "drohung"],
            "ironie_suppress": True,
        },
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 1
    assert result[0].confidence == 0.8, "Should pass with full confidence"


def test_semantic_gate_suppresses_ironie():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="feststellung", intent_confidence=0.8,
        register="informell", emotion_primary="verachtung",
        emotion_secondary=None, ironie=True, ironie_confidence=0.9,
        selbst_fremd="fremd", beziehungsdynamik="distanzierung",
        pre_context=None, tension=0.5, source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_IRONY", layer="ATO", confidence=0.9,
        matches=[], message_indices=[0],
    )

    eng.markers["TEST_IRONY"] = MarkerDef(
        id="TEST_IRONY", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={"ironie_suppress": True},
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 0 or result[0].confidence < 0.2, "Should suppress when ironic"


def test_semantic_gate_passes_without_affinity():
    """Markers without semantic_affinity should always pass."""
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="drohung", intent_confidence=0.9,
        register="intim", emotion_primary="wut",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="fremd", beziehungsdynamik="kontrolle",
        pre_context=None, tension=0.9, source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_NO_AFFINITY", layer="ATO", confidence=0.7,
        matches=[], message_indices=[0],
    )

    eng.markers["TEST_NO_AFFINITY"] = MarkerDef(
        id="TEST_NO_AFFINITY", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity=None,
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 1
    assert result[0].confidence == 0.7
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_semantic_gate.py -v`
Expected: FAIL with `AttributeError: '_apply_semantic_gate'`

**Step 3: Implement the gate**

Add to `api/engine.py` in the `MarkerEngine` class, after `_apply_vad_gate`:

```python
    # -----------------------------------------------------------------------
    # Semantic Gate (Layer 0 integration)
    # -----------------------------------------------------------------------

    def _apply_semantic_gate(
        self,
        detections: list[Detection],
        profile: "SemanticProfile | None",
    ) -> list[Detection]:
        """Filter ATO detections against a SemanticProfile.

        Reduces confidence or suppresses markers whose semantic_affinity
        conflicts with the profiled text. Markers without affinity pass through.
        """
        if profile is None or profile.source == "none":
            return detections

        gated: list[Detection] = []

        for det in detections:
            mdef = self.markers.get(det.marker_id)
            affinity = mdef.semantic_affinity if mdef else None

            if not affinity:
                gated.append(det)
                continue

            score = 1.0

            # Intent exclusion
            if profile.intent in (affinity.get("intents_exclude") or []):
                score *= 0.2
            elif affinity.get("intents") and profile.intent not in affinity["intents"]:
                score *= 0.5

            # Ironie suppression
            if affinity.get("ironie_suppress") and profile.ironie and profile.ironie_confidence > 0.7:
                score *= 0.1

            # Tension minimum
            tension_min = affinity.get("tension_min")
            if tension_min and profile.tension < tension_min:
                score *= 0.4

            # Register exclusion
            if profile.register in (affinity.get("register_exclude") or []):
                score *= 0.3

            # Emotion mismatch (soft penalty)
            if affinity.get("emotions") and profile.emotion_primary not in affinity["emotions"]:
                score *= 0.6

            if score >= 0.3:
                det = Detection(
                    marker_id=det.marker_id,
                    layer=det.layer,
                    confidence=round(det.confidence * score, 4),
                    matches=det.matches,
                    message_indices=det.message_indices,
                    vad=det.vad,
                )
                gated.append(det)

        return gated
```

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_semantic_gate.py -v`
Expected: 4 PASS

**Step 5: Commit**

```bash
git add api/engine.py tests/test_semantic_gate.py
git commit -m "feat: add semantic gate to engine for profile-based marker filtering"
```

---

### Task 7: Wire Semantic Layer into analyze endpoints

**Files:**
- Modify: `api/models.py` (add semantic_mode, response fields)
- Modify: `api/main.py` (call profiler, pass profiles to engine)
- Modify: `api/engine.py` (accept profiles in analyze methods)
- Test: `tests/test_api_semantic.py`

**Step 1: Write the failing test**

```python
# tests/test_api_semantic.py
"""E2E tests for semantic layer integration."""
import httpx

BASE = "http://localhost:8420"


def _reachable():
    try:
        return httpx.get(f"{BASE}/v1/health", timeout=3).status_code == 200
    except Exception:
        return False


import pytest
pytestmark = pytest.mark.skipif(not _reachable(), reason="Server not running")


def test_analyze_accepts_semantic_mode():
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Du hoerst mir nie zu!",
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["analysis_mode"] in ("pattern", "semantic")


def test_conversation_accepts_semantic_mode():
    r = httpx.post(f"{BASE}/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Du hoerst mir nie zu!"},
            {"role": "B", "text": "Das stimmt nicht."},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert "analysis_mode" in data.get("meta", {}) or "markers" in data


def test_analyze_semantic_off_matches_baseline():
    """With semantic_mode=off, results should match pre-existing behavior."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ja nee, ich weiss auch nicht.",
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0


def test_analyze_semantic_auto_without_key():
    """With auto mode but no LLM key, should degrade gracefully."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ja nee, ich weiss auch nicht.",
        "semantic_mode": "auto",
    })
    assert r.status_code == 200
```

**Step 2: Run to verify they fail**

Run: `python3 -m pytest tests/test_api_semantic.py -v` (with server running)
Expected: FAIL (422 validation error — `semantic_mode` not accepted yet)

**Step 3: Implement**

In `api/models.py`, add to `AnalyzeRequest`:
```python
    semantic_mode: str = Field(default="auto", description="Semantic profiling: auto|llm|embedding|off")
```

In `api/models.py`, add to `ConversationRequest`:
```python
    semantic_mode: str = Field(default="auto", description="Semantic profiling: auto|llm|embedding|off")
```

In `api/models.py`, add to `AnalyzeMeta`:
```python
    analysis_mode: str = "pattern"  # "semantic" | "pattern"
```

In `api/models.py`, add new response model:
```python
class SemanticProfileResponse(BaseModel):
    message_index: int
    intent: str
    register: str
    emotion_primary: str
    emotion_secondary: str | None = None
    ironie: bool = False
    ironie_confidence: float = 0.0
    selbst_fremd: str = "unpersoenlich"
    beziehungsdynamik: str = "neutral"
    pre_context: str | None = None
    tension: float = 0.0
    source: str = "none"
```

In `api/main.py`, update the analyze endpoint to:
1. Check `semantic_mode`
2. If not "off", create TextUnits and call profiler
3. Pass profiles to engine
4. Set `analysis_mode` in meta

In `api/engine.py`, update `analyze_conversation` signature to accept optional profiles:
```python
    async def analyze_conversation(
        self,
        messages: list[dict],
        ...
        semantic_profiles: list | None = None,  # NEW
    ) -> dict:
```

And insert the semantic gate call at Phase 1.5.

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_api_semantic.py -v` (with server running)
Expected: 4 PASS

**Step 5: Commit**

```bash
git add api/models.py api/main.py api/engine.py tests/test_api_semantic.py
git commit -m "feat: wire semantic layer into analyze endpoints with semantic_mode parameter"
```

---

### Task 8: BYOK Headers

**Files:**
- Modify: `api/main.py` (read headers, override provider)
- Test: `tests/test_api_semantic.py` (extend)

**Step 1: Write the failing test**

```python
# Append to tests/test_api_semantic.py

def test_byok_header_accepted():
    """BYOK headers should be accepted without error (even if key is invalid)."""
    r = httpx.post(
        f"{BASE}/v1/analyze",
        json={"text": "Hallo Welt", "semantic_mode": "llm"},
        headers={
            "X-LeanDeep-Provider": "openai",
            "X-LeanDeep-Provider-Key": "sk-fake-key-for-testing",
            "X-LeanDeep-Provider-Model": "gpt-4o-mini",
        },
    )
    # Should not crash — either 200 (with fallback) or 503 (provider unavailable)
    assert r.status_code in (200, 503)
```

**Step 2: Run to verify it fails**

Run: `python3 -m pytest tests/test_api_semantic.py::test_byok_header_accepted -v`

**Step 3: Implement in api/main.py**

Read `X-LeanDeep-Provider`, `X-LeanDeep-Provider-Key`, `X-LeanDeep-Provider-Model` from request headers. If present, build a one-off provider chain for this request. If the provider fails and `semantic_mode="llm"`, return 503. Otherwise fall back.

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_api_semantic.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add api/main.py tests/test_api_semantic.py
git commit -m "feat: add BYOK header support for custom LLM providers per request"
```

---

### Task 9: Embedding Provider + Prototype Builder

**Files:**
- Create: `api/providers/embedding.py`
- Create: `tools/build_prototypes.py`
- Test: `tests/test_embedding_provider.py`

**Step 1: Write the failing test**

```python
# tests/test_embedding_provider.py
"""Tests for the embedding fallback provider."""
import numpy as np
import pytest

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False


@pytest.mark.skipif(not HAS_ST, reason="sentence-transformers not installed")
def test_embedding_provider_with_mock_prototypes(tmp_path):
    from api.providers.embedding import EmbeddingProvider
    from api.semantic import TextUnit

    # Create mock prototypes
    proto_path = tmp_path / "marker_prototypes.npz"
    ids = ["ATO_TEST_A", "ATO_TEST_B"]
    # 384-dim for MiniLM
    vecs = np.random.randn(2, 384).astype(np.float32)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    np.savez(proto_path, ids=np.array(ids), vectors=vecs)

    provider = EmbeddingProvider(prototypes_path=str(proto_path))
    assert provider.is_available() is True

    units = [TextUnit(text="Das ist ein Test", index=0, span=(0, 16))]
    import asyncio
    profiles = asyncio.run(provider.profile(units, "de"))
    assert len(profiles) == 1
    assert profiles[0].source == "embedding"
    assert hasattr(profiles[0], "_marker_whitelist")  # internal attribute for gate


def test_embedding_provider_unavailable_without_prototypes():
    from api.providers.embedding import EmbeddingProvider
    provider = EmbeddingProvider(prototypes_path="/nonexistent/path.npz")
    assert provider.is_available() is False
```

**Step 2: Run to verify they fail**

Run: `python3 -m pytest tests/test_embedding_provider.py -v`

**Step 3: Implement**

```python
# api/providers/embedding.py
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
```

```python
# tools/build_prototypes.py
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
```

**Step 4: Run tests**

Run: `python3 -m pytest tests/test_embedding_provider.py -v`
Expected: PASS (or skip if sentence-transformers not installed)

**Step 5: Commit**

```bash
git add api/providers/embedding.py tools/build_prototypes.py tests/test_embedding_provider.py
git commit -m "feat: add embedding fallback provider and prototype builder tool"
```

---

### Task 10: Semantic Affinity Enrichment Tool

**Files:**
- Create: `tools/enrich_semantic_affinity.py`
- Test: Manual run + spot check

**Step 1: Write the tool**

```python
# tools/enrich_semantic_affinity.py
"""Enrich markers with semantic_affinity fields based on ID patterns and metadata.

Usage:
    python3 tools/enrich_semantic_affinity.py              # Rule-based enrichment
    python3 tools/enrich_semantic_affinity.py --dry-run     # Preview changes
    python3 tools/enrich_semantic_affinity.py --stats       # Show coverage stats

Reads/writes: build/markers_rated/**/*.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True

# --- Rule-based affinity mapping ---

INTENT_RULES = [
    # (ID patterns, intents, intents_exclude)
    (["ACCUSATION", "BLAME", "CRITICISM", "VORWURF", "CONTEMPT"],
     ["vorwurf"], ["smalltalk", "reparatur"]),
    (["REPAIR", "APOLOGY", "RECONCIL", "FORGIV", "DEESKALAT"],
     ["reparatur", "bitte"], ["drohung"]),
    (["THREAT", "DEMAND", "COERCI", "ULTIMAT"],
     ["drohung", "vorwurf"], ["smalltalk", "reparatur"]),
    (["QUESTION", "DOUBT", "UNCERTAINTY", "HESITAT"],
     ["frage", "rechtfertigung"], ["drohung", "feststellung"]),
    (["SARCASM", "IRONY"],
     ["vorwurf", "feststellung"], []),
    (["SMALLTALK", "GREETING", "FAREWELL", "ACK_MICRO"],
     ["smalltalk"], ["vorwurf", "drohung"]),
    (["GASLIGHT", "MANIPULAT", "DOUBLE_BIND", "PASSIVE_AGGRESS"],
     ["feststellung", "vorwurf"], ["smalltalk"]),
]

IRONIE_SUPPRESS_IDS = {
    "UNCERTAINTY", "HESITAT", "DOUBT", "FEAR", "ANGST", "ANXIETY",
    "SADNESS", "TRAUER", "GRIEF", "DEPRESSION", "LONELINESS",
    "ATTACHMENT", "LOVE", "TRUST", "BONDING",
}

TENSION_MIN_LAYERS = {"CLU": 0.2, "MEMA": 0.3}


def infer_affinity(marker_id: str, layer: str, tags: list, family: str | None) -> dict | None:
    """Infer semantic_affinity from marker metadata."""
    affinity = {}
    mid_upper = marker_id.upper()

    # Intent rules
    for patterns, intents, excludes in INTENT_RULES:
        if any(p in mid_upper for p in patterns):
            affinity["intents"] = intents
            if excludes:
                affinity["intents_exclude"] = excludes
            break

    # Ironie suppress
    if any(p in mid_upper for p in IRONIE_SUPPRESS_IDS):
        affinity["ironie_suppress"] = True

    # Tension minimum by layer
    if layer in TENSION_MIN_LAYERS:
        affinity["tension_min"] = TENSION_MIN_LAYERS[layer]

    # Register exclude for technical markers
    if "formal" in tags or "technical" in tags:
        affinity["register_exclude"] = ["intim"]

    return affinity if affinity else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    rated_dir = Path("build/markers_rated")
    total = 0
    enriched = 0
    already = 0

    for yaml_file in sorted(rated_dir.rglob("*.yaml")):
        data = yaml.load(yaml_file)
        if not data:
            continue

        total += 1

        if data.get("semantic_affinity"):
            already += 1
            continue

        mid = data.get("id", yaml_file.stem)
        layer = data.get("layer", "ATO")
        tags = data.get("tags", [])
        family = data.get("ld5_family")

        affinity = infer_affinity(mid, layer, tags, family)

        if affinity:
            if args.dry_run or args.stats:
                print(f"  {mid}: {affinity}")
            else:
                data["semantic_affinity"] = affinity
                yaml.dump(data, yaml_file)
            enriched += 1

    print(f"\nTotal: {total}, Already: {already}, Enriched: {enriched}, "
          f"Remaining: {total - already - enriched}")


if __name__ == "__main__":
    main()
```

**Step 2: Run with --dry-run**

Run: `python3 tools/enrich_semantic_affinity.py --dry-run | head -30`
Expected: List of markers with inferred affinities

**Step 3: Run for real**

Run: `python3 tools/enrich_semantic_affinity.py`

**Step 4: Verify via normalize**

Run: `python3 tools/normalize_schema.py && python3 -m pytest tests/ -x -q --ignore=tests/test_webapp.py`

**Step 5: Commit**

```bash
git add tools/enrich_semantic_affinity.py build/markers_rated/
git commit -m "feat: add semantic_affinity enrichment tool with rule-based inference"
```

---

### Task 11: Update requirements.txt + Dockerfile

**Files:**
- Modify: `requirements.txt`
- Modify: `Dockerfile`

**Step 1: Update requirements.txt**

Add optional dependencies section:

```
# Semantic Providers (optional — install what you need)
openai>=1.0
anthropic>=0.40
httpx>=0.27.0

# Embedding Fallback (optional — ~400MB with model)
sentence-transformers>=3.0
numpy>=1.26
```

Note: `google-generativeai` is already listed. `httpx` is already listed under Dev/Test.

**Step 2: Update Dockerfile**

No change needed — the Dockerfile installs from requirements.txt. The optional packages will only be needed if the corresponding provider is configured.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add semantic provider dependencies to requirements.txt"
```

---

### Task 12: Update CLAUDE.md + Frontend

**Files:**
- Modify: `CLAUDE.md`
- Modify: `api/static/app.html` (display semantic profiles in output)

**Step 1: Update CLAUDE.md**

Add Semantic Layer documentation to the Architecture section:
- New Layer 0 (Semantic Profiling) in the pipeline diagram
- New env variables (LEANDEEP_SEMANTIC_PROVIDER, LEANDEEP_SEMANTIC_API_KEY, LEANDEEP_SEMANTIC_MODEL)
- New tools (build_prototypes.py, enrich_semantic_affinity.py)

**Step 2: Update frontend**

In `api/static/app.html`, when `semantic_profiles` is present in the response:
- Show a "Semantic Profile" section per message/sentence
- Display intent, emotion, tension as colored pills
- Show pre_context as italic annotation
- Indicate source (llm/embedding/none) with a badge

**Step 3: Commit**

```bash
git add CLAUDE.md api/static/app.html
git commit -m "docs: update CLAUDE.md and frontend for semantic layer"
```

---

### Task 13: Integration Test (full flow)

**Files:**
- Create: `tests/test_semantic_e2e.py`

**Step 1: Write the test**

```python
# tests/test_semantic_e2e.py
"""Full integration test: text -> semantic profiling -> engine -> response."""
import httpx
import pytest

BASE = "http://localhost:8420"


def _reachable():
    try:
        return httpx.get(f"{BASE}/v1/health", timeout=3).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="Server not running")


def test_full_flow_semantic_off():
    """Baseline: semantic_mode=off should work identically to pre-existing behavior."""
    r = httpx.post(f"{BASE}/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Du hoerst mir ja eh nie zu."},
            {"role": "B", "text": "Doch, ich hoere dir zu!"},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0
    assert data["meta"]["analysis_mode"] == "pattern"
    assert "semantic_profiles" not in data or data["semantic_profiles"] is None


def test_full_flow_semantic_auto_graceful():
    """Auto mode should not crash even without LLM key."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ich bin so wuetend auf dich!",
        "semantic_mode": "auto",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0
```

**Step 2: Run with server**

Run: Start server, then `python3 -m pytest tests/test_semantic_e2e.py -v`

**Step 3: Commit**

```bash
git add tests/test_semantic_e2e.py
git commit -m "test: add semantic layer E2E integration tests"
```

---

Plan complete and saved to `docs/plans/2026-03-08-semantic-prefilter.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?