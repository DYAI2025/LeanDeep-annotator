"""Pydantic models for the LeanDeep Marker API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .semantic_frame import SemanticFrame

UTC = timezone.utc

# --- Enums ---

class Layer(str, Enum):
    ATO = "ATO"
    SEM = "SEM"
    CLU = "CLU"
    MEMA = "MEMA"


class InterpretationMode(str, Enum):
    CLINICAL = "Clinical"
    NARRATIVE = "Narrative"
    EXPLORATIVE = "Explorative"


class Language(str, Enum):
    DE = "de"
    EN = "en"
    BILINGUAL = "bilingual"


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100_000, description="Text to analyze")
    language: Language = Language.DE
    layers: list[Layer] = Field(default_factory=lambda: [Layer.ATO, Layer.SEM], description="Layers to detect")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")
    semantic_mode: str = Field(default="auto", description="Semantic profiling: auto|llm|embedding|off")


class Message(BaseModel):
    role: str = Field(..., description="Speaker role (A/B, therapist/client, etc.)")
    text: str = Field(..., min_length=1, max_length=100_000)


class ConversationRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1, max_length=2000)
    language: Language = Language.DE
    layers: list[Layer] = Field(
        default_factory=lambda: [Layer.ATO, Layer.SEM, Layer.CLU, Layer.MEMA],
        description="Layers to detect",
    )
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    persona_token: str | None = Field(None, description="Persona token for persistent profiling (Pro tier)")
    semantic_mode: str = Field(default="auto", description="Semantic profiling: auto|llm|embedding|off")


class NarrativeRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1, max_length=2000)
    language: Language = Language.DE
    layers: list[Layer] = Field(default_factory=lambda: [Layer.ATO, Layer.SEM, Layer.CLU, Layer.MEMA])
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    semantic_mode: str = Field(default="auto")
    interpretation_mode: InterpretationMode = Field(
        default=InterpretationMode.NARRATIVE,
        description="Interpretation framing: Clinical | Narrative | Explorative"
    )
    include_initial_semantics: bool = Field(
        default=True,
        description="Run pre-analysis semantic space definition"
    )


class MarkerQuery(BaseModel):
    layer: Layer | None = None
    family: str | None = None
    tag: str | None = None
    search: str | None = Field(None, description="Full-text search in ID/description")
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# --- Response Models ---

class PatternMatch(BaseModel):
    pattern: str
    span: tuple[int, int]
    matched_text: str


class DetectedMarker(BaseModel):
    id: str
    layer: Layer
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""
    matches: list[PatternMatch] = Field(default_factory=list)
    family: str | None = None
    multiplier: float | None = None


class AnalyzeMeta(BaseModel):
    processing_ms: float
    version: str = "6.0"
    text_length: int
    markers_detected: int
    layers_scanned: list[str]
    shadow_mode: bool = False
    analysis_mode: str = "pattern"


class AnalyzeResponse(BaseModel):
    markers: list[DetectedMarker]
    meta: AnalyzeMeta


class SemanticProfileResponse(BaseModel):
    message_index: int
    intent: str
    register: str  # noqa: register shadows BaseModel attr (harmless)
    emotion_primary: str
    emotion_secondary: str | None = None
    ironie: bool = False
    ironie_confidence: float = 0.0
    selbst_fremd: str = "unpersoenlich"
    beziehungsdynamik: str = "neutral"
    pre_context: str | None = None
    tension: float = 0.0
    source: str = "none"


class ConversationMarker(BaseModel):
    id: str
    layer: Layer
    confidence: float
    description: str = ""
    message_indices: list[int] = Field(default_factory=list)
    family: str | None = None
    multiplier: float | None = None
    matches: list[PatternMatch] = Field(default_factory=list)
    frame: dict[str, Any] | None = None
    # v6.0 resonance weighting fields (additive, per DEC-v1-backward-compatibility)
    resonance_score: float | None = None
    adjusted_confidence: float | None = None
    tier: str | None = None  # "STRONG" | "WEAK" | "DISCARDED"
    meaning_in_context: str | None = None


class TemporalPattern(BaseModel):
    pattern_type: str
    marker_id: str
    first_seen: int
    last_seen: int
    frequency: int
    trend: str = "stable"


class TopologyHealth(BaseModel):
    score: float
    grade: str

class TopologyConstraint(BaseModel):
    id: str
    severity: str
    status: str
    score: float
    message_indices: list[int] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""

class TopologyReport(BaseModel):
    version: str
    mode: str = "shadow"
    health: TopologyHealth
    constraints: list[TopologyConstraint] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    gates: dict[str, Any] = Field(default_factory=dict)


class ReasoningReport(BaseModel):
    relational_pattern: str
    narrative: str
    is_formal_technical: bool
    confidence_score: float
    evidence_marker_ids: list[str] = Field(default_factory=list)


class WeakCluster(BaseModel):
    """A cluster of weak markers suggesting an alternative interpretation."""
    marker_ids: list[str]
    cluster_label: str
    coherence: float = Field(ge=0.0, le=1.0)
    avg_confidence: float = Field(ge=0.0, le=1.0)
    marker_count: int


class SupportingMarkerRef(BaseModel):
    """Reference to a marker supporting a narrative interpretation."""
    id: str
    adjusted_confidence: float | None = None
    span: tuple[int, int] | None = None
    meaning_in_context: str = ""


class MultiNarrative(BaseModel):
    """A single narrative interpretation (one of 3-4 perspectives)."""
    narrative_id: int
    type: str  # "Primary" | "Contrarian" | "Novel" | "High-Uncertainty" | "Weak Cluster"
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_markers: list[SupportingMarkerRef] = Field(default_factory=list)
    uncertainty_warning: str | None = None
    score: float = 0.0


class VADPoint(BaseModel):
    valence: float
    arousal: float
    dominance: float


# Note: SemanticFrame is defined in api/semantic_frame.py and imported at top of this file.
# Do NOT redefine it here — the import from semantic_frame is the canonical definition.


class VADPoint(BaseModel):
    valence: float
    arousal: float
    dominance: float


class ConversationResponse(BaseModel):
    frame: SemanticFrame | None = None
    markers: list[ConversationMarker]
    narratives: list[MultiNarrative] = Field(default_factory=list)
    weak_clusters: list[WeakCluster] = Field(default_factory=list)
    semantic_profile: list[SemanticProfileResponse] = Field(default_factory=list)
    vad_trajectory: list[VADPoint] = Field(default_factory=list)
    temporal_patterns: list[TemporalPattern] = Field(default_factory=list)
    topology: TopologyReport | None = None
    reasoning: ReasoningReport | None = None
    degraded: bool = False
    provider_used: str | None = None
    fallback_reason: str | None = None
    duration_ms: float | None = None
    meta: AnalyzeMeta


class UEDVariability(BaseModel):
    valence: float
    arousal: float


class UEDMetrics(BaseModel):
    home_base: VADPoint
    variability: UEDVariability
    instability: UEDVariability
    rise_rate: float
    recovery_rate: float
    density: float


class StateIndices(BaseModel):
    trust: float
    conflict: float
    deesc: float
    contributing_markers: int


class EmotionScore(BaseModel):
    scores: dict[str, float]   # {ANGER: 0.12, JOY: 0.45, ...}
    dominant: str              # "JOY"
    dominant_score: float      # 0.45
    prosody: dict[str, float] | None = None  # 17 structural features


class SpeakerDelta(BaseModel):
    speaker: str
    delta_v: float
    delta_a: float
    baseline_v: float
    baseline_a: float
    shift: str | None = None  # "repair" | "escalation" | "volatility"


class SpeakerSummary(BaseModel):
    message_count: int
    baseline_final: VADPoint
    valence_mean: float
    valence_range: float


class SpeakerBaselines(BaseModel):
    speakers: dict[str, SpeakerSummary]
    per_message_delta: list[SpeakerDelta | None]


class PersonaSessionSummary(BaseModel):
    session_number: int
    warm_start_applied: bool
    new_episodes: list[Episode] = Field(default_factory=list)
    state_snapshot: dict[str, float] = Field(default_factory=dict)
    prediction_available: bool = False


class DynamicsResponse(BaseModel):
    markers: list[ConversationMarker]
    message_vad: list[VADPoint]
    message_emotions: list[EmotionScore | None] = Field(default_factory=list)
    ued_metrics: UEDMetrics | None = None
    state_indices: StateIndices
    speaker_baselines: SpeakerBaselines | None = None
    temporal_patterns: list[TemporalPattern] = Field(default_factory=list)
    topology: TopologyReport | None = None
    reasoning: ReasoningReport | None = None
    persona_session: "PersonaSessionSummary | None" = None
    meta: AnalyzeMeta


# --- Semiotic Interpretation Models ---

class SemioticEntry(BaseModel):
    peirce: str              # "icon" | "index" | "symbol"
    signifikat: str
    cultural_frame: str = ""
    framing_type: str = ""
    myth: str = ""


class FramingHypothesis(BaseModel):
    framing_type: str
    label: str
    intensity: float = Field(ge=0.0, le=1.0)
    evidence_markers: list[str]
    message_indices: list[int]
    detection_count: int = 0
    myth: str = ""


class InterpretFindings(BaseModel):
    narrative: str = ""
    key_points: list[str] = Field(default_factory=list)
    relational_pattern: str | None = None
    bias_check: str | None = None


class InterpretResponse(BaseModel):
    framings: list[FramingHypothesis]
    semiotic_map: dict[str, SemioticEntry]
    dominant_framing: str | None = None
    findings: InterpretFindings | None = None
    meta: AnalyzeMeta


class MarkerDetail(BaseModel):
    id: str
    layer: Layer
    lang: str
    description: str
    frame: dict[str, Any]
    patterns: list[dict[str, Any]]
    examples: dict[str, list[str]]
    tags: list[str]
    rating: int
    family: str | None = None
    multiplier: float | None = None
    composed_of: Any = None
    scoring: dict[str, Any] | None = None
    activation: dict[str, Any] | None = None
    window: dict[str, Any] | None = None
    resonance_tags: list[str] = Field(default_factory=list)


class MarkerListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    markers: list[MarkerDetail]


class EngineConfig(BaseModel):
    version: str
    total_markers: int
    layers: dict[str, int]
    families: dict[str, Any]
    ewma: dict[str, Any]
    ars: dict[str, Any]
    bias_protection: dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "6.0"
    markers_loaded: int
    uptime_seconds: float


# --- Persona Models (Pro Tier) ---

class SpeakerEWMAState(BaseModel):
    valence: float
    arousal: float
    dominance: float
    message_count: int = 0
    sessions_seen: int = 0


class Episode(BaseModel):
    id: str
    type: str  # escalation_cluster | repair_trend | withdrawal_phase | rupture | stabilization
    session: int
    duration_messages: int
    markers_involved: list[str] = Field(default_factory=list)
    vad_delta: dict[str, float] = Field(default_factory=dict)
    state_at_entry: dict[str, float] = Field(default_factory=dict)
    state_at_exit: dict[str, float] = Field(default_factory=dict)


class PredictionReservoir(BaseModel):
    shift_counts: dict[str, int] = Field(default_factory=dict)
    shift_prior: dict[str, float] = Field(default_factory=dict)
    shift_given_valence_quartile: dict[str, dict[str, float]] = Field(default_factory=dict)
    top_transition_pairs: list[list] = Field(default_factory=list)


class PersonaStats(BaseModel):
    session_count: int
    total_messages: int
    first_session: str
    last_session: str


class PersonaCreateResponse(BaseModel):
    token: str
    created_at: str


class PredictionResponse(BaseModel):
    token: str
    session_count: int
    predictions: PredictionReservoir | None = None
    confidence: str = "insufficient_data"  # "low" | "medium" | "high" | "insufficient_data"


# --- Candidate Detection Models ---

class ExamplePassage(BaseModel):
    text: str
    context: str = ""
    source_dialogue_hash: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MarkerCandidate(BaseModel):
    candidate_id: str
    example_passages: list[ExamplePassage] = Field(default_factory=list)
    cluster_meaning: str
    frequency: int = Field(default=0, ge=0)
    related_markers: list[str] = Field(default_factory=list)
    coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    novelty: float = Field(default=0.0, ge=0.0, le=1.0)
    rank_score: float = Field(default=0.0, ge=0.0)
    status: str = "proposed"


# --- Narrative Analysis Models ---

class NarrativeActor(BaseModel):
    role: str
    apparent_position: str = ""
    register: str = ""  # noqa: register shadows BaseModel attr (harmless)
    claim_only: bool = False


class NarrativeRelationship(BaseModel):
    actors: list[str] = Field(default_factory=list)
    dynamic: str = ""
    evidence_tier: str = "A"
    supporting_marker_ids: list[str] = Field(default_factory=list)


class NarrativeBeliefSystem(BaseModel):
    label: str
    description: str = ""
    evidence_tier: str = "B"
    claim_of_speaker: bool = False


class HumanReviewFlag(BaseModel):
    marker_id: str
    reason: str  # "mis-triggered" | "context-incompatible" | "cultural-ambiguity"
    context_note: str = ""


class InitialSemanticsReport(BaseModel):
    narrative_domain: str
    discourse_type: str
    actors: list[NarrativeActor] = Field(default_factory=list)
    spatiotemporal_context: str = "unclear"
    cultural_frame: str = "uncertain"
    active_belief_systems: list[str] = Field(default_factory=list)
    tension_axis: str = ""
    semantic_readiness_score: float = Field(0.0, ge=0.0, le=1.0)
    pre_markers_expected: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class NarrativeReport(BaseModel):
    mode: InterpretationMode
    scenario: str
    actors: list[NarrativeActor] = Field(default_factory=list)
    timeline: str = "not_inferable"
    relationships: list[NarrativeRelationship] = Field(default_factory=list)
    belief_systems: list[NarrativeBeliefSystem] = Field(default_factory=list)
    marker_evidence_summary: dict[str, str] = Field(default_factory=dict)
    interpretation: str
    uncertainty_flags: list[str] = Field(default_factory=list)
    human_review_flags: list[HumanReviewFlag] = Field(default_factory=list)
    bias_check_summary: str
    evidence_tier_used: str = "A+B"


class NarrativeResponse(BaseModel):
    markers: list[ConversationMarker]
    initial_semantics: InitialSemanticsReport | None = None
    narrative_report: NarrativeReport | None = None
    meta: AnalyzeMeta


# --- Transcript Models ---

class TranscriptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100_000)


class TranscriptResponse(BaseModel):
    messages: list[Message]
    format_detected: str
    speaker_count: int


# Ensure forward references are resolved in this module namespace.
# This avoids FastAPI/Pydantic schema generation failures under some
# Python/Pydantic version combinations during app import.
for _model in (
    UEDMetrics,
    SpeakerSummary,
    SpeakerBaselines,
    DynamicsResponse,
):
    try:
        _model.model_rebuild(_types_namespace=globals())
    except TypeError:
        _model.model_rebuild()
