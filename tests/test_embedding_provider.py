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
    assert hasattr(profiles[0], "_marker_whitelist")


def test_embedding_provider_unavailable_without_prototypes():
    from api.providers.embedding import EmbeddingProvider
    provider = EmbeddingProvider(prototypes_path="/nonexistent/path.npz")
    assert provider.is_available() is False
