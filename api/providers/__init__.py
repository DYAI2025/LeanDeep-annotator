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

    return chain
