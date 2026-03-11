"""
Narrative Analysis Module for LeanDeep 6.0.

Two-stage LLM layer:
  1. InitialSemanticsGenerator  — pre-analysis: defines the narrative-semantic space
  2. NarrativeReportGenerator   — post-analysis: produces objective report with 3 interpretation modes

Interpretation modes:
  - Clinical:    Pattern-analytic language, analytic lenses only (no diagnoses), formal, evidence-bound
  - Narrative:   Story-framed, accessible language, actors / scenes / relationships
  - Explorative: Explicitly speculative, flags assumptions, invites multi-reading

Evidence tiers (strictly separated):
  A) Direct textual evidence (quotes + marker triggers)
  B) Plausible hypotheses (marker resonance patterns)
  C) Explorative theses (explicitly speculative)

Non-goals:
  - No psychotherapy / medical / legal advice
  - No moral evaluation of participants
  - No endorsement of any speaker's claims or beliefs
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger("leandeep.narrative")


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class InterpretationMode(str, Enum):
    CLINICAL = "Clinical"
    NARRATIVE = "Narrative"
    EXPLORATIVE = "Explorative"


_MODE_INSTRUCTIONS: dict[InterpretationMode, str] = {
    InterpretationMode.CLINICAL: (
        "Use pattern-analytic language. Reference psychological or relational patterns ONLY as "
        "analytic lenses, never as diagnoses. Be formal, precise, and evidence-bound. "
        "Prefix every interpretive statement with 'Pattern analysis suggests...' or 'Marker evidence "
        "indicates...'. Avoid emotional language."
    ),
    InterpretationMode.NARRATIVE: (
        "Frame the output as a story with actors, scenes, and a timeline. Use accessible, "
        "non-technical language. Describe what appears to be happening from a neutral narrator's "
        "perspective. Avoid clinical jargon. Treat participants as characters, not patients."
    ),
    InterpretationMode.EXPLORATIVE: (
        "Present multiple possible readings. Each thesis MUST be prefixed with 'Hypothesis:' "
        "and labeled with confidence (speculative / plausible / supported). Explicitly flag "
        "assumptions and invite alternative interpretations. Mark uncertain cultural inferences "
        "as UNCERTAIN."
    ),
}


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------

class Actor(BaseModel):
    role: str = Field(..., description="Speaker role label (A/B, therapist/client, etc.)")
    apparent_position: str = Field("", description="Inferred discourse position (e.g., accuser, mediator)")
    register: str = Field("", description="Dominant register inferred for this actor")  # noqa: register shadows BaseModel attr (harmless)
    claim_only: bool = Field(
        False,
        description="True if inferred position is CLAIM (speaker's assertion, not marker-supported)"
    )


class NarrativeRelationship(BaseModel):
    actors: list[str] = Field(default_factory=list, description="Roles involved")
    dynamic: str = Field("", description="Relationship dynamic described in plain terms")
    evidence_tier: str = Field("A", description="A=direct evidence / B=hypothesis / C=speculative")
    supporting_marker_ids: list[str] = Field(default_factory=list)


class BeliefSystem(BaseModel):
    label: str = Field(..., description="Name of the myth/norm/belief system")
    description: str = Field("", description="How it manifests in the text")
    evidence_tier: str = Field("B", description="A/B/C evidence tier")
    claim_of_speaker: bool = Field(
        False, description="True if this is a speaker's CLAIM, not marker-grounded"
    )


class HumanReviewFlag(BaseModel):
    marker_id: str
    reason: str  # "mis-triggered" | "context-incompatible" | "cultural-ambiguity"
    context_note: str = ""


class InitialSemanticsOutput(BaseModel):
    """Pre-analysis semantic space definition produced before marker detection."""

    narrative_domain: str = Field(
        ...,
        description="High-level domain (e.g., romantic_conflict, workplace_negotiation, family_dynamics)"
    )
    discourse_type: str = Field(
        ...,
        description="e.g., argumentative_bilateral, monologue_confessional, therapeutic_dialogue"
    )
    actors: list[Actor] = Field(default_factory=list)
    spatiotemporal_context: str = Field("unclear", description="Inferred setting if detectable")
    cultural_frame: str = Field(
        "uncertain",
        description="Dominant cultural context; mark as UNCERTAIN if not inferable"
    )
    active_belief_systems: list[str] = Field(
        default_factory=list,
        description="Pre-activated cultural norms/myths that may shape marker salience"
    )
    tension_axis: str = Field(
        "",
        description="Primary tension axis (e.g., autonomy_vs_closeness, fairness_vs_loyalty)"
    )
    semantic_readiness_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="How much semantic context is inferable [0=opaque, 1=fully clear]"
    )
    pre_markers_expected: list[str] = Field(
        default_factory=list,
        description="Marker IDs the semantic context suggests are likely to fire"
    )
    uncertainty_notes: list[str] = Field(
        default_factory=list,
        description="Aspects that remain unclear or culturally ambiguous"
    )


class NarrativeReportOutput(BaseModel):
    """Post-analysis semantic report produced after marker detection."""

    mode: InterpretationMode
    scenario: str = Field(..., description="2-4 sentence neutral description of the situation")
    actors: list[Actor] = Field(default_factory=list)
    timeline: str = Field(
        "",
        description="Temporal/spatial arc if inferable from text; 'not_inferable' otherwise"
    )
    relationships: list[NarrativeRelationship] = Field(default_factory=list)
    belief_systems: list[BeliefSystem] = Field(default_factory=list)
    marker_evidence_summary: dict[str, str] = Field(
        default_factory=dict,
        description="marker_id -> brief explanation of what it reveals in this context"
    )
    interpretation: str = Field(
        ...,
        description="Main interpretive synthesis, mode-appropriate framing"
    )
    uncertainty_flags: list[str] = Field(default_factory=list)
    human_review_flags: list[HumanReviewFlag] = Field(default_factory=list)
    bias_check_summary: str = Field(
        ...,
        description="Bias audit: confirmation / negativity / cultural / authority bias checks"
    )
    evidence_tier_used: str = Field(
        "A+B",
        description="Which tiers are represented: A (direct), B (hypothesis), C (speculative)"
    )


# ---------------------------------------------------------------------------
# InitialSemanticsGenerator
# ---------------------------------------------------------------------------

class InitialSemanticsGenerator:
    """
    Pre-analysis LLM call that defines the narrative-semantic space before markers run.

    This primes interpretation by surfacing:
      - discourse domain and type
      - inferred actors and their positions
      - cultural frame and active belief systems
      - tension axis

    The output is passed to the marker engine (as context enrichment hint) and to
    NarrativeReportGenerator for post-analysis synthesis.
    """

    def __init__(self):
        self.enabled = bool(settings.google_api_key)
        self._model = None

        if self.enabled:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self._model = genai.GenerativeModel(settings.reasoning_model)
            except ImportError:
                logger.warning("google-generativeai not installed. Initial semantics disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for initial semantics: {e}")
                self.enabled = False

    async def generate(
        self,
        messages: list[dict],
        language: str = "de",
    ) -> InitialSemanticsOutput | None:
        """Generate the pre-analysis semantic space for a conversation."""
        if not self.enabled or not self._model:
            return None

        text_sample = self._sample_text(messages)
        prompt = self._build_initial_semantics_prompt(text_sample, language)

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            return InitialSemanticsOutput(**data)
        except Exception as e:
            logger.error(f"InitialSemanticsGenerator failed: {e}")
            return None

    def _sample_text(self, messages: list[dict], max_chars: int = 2000) -> str:
        """Produce a representative text sample without including the full conversation."""
        parts = []
        total = 0
        for msg in messages:
            role = msg.get("role", "?")
            text = msg.get("text", "")[:400]  # max 400 chars per message
            chunk = f"[{role}]: {text}"
            if total + len(chunk) > max_chars:
                parts.append("...[truncated]")
                break
            parts.append(chunk)
            total += len(chunk)
        return "\n".join(parts)

    def _build_initial_semantics_prompt(self, text_sample: str, language: str) -> str:
        return f"""
You are a narrative semanticist analyzing text for the LeanDeep discourse analysis system.

TASK: Before running marker detection, define the narrative-semantic space this text operates in.
      This "semantic priming" helps downstream analysis interpret markers correctly.

RULES:
1. NEUTRALITY: Never judge participants as good/bad/healthy/unhealthy/right/wrong.
2. CLAIMS: If you infer a speaker's position but it is only the speaker's claim (not evidence-based),
   set actor.claim_only = true.
3. CULTURAL UNCERTAINTY: If cultural context is unclear, set cultural_frame = "UNCERTAIN" and
   add a note to uncertainty_notes.
4. DO NOT DIAGNOSE: You describe discourse patterns, not psychological conditions.
5. EVIDENCE TIER: Use "A" for direct textual evidence, "B" for plausible hypothesis, "C" for speculative.
6. LANGUAGE: The text may be in {language}. Respond in English for schema consistency.

TEXT SAMPLE:
{text_sample}

OUTPUT FORMAT:
Return a valid JSON matching this schema exactly:
{{
  "narrative_domain": "string (e.g., romantic_conflict, workplace_negotiation, family_dynamics, self_reflection)",
  "discourse_type": "string (e.g., argumentative_bilateral, monologue_confessional, therapeutic_dialogue)",
  "actors": [
    {{
      "role": "string (A/B or role label)",
      "apparent_position": "string (e.g., accuser, mediator, supporter)",
      "register": "string (e.g., emotional, formal, defensive)",
      "claim_only": boolean
    }}
  ],
  "spatiotemporal_context": "string or 'unclear'",
  "cultural_frame": "string or 'UNCERTAIN'",
  "active_belief_systems": ["string"],
  "tension_axis": "string (e.g., autonomy_vs_closeness, fairness_vs_loyalty) or ''",
  "semantic_readiness_score": float (0.0-1.0),
  "pre_markers_expected": ["MARKER_ID"],
  "uncertainty_notes": ["string"]
}}
"""


# ---------------------------------------------------------------------------
# NarrativeReportGenerator
# ---------------------------------------------------------------------------

class NarrativeReportGenerator:
    """
    Post-analysis LLM call that synthesizes an objective narrative report from detected markers.

    Supports three interpretation modes: Clinical, Narrative, Explorative.
    Strictly separates evidence tiers A/B/C.
    Includes mandatory bias check and human-review flagging.
    """

    def __init__(self):
        self.enabled = bool(settings.google_api_key)
        self._model = None

        if self.enabled:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self._model = genai.GenerativeModel(settings.reasoning_model)
            except ImportError:
                logger.warning("google-generativeai not installed. Narrative report disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for narrative report: {e}")
                self.enabled = False

    async def generate(
        self,
        messages: list[dict],
        detections: list[Any],
        initial_semantics: InitialSemanticsOutput | None,
        mode: InterpretationMode = InterpretationMode.NARRATIVE,
        language: str = "de",
    ) -> NarrativeReportOutput | None:
        """Generate the post-analysis narrative report."""
        if not self.enabled or not self._model:
            return None

        briefing = self._prepare_briefing(messages, detections, initial_semantics)
        prompt = self._build_narrative_prompt(briefing, mode, language)

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            data["mode"] = mode.value
            return NarrativeReportOutput(**data)
        except Exception as e:
            logger.error(f"NarrativeReportGenerator failed: {e}")
            return None

    def _prepare_briefing(
        self,
        messages: list[dict],
        detections: list[Any],
        initial_semantics: InitialSemanticsOutput | None,
    ) -> dict:
        """Condense everything into a structured briefing for the LLM."""
        top_markers = sorted(
            detections, key=lambda d: getattr(d, "confidence", 0), reverse=True
        )[:20]

        marker_list = [
            {
                "id": getattr(d, "id", getattr(d, "marker_id", "")),
                "layer": getattr(d, "layer", ""),
                "confidence": round(getattr(d, "confidence", 0), 3),
                "description": getattr(d, "description", ""),
                "family": getattr(d, "family", None),
            }
            for d in top_markers
        ]

        # Sample messages — include all roles to avoid authority bias
        text_sample = []
        for i, msg in enumerate(messages[:20]):
            text_sample.append({
                "index": i,
                "role": msg.get("role", "?"),
                "excerpt": msg.get("text", "")[:300],
            })

        briefing: dict = {
            "messages_sample": text_sample,
            "total_messages": len(messages),
            "detected_markers": marker_list,
            "total_detections": len(detections),
        }

        if initial_semantics:
            briefing["initial_semantics"] = initial_semantics.model_dump()

        return briefing

    def _build_narrative_prompt(
        self, briefing: dict, mode: InterpretationMode, language: str
    ) -> str:
        mode_instruction = _MODE_INSTRUCTIONS[mode]
        return f"""
You are the narrative analysis engine for LeanDeep 6.0.
You produce an objective, traceable semantic report of a conversation/text based on detected markers.

INTERPRETATION MODE: {mode.value}
MODE INSTRUCTION: {mode_instruction}

MANDATORY RULES (apply to ALL modes):
1. EVIDENCE TIERS — strictly separate:
   - Tier A: Direct textual evidence (quote a passage, name the marker that triggered)
   - Tier B: Plausible hypothesis (marker resonance pattern, not directly quoted)
   - Tier C: Explorative thesis (explicitly speculative, labeled as such)
2. CLAIMS: Any speaker's assertion that cannot be verified via markers → label as CLAIM.
3. NEUTRALITY: Never rate participants as good/bad/healthy/unhealthy/right/wrong.
4. CULTURAL SENSITIVITY: If you use a cultural frame inference, and it is uncertain, prefix with UNCERTAIN.
5. HUMAN_REVIEW: If a detected marker appears mis-triggered or context-incompatible, flag it in
   human_review_flags with reason and context_note.
6. BIAS CHECK: After synthesis, run internal checks for:
   - Confirmation bias (only selected supporting evidence)
   - Negativity/positivity bias (skewed emotional framing)
   - Cultural bias (overconfident cultural assumptions)
   - Authority bias (trusting one speaker more without evidence)
   Output findings in bias_check_summary, including what was corrected.
7. MISSING INPUT GUARD: If the transcript is too short or ambiguous for any field, use "" or
   "not_inferable" rather than inventing content.
8. NO DIAGNOSIS: You do not diagnose. Analytic patterns may be named as lenses, not conditions.
9. LANGUAGE: Text may be in {language}. Output in English for schema consistency.

BRIEFING:
{json.dumps(briefing, indent=2, ensure_ascii=False)}

OUTPUT FORMAT:
Return a valid JSON matching this schema exactly:
{{
  "mode": "{mode.value}",
  "scenario": "string (2-4 sentences, neutral)",
  "actors": [
    {{
      "role": "string",
      "apparent_position": "string",
      "register": "string",
      "claim_only": boolean
    }}
  ],
  "timeline": "string or 'not_inferable'",
  "relationships": [
    {{
      "actors": ["role_A", "role_B"],
      "dynamic": "string",
      "evidence_tier": "A|B|C",
      "supporting_marker_ids": ["MARKER_ID"]
    }}
  ],
  "belief_systems": [
    {{
      "label": "string",
      "description": "string",
      "evidence_tier": "A|B|C",
      "claim_of_speaker": boolean
    }}
  ],
  "marker_evidence_summary": {{
    "MARKER_ID": "what this marker reveals in this specific context"
  }},
  "interpretation": "string (main synthesis, mode-appropriate)",
  "uncertainty_flags": ["string"],
  "human_review_flags": [
    {{
      "marker_id": "string",
      "reason": "mis-triggered|context-incompatible|cultural-ambiguity",
      "context_note": "string"
    }}
  ],
  "bias_check_summary": "string (findings + corrections applied)",
  "evidence_tier_used": "A|A+B|A+B+C"
}}
"""


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

initial_semantics_generator = InitialSemanticsGenerator()
narrative_report_generator = NarrativeReportGenerator()
