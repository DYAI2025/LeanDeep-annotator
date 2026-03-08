"""Tests for SemanticProfile and provider protocol."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_api_reachable():
    """Override: semantic tests are pure unit tests, no API needed."""
    return


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
