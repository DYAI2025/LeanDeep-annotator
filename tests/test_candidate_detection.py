"""Unit tests for the candidate detection pipeline (api/candidates.py).

Covers REQ-F-candidate-detection acceptance criteria:
- Clusters have >= 3 coherent example passages
- Candidates are ranked (best first)
- LLM path + heuristic fallback path
- Novelty scoring rejects known-marker duplicates
- Cross-marker family diversity raises novelty
"""

from __future__ import annotations

import pytest

from api.candidates import (
    COHERENCE_THRESHOLD,
    MIN_EXAMPLES_PER_CANDIDATE,
    PassageCluster,
    PassageHit,
    build_candidates_from_clusters,
    cluster_passages_heuristic,
    cluster_passages_llm,
    detect_candidates,
    extract_passage_hits,
    hash_dialogue,
    rank_candidates,
    _compute_novelty,
)
from api.engine import Match
from api.resonance import WeightedMarker


# ---- Fixtures ------------------------------------------------------------

def make_match(text: str, start: int = 0, end: int | None = None) -> Match:
    return Match(
        marker_id="x",
        pattern="p",
        start=start,
        end=end if end is not None else len(text),
        matched_text=text,
    )


def make_weighted(
    marker_id: str,
    tier: str = "WEAK",
    matches: list[Match] | None = None,
    family: str = "MODAL_DOUBT",
    description: str = "test marker",
    adjusted: float = 0.35,
    message_indices: list[int] | None = None,
) -> WeightedMarker:
    return WeightedMarker(
        marker_id=marker_id,
        layer="ATO",
        confidence=0.8,
        resonance_score=0.5,
        adjusted_confidence=adjusted,
        tier=tier,
        description=description,
        family=family,
        matches=matches or [make_match("test")],
        message_indices=message_indices or [0],
    )


# ---- hash_dialogue -------------------------------------------------------

def test_hash_dialogue_is_stable():
    assert hash_dialogue("hello") == hash_dialogue("hello")
    assert hash_dialogue("hello") != hash_dialogue("world")
    assert len(hash_dialogue("anything")) == 16


# ---- extract_passage_hits ------------------------------------------------

def test_extract_ignores_strong_markers():
    dialogue = "I am really really unsure about this today."
    strong = make_weighted(
        "ATO_STRONG",
        tier="STRONG",
        matches=[make_match("unsure", start=19, end=25)],
    )
    weak = make_weighted(
        "ATO_WEAK",
        tier="WEAK",
        matches=[make_match("really", start=5, end=11)],
    )
    hits = extract_passage_hits([strong, weak], dialogue)
    assert len(hits) == 1
    assert hits[0].marker_id == "ATO_WEAK"


def test_extract_includes_weak_and_discarded():
    dialogue = "I am not sure. Maybe tomorrow. Or never."
    weak = make_weighted("ATO_W", tier="WEAK", matches=[make_match("not sure", 5, 13)])
    discarded = make_weighted("ATO_D", tier="DISCARDED", matches=[make_match("Maybe", 15, 20)])
    hits = extract_passage_hits([weak, discarded], dialogue)
    assert len(hits) == 2
    assert {h.marker_id for h in hits} == {"ATO_W", "ATO_D"}


def test_extract_captures_context():
    dialogue = "The weather is cold today and I feel so tired already."
    weak = make_weighted("ATO_W", tier="WEAK", matches=[make_match("tired", 39, 44)])
    hits = extract_passage_hits([weak], dialogue)
    assert "tired" in hits[0].context
    # context should include surrounding text
    assert len(hits[0].context) > len("tired")


def test_extract_resolves_context_via_per_message_coordinates():
    """Match.start/end are per-message offsets, not dialogue-level.
    Without passing messages, we'd slice the wrong region.
    """
    messages = [
        {"role": "A", "text": "This first message is totally unrelated content."},
        {"role": "B", "text": "I don't really know what I want from this."},
    ]
    full = "\n".join(m["text"] for m in messages)

    # marker hit in message 1 at position 2-20 ("don't really know")
    weak = make_weighted(
        "ATO_DOUBT",
        tier="WEAK",
        matches=[make_match("don't really know", start=2, end=19)],
        message_indices=[1],
    )

    # With messages passed: context should come from message 1
    hits_with_messages = extract_passage_hits([weak], full, messages=messages)
    assert len(hits_with_messages) == 1
    assert "don't really know" in hits_with_messages[0].context
    assert "first message" not in hits_with_messages[0].context  # not from msg 0

    # Without messages: fallback slices dialogue_text with per-message coords,
    # which would produce wrong context — verify the bug path differs
    hits_without = extract_passage_hits([weak], full)
    assert len(hits_without) == 1
    # The fallback slices `full` at offset 2-19 — which is inside msg 0
    assert "first message" in hits_without[0].context.lower() or \
           "don't really know" not in hits_without[0].context



def test_extract_resolves_context_per_match_when_marker_spans_messages():
    """A merged marker can carry matches from different messages."""
    messages = [
        {"role": "A", "text": "I cannot keep doing this anymore."},
        {"role": "B", "text": "Maybe we should pause and think."},
    ]
    full = "\n".join(m["text"] for m in messages)

    weak = make_weighted(
        "ATO_MERGED",
        tier="WEAK",
        matches=[
            make_match("cannot", start=2, end=8),
            make_match("Maybe", start=0, end=5),
        ],
        message_indices=[0, 1],
    )

    hits = extract_passage_hits([weak], full, messages=messages)
    assert len(hits) == 2

    assert "cannot keep" in hits[0].context
    assert hits[0].message_index == 0

    assert "Maybe we should" in hits[1].context
    assert hits[1].message_index == 1


def test_extract_handles_invalid_message_index_gracefully():
    """If message_indices points beyond the messages list, fall back safely."""
    messages = [{"role": "A", "text": "only one message"}]
    weak = make_weighted(
        "ATO_X",
        tier="WEAK",
        matches=[make_match("one", start=5, end=8)],
        message_indices=[5],  # out of range
    )
    hits = extract_passage_hits([weak], "only one message", messages=messages)
    assert len(hits) == 1
    # Falls back to dialogue_text, which happens to equal messages[0].text here
    assert "one" in hits[0].text


def test_extract_skips_empty_matches():
    weak = make_weighted("ATO_W", matches=[Match(marker_id="x", pattern="p", start=0, end=0, matched_text="")])
    hits = extract_passage_hits([weak], "hello")
    assert hits == []


# ---- cluster_passages_heuristic ------------------------------------------

def test_heuristic_groups_by_family_with_minimum():
    hits = [
        PassageHit("M1", "DOUBT", "", "not sure", "ctx", 0.4, "h1"),
        PassageHit("M2", "DOUBT", "", "maybe", "ctx", 0.35, "h2"),
        PassageHit("M3", "DOUBT", "", "I think", "ctx", 0.3, "h3"),
        PassageHit("M4", "AVOID", "", "can't say", "ctx", 0.4, "h4"),  # only 1 in family — skipped
    ]
    clusters = cluster_passages_heuristic(hits)
    assert len(clusters) == 1
    assert clusters[0].label.startswith("Recurring")
    assert len(clusters[0].passages) == 3
    assert clusters[0].coherence <= 0.75
    assert set(clusters[0].related_markers) == {"M1", "M2", "M3"}


def test_heuristic_returns_empty_when_no_family_has_minimum():
    hits = [
        PassageHit("M1", "A", "", "x", "ctx", 0.4, "h"),
        PassageHit("M2", "B", "", "y", "ctx", 0.4, "h"),
    ]
    assert cluster_passages_heuristic(hits) == []


# ---- cluster_passages_llm (with injected caller) -------------------------

@pytest.mark.asyncio
async def test_llm_cluster_returns_parsed_clusters():
    hits = [
        PassageHit(f"M{i}", "FAM", "", f"text{i}", f"ctx{i}", 0.4, "h")
        for i in range(4)
    ]

    async def fake_llm(_prompt: str) -> str:
        return (
            '{"clusters": [{"label": "recurring hedging",'
            ' "passage_indices": [0, 1, 2, 3],'
            ' "coherence": 0.85,'
            ' "related_existing_markers": ["ATO_HEDGE"]}]}'
        )

    clusters = await cluster_passages_llm(hits, llm_call=fake_llm)
    assert len(clusters) == 1
    assert clusters[0].label == "recurring hedging"
    assert clusters[0].coherence == 0.85
    assert clusters[0].related_markers == ["ATO_HEDGE"]


@pytest.mark.asyncio
async def test_llm_cluster_filters_low_coherence():
    hits = [PassageHit(f"M{i}", "F", "", "x", "c", 0.4, "h") for i in range(3)]

    async def fake_llm(_prompt: str) -> str:
        return '{"clusters": [{"label": "noise", "passage_indices": [0,1,2], "coherence": 0.4}]}'

    clusters = await cluster_passages_llm(hits, llm_call=fake_llm)
    assert clusters == []  # below COHERENCE_THRESHOLD


@pytest.mark.asyncio
async def test_llm_cluster_skips_tiny_clusters():
    hits = [PassageHit(f"M{i}", "F", "", "x", "c", 0.4, "h") for i in range(5)]

    async def fake_llm(_prompt: str) -> str:
        # LLM returns a 1-passage "cluster" — should be filtered
        return '{"clusters": [{"label": "solo", "passage_indices": [0], "coherence": 0.9}]}'

    clusters = await cluster_passages_llm(hits, llm_call=fake_llm)
    assert clusters == []


@pytest.mark.asyncio
async def test_llm_cluster_handles_llm_failure_gracefully():
    hits = [PassageHit(f"M{i}", "F", "", "x", "c", 0.4, "h") for i in range(3)]

    async def failing_llm(_prompt: str) -> str:
        raise RuntimeError("LLM down")

    clusters = await cluster_passages_llm(hits, llm_call=failing_llm)
    assert clusters == []


@pytest.mark.asyncio
async def test_llm_cluster_returns_empty_below_minimum_hits():
    hits = [PassageHit("M1", "F", "", "x", "c", 0.4, "h")]  # only 1 hit

    async def fake_llm(_prompt: str) -> str:
        pytest.fail("LLM should not be called when below minimum")
        return ""

    clusters = await cluster_passages_llm(hits, llm_call=fake_llm)
    assert clusters == []


# ---- build_candidates_from_clusters --------------------------------------

def test_build_candidates_assembles_example_passages():
    hits = [PassageHit(f"M{i}", "F", "desc", f"text{i}", f"ctx{i}", 0.5, "h") for i in range(4)]
    cluster = PassageCluster(label="pattern", passages=hits, coherence=0.8, related_markers=["OTHER"])
    candidates = build_candidates_from_clusters([cluster], existing_marker_ids=set())
    assert len(candidates) == 1
    c = candidates[0]
    assert c.cluster_meaning == "pattern"
    assert c.coherence == 0.8
    assert 0 <= c.novelty <= 1
    assert c.frequency == 4
    assert c.status == "proposed"
    assert len(c.example_passages) == 4
    assert all(p.source_dialogue_hash == "h" for p in c.example_passages)


def test_build_candidates_dedupes_passages_by_text():
    hits = [
        PassageHit("M1", "F", "", "duplicate", "c", 0.5, "h"),
        PassageHit("M2", "F", "", "duplicate", "c", 0.5, "h"),
        PassageHit("M3", "F", "", "unique1", "c", 0.5, "h"),
        PassageHit("M4", "F", "", "unique2", "c", 0.5, "h"),
    ]
    cluster = PassageCluster(label="p", passages=hits, coherence=0.8)
    candidates = build_candidates_from_clusters([cluster], existing_marker_ids=set())
    assert len(candidates) == 1
    # 3 unique texts: duplicate, unique1, unique2
    assert len(candidates[0].example_passages) == 3
    assert candidates[0].frequency == 4  # frequency is raw count, not deduped


def test_build_candidates_filters_below_minimum_unique_passages():
    hits = [
        PassageHit("M1", "F", "", "same", "c", 0.5, "h"),
        PassageHit("M2", "F", "", "same", "c", 0.5, "h"),
    ]  # only 1 unique text after dedup → below MIN
    cluster = PassageCluster(label="p", passages=hits, coherence=0.9)
    candidates = build_candidates_from_clusters([cluster], existing_marker_ids=set())
    assert candidates == []


def test_build_candidates_filters_low_novelty():
    # Single-family, all markers known → low novelty
    hits = [PassageHit(f"M{i}", "F", "", f"text{i}", "c", 0.5, "h") for i in range(3)]
    cluster = PassageCluster(
        label="known pattern",
        passages=hits,
        coherence=0.9,
        related_markers=["KNOWN1", "KNOWN2"],
    )
    existing = {"KNOWN1", "KNOWN2"}
    candidates = build_candidates_from_clusters([cluster], existing_marker_ids=existing)
    # novelty = (1/3 * 0.5) + (0 * 0.5) = 0.166 < 0.2 → rejected
    assert candidates == []


def test_build_candidates_caps_examples_at_max():
    hits = [PassageHit(f"M{i}", "F", "", f"text{i}", "c", 0.5, "h") for i in range(20)]
    cluster = PassageCluster(label="p", passages=hits, coherence=0.9)
    candidates = build_candidates_from_clusters([cluster], existing_marker_ids=set())
    assert len(candidates) == 1
    assert len(candidates[0].example_passages) == 5  # MAX_EXAMPLES_IN_CANDIDATE


# ---- _compute_novelty ----------------------------------------------------

def test_novelty_high_for_diverse_unknown_families():
    hits = [
        PassageHit("M1", "FAM_A", "", "a", "c", 0.5, "h"),
        PassageHit("M2", "FAM_B", "", "b", "c", 0.5, "h"),
        PassageHit("M3", "FAM_C", "", "c", "c", 0.5, "h"),
    ]
    cluster = PassageCluster(label="p", passages=hits, coherence=0.9, related_markers=[])
    novelty = _compute_novelty(cluster, existing=set())
    assert novelty >= 0.7


def test_novelty_low_for_known_single_family():
    hits = [
        PassageHit("M1", "FAM", "", "a", "c", 0.5, "h"),
        PassageHit("M2", "FAM", "", "b", "c", 0.5, "h"),
    ]
    cluster = PassageCluster(
        label="p",
        passages=hits,
        coherence=0.9,
        related_markers=["ATO_EXISTING"],
    )
    novelty = _compute_novelty(cluster, existing={"ATO_EXISTING"})
    # family_diversity = 1/3 ≈ 0.33, overlap = 1/1 = 1 → 0.33*0.5 + 0*0.5 = 0.165
    assert novelty < 0.2


def test_novelty_zero_for_empty_cluster():
    cluster = PassageCluster(label="p", passages=[], coherence=0.5)
    assert _compute_novelty(cluster, existing=set()) == 0.0


# ---- rank_candidates -----------------------------------------------------

def test_rank_candidates_orders_by_rank_score_descending():
    from api.models import ExamplePassage, MarkerCandidate

    def make_candidate(cid: str, score: float) -> MarkerCandidate:
        return MarkerCandidate(
            candidate_id=cid,
            example_passages=[ExamplePassage(text="x")],
            cluster_meaning="c",
            coherence=0.8,
            novelty=0.5,
            rank_score=score,
        )

    candidates = [
        make_candidate("low", 1.0),
        make_candidate("high", 10.0),
        make_candidate("mid", 5.0),
    ]
    ranked = rank_candidates(candidates)
    assert [c.candidate_id for c in ranked] == ["high", "mid", "low"]


# ---- detect_candidates (end-to-end) --------------------------------------

@pytest.mark.asyncio
async def test_detect_candidates_end_to_end_heuristic():
    dialogue = (
        "I don't really know what I want. "
        "Maybe it's fine but I'm not sure. "
        "It's complicated, I guess."
    )
    markers = [
        make_weighted("ATO_1", tier="WEAK", family="DOUBT",
                      matches=[make_match("don't really know", 2, 19)]),
        make_weighted("ATO_2", tier="WEAK", family="DOUBT",
                      matches=[make_match("not sure", 59, 67)]),
        make_weighted("ATO_3", tier="DISCARDED", family="DOUBT",
                      matches=[make_match("I guess", 89, 96)]),
    ]
    candidates = await detect_candidates(
        markers, dialogue, existing_marker_ids=set(), use_llm=False,
    )
    assert len(candidates) >= 1
    c = candidates[0]
    assert c.frequency == 3
    assert c.coherence > 0
    assert c.status == "proposed"
    assert len(c.example_passages) >= MIN_EXAMPLES_PER_CANDIDATE


@pytest.mark.asyncio
async def test_detect_candidates_returns_empty_when_too_few_hits():
    markers = [make_weighted("ATO_1", tier="WEAK", matches=[make_match("hmm", 0, 3)])]
    candidates = await detect_candidates(markers, "hmm", use_llm=False)
    assert candidates == []


@pytest.mark.asyncio
async def test_detect_candidates_uses_llm_when_provided():
    dialogue = "I am unsure. I don't know. I doubt this."
    markers = [
        make_weighted("M1", tier="WEAK", family="F",
                      matches=[make_match("unsure", 5, 11)]),
        make_weighted("M2", tier="WEAK", family="F",
                      matches=[make_match("don't know", 15, 25)]),
        make_weighted("M3", tier="WEAK", family="F",
                      matches=[make_match("doubt", 29, 34)]),
    ]

    async def fake_llm(_prompt: str) -> str:
        return (
            '{"clusters": [{"label": "hedging pattern",'
            ' "passage_indices": [0, 1, 2],'
            ' "coherence": 0.88,'
            ' "related_existing_markers": []}]}'
        )

    candidates = await detect_candidates(
        markers, dialogue,
        existing_marker_ids=set(),
        use_llm=True,
        llm_call=fake_llm,
    )
    assert len(candidates) == 1
    assert candidates[0].cluster_meaning == "hedging pattern"
    assert candidates[0].coherence == 0.88
