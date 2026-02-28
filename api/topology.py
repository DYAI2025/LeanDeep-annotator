"""
Conversation topology + constraint checks for LeanDeep 6.0.

Goal: deterministic, explainable "self-referential validation" by checking
invariants of discourse (adjacency, commitments, drift, repair).

This module intentionally avoids LLMs and heavy NLP. It operates on marker
detections + lightweight heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

    # Turn-taking asymmetry
    "asymmetry_window": 12,
    "asymmetry_ratio": 0.75,

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
# Marker IDs used as hooks
# ---------------------------------------------------------------------------

M_QUESTION = {"ATO_QUESTION", "ATO_QUESTIONING"}
M_CLARIFY = {"ATO_CLARIFY_REQ"}
M_ACK = {"ATO_ACK", "ATO_ACK_MICRO", "ATO_ACKNOWLEDGE"}
M_AVOID = {"ATO_AVOIDANCE_PHRASE", "SEM_AVOIDANCE_LOOP", "SEM_CONFLICT_AVOIDANCE"}
M_REFUSAL = {"ATO_TOPIC_REFUSAL"}

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
# Types & Helpers
# ---------------------------------------------------------------------------

@dataclass
class ConstraintResult:
    id: str
    severity: str            # "HARD" | "SOFT"
    status: str              # "pass" | "warn" | "fail"
    score: float
    message_indices: list[int] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

def _safe_text(messages: list[dict], i: int) -> str:
    try: return (messages[i].get("text") or "")
    except: return ""

def _role(messages: list[dict], i: int) -> str:
    try: return (messages[i].get("role") or "unknown")
    except: return "unknown"

def _is_skip_message(messages: list[dict], i: int) -> bool:
    return len(_safe_text(messages, i).strip()) < 2

def _build_marker_index(messages: list[dict], detections: Iterable[Any]) -> list[set[str]]:
    m = [set() for _ in range(len(messages))]
    for d in detections:
        mid = getattr(d, "marker_id", getattr(d, "id", None))
        if not mid: continue
        for idx in getattr(d, "message_indices", []) or []:
            if 0 <= idx < len(m): m[idx].add(mid)
    return m

def _has(msg_markers: list[set[str]], i: int, marker_set: set[str]) -> bool:
    if i < 0 or i >= len(msg_markers): return False
    return any(mid in msg_markers[i] for mid in marker_set)

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def compute_topology_report(
    messages: list[dict],
    detections: list[Any],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}
    msg_markers = _build_marker_index(messages, detections)
    M = len(messages)
    results: list[ConstraintResult] = []

    # Attribution guard
    quoted_msgs = {i for i in range(M) if _has(msg_markers, i, M_QUOTES)}

    # 1. CTG_QA_01: Question -> Answer
    open_pairs = []
    unresolved = 0
    N = int(cfg["adjacency_window"])
    for i in range(M):
        if _is_skip_message(messages, i) or not _has(msg_markers, i, M_QUESTION): continue
        asker = _role(messages, i)
        partner_turns = [j for j in range(i + 1, min(M, i + 1 + N))
                         if _role(messages, j) != asker and not _is_skip_message(messages, j)]
        if not partner_turns:
            open_pairs.append({"q_idx": i, "by": asker, "resolved": None})
            continue
        j0 = partner_turns[0]
        answer_like = _has(msg_markers, j0, M_ACK) or (len(_safe_text(messages, j0)) >= cfg["min_answer_chars"])
        deferral = _has(msg_markers, j0, M_AVOID | M_REFUSAL)
        res = bool(answer_like or deferral)
        open_pairs.append({"q_idx": i, "by": asker, "resolved": res, "response_idx": j0})
        if not res: unresolved += 1

    qa_status = "fail" if unresolved >= 1 else "warn" if any(p["resolved"] is None for p in open_pairs) else "pass"
    results.append(ConstraintResult("CTG_QA_01", "HARD", qa_status, 
                                   cfg[f"score_{qa_status}"], 
                                   [p["q_idx"] for p in open_pairs]))

    # 2. CTG_THREAT_01: Threat -> Response
    threat_unhandled = 0
    for i in range(M):
        if _has(msg_markers, i, M_THREAT) and i not in quoted_msgs:
            spk = _role(messages, i)
            pt = [j for j in range(i + 1, min(M, i + 1 + N)) if _role(messages, j) != spk]
            if not pt or not _has(msg_markers, pt[0], M_ACK | {"ATO_NEGATION"} | M_APOLOGY):
                threat_unhandled += 1
    t_status = "fail" if threat_unhandled > 0 else "pass"
    results.append(ConstraintResult("CTG_THREAT_01", "HARD", t_status, cfg[f"score_{t_status}"], []))

    # 3. CTG_CIRC_01: Circular Reasoning
    circ_idxs = [i for i in range(M) if _has(msg_markers, i, M_CIRCULAR)]
    c_status = "fail" if circ_idxs else "pass"
    results.append(ConstraintResult("CTG_CIRC_01", "HARD", c_status, cfg[f"score_{c_status}"], circ_idxs))

    # 4. CTG_COMMIT_02: Contradiction
    broken = 0
    contradictions = [i for i in range(M) if _has(msg_markers, i, M_CONTRADICTION)]
    commit_idxs = [i for i in range(M) if _has(msg_markers, i, M_COMMIT)]
    for c_idx in contradictions:
        if any(ci < c_idx and _role(messages, ci) == _role(messages, c_idx) for ci in commit_idxs):
            broken += 1
    b_status = "fail" if broken > 0 else "pass"
    results.append(ConstraintResult("CTG_COMMIT_02", "HARD", b_status, cfg[f"score_{b_status}"], contradictions))

    # 5. CTG_EPIST_01: Absolutizers
    abs_count = sum(1 for i in range(M) if _has(msg_markers, i, M_ABSOLUTIZER))
    e_status = "fail" if abs_count >= 4 else "warn" if abs_count >= 2 else "pass"
    results.append(ConstraintResult("CTG_EPIST_01", "SOFT", e_status, cfg[f"score_{e_status}"], []))

    # Aggregate Health
    total_w = sum(cfg["weight_hard"] if r.severity=="HARD" else cfg["weight_soft"] for r in results)
    total_s = sum((cfg["weight_hard"] if r.severity=="HARD" else cfg["weight_soft"]) * r.score for r in results)
    health = total_s / total_w if total_w > 0 else 1.0
    grade = "green" if health >= cfg["grade_green"] else "yellow" if health >= cfg["grade_yellow"] else "red"

    return {
        "version": "ctg-0.1",
        "health": {"score": round(health, 3), "grade": grade},
        "constraints": [r.__dict__ for r in results],
        "summary": {
            "unresolved_questions": unresolved,
            "commitments_broken": broken,
            "absolutizer_count": abs_count
        },
        "gates": {
            "instability": grade == "red" or unresolved >= 3 or c_status == "fail",
            "gaslighting_present": any(_has(msg_markers, i, M_GAS) for i in range(M))
        }
    }
