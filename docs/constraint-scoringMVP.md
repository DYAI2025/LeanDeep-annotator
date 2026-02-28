## Kernverstaendnis

Du willst jetzt drei Dinge in "MVP-sicher":

**Default-Konfiguration** (Fensterlaengen, Schwellen, Gewichte)

**Constraint-Scoring -> Health-Score + Grade + Instability-Gate**

**Skeleton fuer **`api/topology.py` + minimaler Glue-Code fuer Engine/API

Ich liefere dir das so, dass es *deterministisch*, *erklaerbar* und *low-latency* bleibt (keine Embeddings, kein LLM).

---

## Default-Konfiguration (ctg-0.1)

**Fenster / Schwellen (Default):**

`adjacency_window N = 3`  (Frage/Demand/Threat erwartet Reaktion in den naechsten 3 Turns)

`min_answer_chars = 12`   (Heuristik fuer "answer-like", wenn kein ACK-Marker)

`clarify_window W = 5`, `clarify_k = 2`  (>=2 Clarify-Requests in 5 Turns => Loop-Warn)

`avoidance_window W = 6`, `avoidance_k = 3` (>=3 Avoidance-Signale in 6 Turns => Warn; Fail wenn Withdrawal-Pursuit dazukommt)

`commitment_window W = 5` (Commitment sollte innerhalb 5 Turns Follow-up/Retraction/Engagement haben)

`asymmetry_window = 12`, `asymmetry_ratio = 0.70` (optional spaeter aktivieren)

**Scoring:**

Status->Score: `pass=1.0`, `warn=0.6`, `fail=0.0`

Severity->Weight: `HARD=2.0`, `SOFT=1.0`

Health: gewichtetes Mittel aller Constraint-Scores

**Grade:**

`green >= 0.82`

`yellow >= 0.65`

sonst `red`

**Instability-Gate (MVP-Heuristik):**

`instability = True` wenn:

grade == red **oder**

`unresolved_questions >= 3` **oder**

`CTG_CIRC_01 == fail`

---

## Skeleton: `api/topology.py` (copy/paste)

Python

"""
Conversation topology + constraint checks for LeanDeep.

Goal: deterministic, explainable "self-referential validation" by checking
invariants of discourse (adjacency, commitments, drift, repair).

This module intentionally avoids LLMs and heavy NLP. It operates on marker
detections + lightweight heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Default configuration (MVP)
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    # Adjacency / response expectations
    "adjacency_window": 3,          # N
    "min_answer_chars": 12,

    # Loops / streaks
    "clarify_window": 5,
    "clarify_k": 2,
    "avoidance_window": 6,
    "avoidance_k": 3,

    # Commitments
    "commitment_window": 5,

    # Turn-taking asymmetry (optional later)
    "asymmetry_window": 12,
    "asymmetry_ratio": 0.70,

    # Health grading
    "grade_green": 0.82,
    "grade_yellow": 0.65,

    # Scoring
    "score_pass": 1.0,
    "score_warn": 0.6,
    "score_fail": 0.0,
    "weight_hard": 2.0,
    "weight_soft": 1.0,
}

# ---------------------------------------------------------------------------
# Marker IDs used as hooks (must exist in registry)
# ---------------------------------------------------------------------------

M_QUESTION = {"ATO_QUESTION", "ATO_QUESTIONING"}
M_CLARIFY = {"ATO_CLARIFY_REQ"}
M_ACK = {"ATO_ACK", "ATO_ACK_MICRO", "ATO_ACKNOWLEDGE"}
M_AVOID = {"ATO_AVOIDANCE_PHRASE", "SEM_AVOIDANCE_LOOP", "SEM_CONFLICT_AVOIDANCE"}
M_REFUSAL = {"ATO_TOPIC_REFUSAL"}   # explicit refusal

M_DEMAND = {"ATO_VEHEMENCE_DEMAND", "SEM_VEHEMENCE_DEMAND"}
M_APOLOGY = {"ATO_APOLOGY", "ATO_APOLOGY_DE"}
M_THREAT = {"ATO_THREAT_LANGUAGE"}

M_TOPIC_SHIFT = {
    "ATO_TOPIC_JUMP_MARKER",
    "ATO_TOPIC_SPLIT",
    "ATO_TOPIC_SWITCH_TECH",
    "ATO_TOPIC_SWITCH_ADVERSATIVE",
    "CLU_TOPIC_DRIFT",
}
M_CIRCULAR = {"CLU_CIRCULAR_REASONING"}
M_CONTRADICTION = {"SEM_CONTRADICTION", "CLU_SELF_CONTRADICTION", "ATO_CONTRADICTION_LEX"}

M_COMMIT = {
    "ATO_COMMITMENT_PHRASE",
    "ATO_COMMITMENT_PHRASES",
    "SEM_COMMITMENT_LOCKIN",
    "SEM_SOFT_COMMITMENT",
}

M_QUOTES = {"ATO_AMBIGUITY_QUOTES"}

M_ABSOLUTIZER = {"ATO_ABSOLUTIZER"}

M_GAS = {"SEM_GASLIGHTING", "SEM_GASLIGHTING_ATTEMPT", "CLU_GASLIGHTING_SEQUENCE", "MEMA_GASLIGHTER"}
M_WITHDRAW_PURSUIT = {"MEMA_WITHDRAWAL_PURSUIT_DYNAMIC"}

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class ConstraintResult:
    id: str
    severity: str            # "HARD" | "SOFT"
    status: str              # "pass" | "warn" | "fail"
    score: float
    message_indices: list[int]
    evidence: dict[str, Any]
    notes: str = ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_text(messages: list[dict], i: int) -> str:
    try:
        return (messages[i].get("text") or "")
    except Exception:
        return ""

def _role(messages: list[dict], i: int) -> str:
    try:
        return (messages[i].get("role") or "unknown")
    except Exception:
        return "unknown"

def _is_skip_message(messages: list[dict], i: int) -> bool:
    t = _safe_text(messages, i).strip()
    return len(t) < 2

def _build_marker_index(messages: list[dict], detections: Iterable[Any]) -> list[set[str]]:
    m = [set() for _ in range(len(messages))]
    for d in detections:
        mid = getattr(d, "marker_id", None)
        if not mid:
            continue
        for idx in getattr(d, "message_indices", []) or []:
            if 0 <= idx < len(m):
                m[idx].add(mid)
    return m

def _has(msg_markers: list[set[str]], i: int, marker_set: set[str]) -> bool:
    if i < 0 or i >= len(msg_markers):
        return False
    return any(mid in msg_markers[i] for mid in marker_set)

def _score_from_status(cfg: dict[str, Any], status: str) -> float:
    if status == "pass":
        return float(cfg["score_pass"])
    if status == "warn":
        return float(cfg["score_warn"])
    return float(cfg["score_fail"])

def _weight(cfg: dict[str, Any], severity: str) -> float:
    return float(cfg["weight_hard"] if severity == "HARD" else cfg["weight_soft"])

def _grade(cfg: dict[str, Any], health: float) -> str:
    if health >= float(cfg["grade_green"]):
        return "green"
    if health >= float(cfg["grade_yellow"]):
        return "yellow"
    return "red"

# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def compute_topology_report(
    messages: list[dict],
    detections: list[Any],
    *,
    message_vad: list[dict] | None = None,
    state_indices: dict | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Returns a dict that can be placed into engine.analyze_conversation output as "topology".
    """
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}

    msg_markers = _build_marker_index(messages, detections)
    M = len(messages)

    results: list[ConstraintResult] = []

    # Attribution guard: if quotes in a turn, downweight threat/commit eval on that message
    quoted_msgs = {i for i in range(M) if _has(msg_markers, i, M_QUOTES)}

    # ------------------------------------------------------------------
    # CTG_QA_01 Question -> Answer/Deferral
    # ------------------------------------------------------------------
    open_pairs = []
    unresolved = 0
    N = int(cfg["adjacency_window"])

    for i in range(M):
        if _is_skip_message(messages, i):
            continue
        if not _has(msg_markers, i, M_QUESTION):
            continue

        asker = _role(messages, i)

        # find first partner turn within window
        partner_turns = [j for j in range(i + 1, min(M, i + 1 + N))
                         if _role(messages, j) != asker and not _is_skip_message(messages, j)]
        if not partner_turns:
            open_pairs.append({"q_idx": i, "by": asker, "resolved": None, "within": N, "note": "no_partner_turn"})
            continue
        j0 = partner_turns[0]

        # evaluate response
        answer_like = _has(msg_markers, j0, M_ACK) or (
            len(_safe_text(messages, j0).strip()) >= int(cfg["min_answer_chars"])
            and not _has(msg_markers, j0, M_QUESTION | M_CLARIFY)
        )
        deferral = _has(msg_markers, j0, M_AVOID | M_REFUSAL)
        resolved = bool(answer_like or deferral)

        open_pairs.append({"q_idx": i, "by": asker, "resolved": resolved, "within": N, "response_idx": j0})
        if not resolved:
            unresolved += 1

    status = "pass"
    if unresolved >= 1:
        status = "fail"
    elif any(p.get("resolved") is None for p in open_pairs):
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_QA_01",
            severity="HARD",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted({p["q_idx"] for p in open_pairs if "q_idx" in p} |
                                   {p.get("response_idx") for p in open_pairs if p.get("response_idx") is not None}),
            evidence={
                "open_pairs": open_pairs,
                "markers": ["ATO_QUESTION", "ATO_QUESTIONING", "ATO_ACK*", "ATO_AVOIDANCE_PHRASE", "ATO_TOPIC_REFUSAL"],
            },
            notes=f"unresolved_questions={unresolved} (window N={N})",
        )
    )

    # ------------------------------------------------------------------
    # CTG_QA_02 Clarification loop (soft)
    # ------------------------------------------------------------------
    clarify_hits = [i for i in range(M) if _has(msg_markers, i, M_CLARIFY)]
    clarify_k = int(cfg["clarify_k"])
    clarify_w = int(cfg["clarify_window"])

    loop_events = []
    for i in clarify_hits:
        c = sum(1 for j in range(i, min(M, i + clarify_w)) if _has(msg_markers, j, M_CLARIFY))
        if c >= clarify_k:
            loop_events.append({"start_idx": i, "count": c, "window": clarify_w})

    status = "pass"
    if loop_events:
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_QA_02",
            severity="SOFT",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted({e["start_idx"] for e in loop_events}),
            evidence={"loop_events": loop_events, "markers": ["ATO_CLARIFY_REQ"]},
            notes=f"clarify_loop if >= {clarify_k} within W={clarify_w}",
        )
    )

    # ------------------------------------------------------------------
    # CTG_AVOID_01 Avoidance streak (soft->hard via withdrawal/pursuit)
    # ------------------------------------------------------------------
    avoid_w = int(cfg["avoidance_window"])
    avoid_k = int(cfg["avoidance_k"])
    streaks = []
    for i in range(M):
        c = sum(1 for j in range(i, min(M, i + avoid_w)) if _has(msg_markers, j, M_AVOID))
        if c >= avoid_k:
            streaks.append({"start_idx": i, "count": c, "window": avoid_w})

    status = "pass"
    if streaks:
        status = "warn"
        if any(_has(msg_markers, i, M_WITHDRAW_PURSUIT) for i in range(M)):
            status = "fail"

    results.append(
        ConstraintResult(
            id="CTG_AVOID_01",
            severity="SOFT",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted({s["start_idx"] for s in streaks}),
            evidence={"streaks": streaks, "markers": sorted(list(M_AVOID | M_WITHDRAW_PURSUIT))},
            notes=f"avoidance_streak if >= {avoid_k} within W={avoid_w}",
        )
    )

    # ------------------------------------------------------------------
    # CTG_CIRC_01 Circular reasoning (hard)
    # ------------------------------------------------------------------
    circ_idxs = [i for i in range(M) if _has(msg_markers, i, M_CIRCULAR)]
    status = "pass"
    if circ_idxs:
        status = "fail"

    results.append(
        ConstraintResult(
            id="CTG_CIRC_01",
            severity="HARD",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=circ_idxs,
            evidence={"markers": sorted(list(M_CIRCULAR)), "hits": circ_idxs},
            notes="circular reasoning marker detected",
        )
    )

    # ------------------------------------------------------------------
    # CTG_ATTR_01 Attribution guard (hard, warn if present)
    # ------------------------------------------------------------------
    status = "pass"
    if quoted_msgs:
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_ATTR_01",
            severity="HARD",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted(list(quoted_msgs)),
            evidence={"quoted_messages": sorted(list(quoted_msgs)), "markers": sorted(list(M_QUOTES))},
            notes="quoted turns: threats/commitments in same turn should be downweighted",
        )
    )

    # ------------------------------------------------------------------
    # CTG_THREAT_01 Threat requires response/boundary (hard)
    # ------------------------------------------------------------------
    threat_idxs = [i for i in range(M) if _has(msg_markers, i, M_THREAT) and i not in quoted_msgs]
    threat_unhandled = 0
    threat_events = []
    for i in threat_idxs:
        speaker = _role(messages, i)
        partner_turns = [j for j in range(i + 1, min(M, i + 1 + N))
                         if _role(messages, j) != speaker and not _is_skip_message(messages, j)]
        if not partner_turns:
            threat_events.append({"idx": i, "handled": None, "note": "no_partner_turn"})
            continue
        j0 = partner_turns[0]
        handled = _has(msg_markers, j0, M_ACK | {"ATO_NEGATION"} | M_APOLOGY)
        threat_events.append({"idx": i, "handled": handled, "response_idx": j0})
        if not handled:
            threat_unhandled += 1

    status = "pass"
    if threat_unhandled >= 1:
        status = "fail"
    elif any(e.get("handled") is None for e in threat_events):
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_THREAT_01",
            severity="HARD",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted({e["idx"] for e in threat_events} |
                                   {e.get("response_idx") for e in threat_events if e.get("response_idx") is not None}),
            evidence={"threat_events": threat_events, "markers": ["ATO_THREAT_LANGUAGE"]},
            notes=f"unhandled_threats={threat_unhandled}",
        )
    )

    # ------------------------------------------------------------------
    # CTG_COMMIT_01 Commitment follow-up (soft)
    # ------------------------------------------------------------------
    commit_idxs = [i for i in range(M) if _has(msg_markers, i, M_COMMIT) and i not in quoted_msgs]
    W = int(cfg["commitment_window"])
    unresolved_commits = 0
    commit_events = []

    for i in commit_idxs:
        speaker = _role(messages, i)
        follow = [j for j in range(i + 1, min(M, i + 1 + W))
                  if _role(messages, j) == speaker and not _is_skip_message(messages, j)]
        resolved = False
        follow_idx = None
        for j in follow:
            follow_idx = j
            if _has(msg_markers, j, M_ACK | M_APOLOGY | {"ATO_NEGATION"}):
                resolved = True
                break
            if len(_safe_text(messages, j).strip()) >= int(cfg["min_answer_chars"]) and not _has(msg_markers, j, M_AVOID):
                resolved = True
                break
        if not follow:
            commit_events.append({"idx": i, "resolved": None, "window": W})
        else:
            commit_events.append({"idx": i, "resolved": resolved, "follow_idx": follow_idx, "window": W})
            if not resolved:
                unresolved_commits += 1

    status = "pass"
    if unresolved_commits >= 1 or any(e.get("resolved") is None for e in commit_events):
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_COMMIT_01",
            severity="SOFT",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted({e["idx"] for e in commit_events} |
                                   {e.get("follow_idx") for e in commit_events if e.get("follow_idx") is not None}),
            evidence={"commit_events": commit_events, "markers": sorted(list(M_COMMIT))},
            notes=f"unresolved_commitments={unresolved_commits} (window W={W})",
        )
    )

    # ------------------------------------------------------------------
    # CTG_COMMIT_02 Contradiction after commitment (hard, uses contradiction markers)
    # ------------------------------------------------------------------
    broken = 0
    contradictions = [i for i in range(M) if _has(msg_markers, i, M_CONTRADICTION)]
    if commit_idxs and contradictions:
        for c_idx in contradictions:
            speaker = _role(messages, c_idx)
            prior_commit = any(ci < c_idx and _role(messages, ci) == speaker for ci in commit_idxs)
            if prior_commit:
                broken += 1

    status = "pass"
    if broken >= 1:
        status = "fail"

    results.append(
        ConstraintResult(
            id="CTG_COMMIT_02",
            severity="HARD",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=sorted(set(commit_idxs + contradictions)),
            evidence={
                "commitment_idxs": commit_idxs,
                "contradiction_idxs": contradictions,
                "broken_count": broken,
                "markers": sorted(list(M_CONTRADICTION | M_COMMIT)),
            },
            notes="commitment followed by contradiction markers",
        )
    )

    # ------------------------------------------------------------------
    # CTG_TOPIC_01 Topic shift present (soft)
    # ------------------------------------------------------------------
    topic_idxs = [i for i in range(M) if _has(msg_markers, i, M_TOPIC_SHIFT)]
    status = "pass"
    if topic_idxs:
        status = "warn"

    results.append(
        ConstraintResult(
            id="CTG_TOPIC_01",
            severity="SOFT",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=topic_idxs,
            evidence={"topic_events": topic_idxs, "markers": sorted(list(M_TOPIC_SHIFT))},
            notes="topic drift/shift markers present",
        )
    )

    # ------------------------------------------------------------------
    # CTG_EPIST_01 Absolutizers frequency (soft)
    # ------------------------------------------------------------------
    abs_idxs = [i for i in range(M) if _has(msg_markers, i, M_ABSOLUTIZER)]
    status = "pass"
    if len(abs_idxs) >= 2:
        status = "warn"
    if len(abs_idxs) >= 4:
        status = "fail"

    results.append(
        ConstraintResult(
            id="CTG_EPIST_01",
            severity="SOFT",
            status=status,
            score=_score_from_status(cfg, status),
            message_indices=abs_idxs,
            evidence={"absolutizer_idxs": abs_idxs, "markers": sorted(list(M_ABSOLUTIZER))},
            notes="absolutizer frequency (no external truth check)",
        )
    )

    # ------------------------------------------------------------------
    # Aggregate health
    # ------------------------------------------------------------------
    total_w = 0.0
    total_s = 0.0
    for r in results:
        w = _weight(cfg, r.severity)
        total_w += w
        total_s += w * float(r.score)

    health = (total_s / total_w) if total_w > 0 else 1.0
    grade = _grade(cfg, health)

    # Instability gate (MVP)
    instability = False
    if grade == "red":
        instability = True
    if unresolved >= 3:
        instability = True
    if any(r.id == "CTG_CIRC_01" and r.status == "fail" for r in results):
        instability = True

    gas_present = any(_has(msg_markers, i, M_GAS) for i in range(M))

    return {
        "version": "ctg-0.1",
        "health": {"score": round(health, 3), "grade": grade},
        "constraints": [
            {
                "id": r.id,
                "severity": r.severity,
                "status": r.status,
                "score": round(float(r.score), 3),
                "message_indices": r.message_indices,
                "evidence": r.evidence,
                "notes": r.notes,
            }
            for r in results
        ],
        "summary": {
            "open_questions": len(open_pairs),
            "unresolved_questions": unresolved,
            "commitments_open": len(commit_idxs),
            "commitments_broken": broken,
            "topic_drift_events": len(topic_idxs),
        },
        "gates": {
            "instability": instability,
            "attribution_guard_applied": bool(quoted_msgs),
            "gaslighting_present": gas_present,
        },
    }

---

## Engine-Integration (minimal)

In `api/engine.py` (am Ende von `analyze_conversation`, kurz vor `return {...}`):

Python

from .topology import compute_topology_report

topology = compute_topology_report(
    messages,
    all_detections,          # deduplicated detections
    message_vad=message_vad,
    state_indices=state_indices,
)

Und dann im Return-Dict:

Python

return {
    "detections": all_detections,
    "temporal_patterns": temporal,
    "message_vad": message_vad,
    "message_emotions": message_emotions,
    "ued_metrics": ued_metrics,
    "state_indices": state_indices,
    "speaker_baselines": speaker_baselines,
    "topology": topology,          # <-- neu
    "timing_ms": round(elapsed, 2),
}

---

## API-Models + Endpoint (minimal, robust)

### `api/models.py` (neue Pydantic Models)

Python

from typing import Any

class TopologyHealth(BaseModel):
    score: float
    grade: str

class TopologyConstraint(BaseModel):
    id: str
    severity: str
    status: str
    score: float
    message_indices: list[int] = []
    evidence: dict[str, Any] = {}
    notes: str = ""

class TopologyReport(BaseModel):
    version: str
    health: TopologyHealth
    constraints: list[TopologyConstraint] = []
    summary: dict[str, Any] = {}
    gates: dict[str, Any] = {}

class ConversationResponse(BaseModel):
    markers: list[ConversationMarker]
    temporal_patterns: list[TemporalPattern] = []
    meta: AnalyzeMeta
    topology: TopologyReport | None = None   # <-- neu

### `api/main.py` (Conversation endpoint)

Python

from .models import TopologyReport

topology = TopologyReport(**result["topology"]) if result.get("topology") else None

return ConversationResponse(
    markers=sorted(markers, key=lambda m: (-m.confidence, m.id)),
    temporal_patterns=temporal,
    topology=topology,   # <-- neu
    meta=AnalyzeMeta(...),
)

---

## Tool Calls & Evidenz (Action-Log)

**Action-ID:** run_python_calculation

**Grund:** Repo-Inspektion (Marker-IDs verifizieren, Engine-Return keys/Struktur, damit die Hooks exakt passen).

**Parameter:** `/mnt/data/LeanDeep-annotator-main.zip` -> `api/engine.py`, `build/markers_normalized/marker_registry.json`

---

## Reflexion & Bias-Report

Wichtigster Blindspot, den wir hier aktiv adressieren: **"Style/Rhythmus als Urteil"**. In dieser Version ist Rhythmus nicht Urteil, sondern nur indirekt (ueber Marker) und kann spaeter als Gate ergaenzt werden.

Commitment-Checks bleiben in MVP bewusst konservativ (mehr `warn` als `fail`), bis ihr echte "Progress"-Marker oder Task-Signale stabil habt.
