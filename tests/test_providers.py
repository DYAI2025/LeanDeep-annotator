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
    assert isinstance(chain, list)


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
