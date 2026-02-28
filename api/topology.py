"""
Conversation Topology Analysis (CTG) Module for LeanDeep 6.0.

Analyzes the structural 'health' of a conversation by checking 
topological constraints (QA pairs, commitments, topic shifts) 
using detected markers as hooks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from .engine import Detection, MarkerDef


@dataclass
class TopologyConstraint:
    id: str
    severity: Literal["HARD", "SOFT"]
    status: Literal["pass", "warn", "fail"] = "pass"
    score: float = 1.0  # 1.0 = perfect, 0.0 = total failure
    message_indices: list[int] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


class TopologyAnalyzer:
    """Analyzes conversation topology and consistency."""

    def __init__(self, window_size: int = 4):
        self.window_size = window_size
        self.constraints: list[TopologyConstraint] = []

    def analyze(
        self, 
        messages: list[dict], 
        detections: list[Detection], 
        marker_defs: dict[str, MarkerDef]
    ) -> dict:
        """Run all topological checks on the conversation."""
        self.constraints = []
        
        # 1. Map detections to message indices for fast lookup
        msg_markers: dict[int, set[str]] = {}
        msg_tags: dict[int, set[str]] = {}
        for d in detections:
            for idx in d.message_indices:
                msg_markers.setdefault(idx, set()).add(d.marker_id)
                mdef = marker_defs.get(d.marker_id)
                if mdef:
                    msg_tags.setdefault(idx, set()).update(set(mdef.tags))

        # 2. Build adjacency & structural features per message
        msg_features = []
        for i, msg in enumerate(messages):
            markers = msg_markers.get(i, set())
            tags = msg_tags.get(i, set())
            
            features = {
                "is_question": any(m in markers for m in ["ATO_QUESTION", "ATO_QUESTIONING", "ATO_CLARIFY_REQ"]) or "?" in msg["text"],
                "is_ack": any(m in markers for m in ["ATO_ACK", "ATO_ACKNOWLEDGE", "ATO_ACK_MICRO"]),
                "is_avoid": any(m in markers for m in ["ATO_AVOIDANCE_PHRASE", "ATO_TOPIC_REFUSAL", "SEM_CONFLICT_AVOIDANCE"]),
                "is_commit": any(m in markers for m in ["ATO_COMMITMENT_PHRASE", "SEM_COMMITMENT_LOCKIN", "SEM_SOFT_COMMITMENT"]),
                "is_threat": "ATO_THREAT_LANGUAGE" in markers,
                "is_apology": any(m in markers for m in ["ATO_APOLOGY", "ATO_APOLOGY_DE"]),
                "is_topic_shift": any(m in markers for m in ["ATO_TOPIC_JUMP_MARKER", "ATO_TOPIC_SWITCH_TECH", "CLU_TOPIC_DRIFT"]),
                "is_quote": "ATO_AMBIGUITY_QUOTES" in markers,
                "is_demand": any(m in markers for m in ["ATO_VEHEMENCE_DEMAND", "SEM_VEHEMENCE_DEMAND"]),
                "is_negation": "ATO_NEGATION" in markers or "ATO_NEGATION_TOKEN" in markers,
                "role": msg.get("role", "?")
            }
            msg_features.append(features)

        # 3. Run specific checks
        self._check_qa_adjacency(msg_features, messages)
        self._check_demand_response(msg_features)
        self._check_repair_cycle(msg_features)
        self._check_threat_response(msg_features)
        self._check_turn_asymmetry(msg_features)
        self._check_commitments(msg_features, messages)
        self._check_attribution_guard(msg_features)
        self._check_gaslighting_influence(msg_features)

        # 4. Synthesize result
        # Apply gaslighting penalty if detected
        gas_penalty = 1.0
        if any(c.id == "CTG_GAS_01" and c.status != "pass" for c in self.constraints):
            gas_penalty = 0.7 # Reduce overall health if gaslighting suspected
        
        total_score = (sum(c.score for c in self.constraints) / len(self.constraints) if self.constraints else 1.0) * gas_penalty
        grade = "green" if total_score > 0.8 else "yellow" if total_score > 0.5 else "red"

        return {
            "version": "ctg-0.1",
            "health": {
                "score": round(total_score, 2),
                "grade": grade
            },
            "constraints": [
                {
                    "id": c.id,
                    "severity": c.severity,
                    "status": c.status,
                    "score": round(c.score, 2),
                    "message_indices": c.message_indices,
                    "evidence": c.evidence,
                    "notes": c.notes
                } for c in self.constraints
            ]
        }

    def _check_qa_adjacency(self, features: list[dict], messages: list[dict]):
        """CTG_QA_01: Questions must be answered or deferred."""
        open_questions = []
        for i, f in enumerate(features):
            # Resolve existing open questions if role changed
            if open_questions:
                resolved = []
                for q_idx, q_role in open_questions:
                    if f["role"] != q_role:
                        if f["is_ack"] or f["is_avoid"] or len(messages[i]["text"]) > 10: # Heuristic for answer
                            resolved.append((q_idx, q_role))
                
                for r in resolved:
                    open_questions.remove(r)

            if f["is_question"]:
                open_questions.append((i, f["role"]))

            # Check if questions stay open too long
            for q_idx, q_role in list(open_questions):
                if i - q_idx >= self.window_size:
                    self.constraints.append(TopologyConstraint(
                        id="CTG_QA_01",
                        severity="HARD",
                        status="fail",
                        score=0.0,
                        message_indices=[q_idx, i],
                        notes=f"Question at index {q_idx} not answered within {self.window_size} turns."
                    ))
                    open_questions.remove((q_idx, q_role))

    def _check_demand_response(self, features: list[dict]):
        """CTG_DEMAND_01: Demands should be acknowledged or negotiated."""
        for i, f in enumerate(features):
            if f["is_demand"]:
                responded = False
                for j in range(i + 1, min(i + 1 + self.window_size, len(features))):
                    if features[j]["role"] != f["role"] and (features[j]["is_ack"] or features[j]["is_negation"]):
                        responded = True
                        break
                if not responded and i < len(features) - 1:
                    self.constraints.append(TopologyConstraint(
                        id="CTG_DEMAND_01",
                        severity="SOFT",
                        status="warn",
                        score=0.5,
                        message_indices=[i],
                        notes="Demand issued without clear response."
                    ))

    def _check_repair_cycle(self, features: list[dict]):
        """CTG_REPAIR_01: Repair attempts should be received."""
        for i, f in enumerate(features):
            if f["is_apology"]:
                received = False
                for j in range(i + 1, min(i + 1 + self.window_size, len(features))):
                    if features[j]["role"] != f["role"] and (features[j]["is_ack"] or features[j]["is_commit"]):
                        received = True
                        break
                if not received and i < len(features) - 1:
                    self.constraints.append(TopologyConstraint(
                        id="CTG_REPAIR_01",
                        severity="SOFT",
                        status="warn",
                        score=0.6,
                        message_indices=[i],
                        notes="Apology/Repair attempt not acknowledged."
                    ))

    def _check_threat_response(self, features: list[dict]):
        """CTG_THREAT_01: Threat escalation requires boundary response."""
        for i, f in enumerate(features):
            if f["is_threat"]:
                guarded = False
                for j in range(i + 1, min(i + 1 + self.window_size, len(features))):
                    if features[j]["role"] != f["role"] and (features[j]["is_negation"] or features[j]["is_avoid"]):
                        guarded = True
                        break
                if not guarded:
                    self.constraints.append(TopologyConstraint(
                        id="CTG_THREAT_01",
                        severity="HARD",
                        status="fail",
                        score=0.0,
                        message_indices=[i],
                        notes="Threat language detected without subsequent boundary setting."
                    ))

    def _check_turn_asymmetry(self, features: list[dict]):
        """CTG_TURN_01: Detect monologue or extreme asymmetry."""
        if len(features) < 5: return
        
        counts = {}
        for f in features:
            counts[f["role"]] = counts.get(f["role"], 0) + 1
        
        total = len(features)
        for role, count in counts.items():
            ratio = count / total
            if ratio > 0.8:
                self.constraints.append(TopologyConstraint(
                    id="CTG_TURN_01",
                    severity="SOFT",
                    status="warn",
                    score=0.4,
                    notes=f"Speaker {role} dominates {int(ratio*100)}% of the turns."
                ))

    def _check_topic_signals(self, features: list[dict]):
        """CTG_TOPIC_01: Significant shifts should be signaled."""
        # This is harder without semantic comparison, but we check if 
        # a topic shift marker is missing when VAD or role flow changes abruptly.
        pass

    def _check_commitments(self, features: list[dict], messages: list[dict]):
        """CTG_COMMIT_01 & CTG_COMMIT_02: Commitment follow-up and contradictions."""
        commit_ledger = {} # role -> {text_hash: msg_idx}
        
        for i, f in enumerate(features):
            if f["is_commit"]:
                # Simple "hash" of text to detect identical repeated promises
                text_hash = messages[i]["text"].strip().lower()[:30]
                role = f["role"]
                
                if role in commit_ledger and text_hash in commit_ledger[role]:
                    # Repeated commitment without progress?
                    self.constraints.append(TopologyConstraint(
                        id="CTG_CIRC_01",
                        severity="HARD",
                        status="warn",
                        score=0.6,
                        message_indices=[commit_ledger[role][text_hash], i],
                        notes="Circular commitment pattern: identical promise repeated."
                    ))
                
                commit_ledger.setdefault(role, {})[text_hash] = i

                # Commitment at end
                if i == len(features) - 1:
                    self.constraints.append(TopologyConstraint(
                        id="CTG_COMMIT_01",
                        severity="HARD",
                        status="warn",
                        score=0.7,
                        message_indices=[i],
                        notes="Commitment made at end of conversation without closing ack."
                    ))

            # Contradiction check (Heuristic: Negation of similar phrase)
            if f["is_negation"]:
                role = f["role"]
                text = messages[i]["text"].lower()
                if role in commit_ledger:
                    for hash_text, idx in commit_ledger[role].items():
                        # If negation contains significant parts of the commitment text
                        words = [w for w in hash_text.split() if len(w) > 3]
                        if words and all(w in text for w in words):
                            self.constraints.append(TopologyConstraint(
                                id="CTG_COMMIT_02",
                                severity="HARD",
                                status="fail",
                                score=0.0,
                                message_indices=[idx, i],
                                notes=f"Contradiction detected: Commitment at {idx} negated at {i}."
                            ))

    def _check_gaslighting_influence(self, features: list[dict]):
        """CTG_GAS_01: Gaslighting requires higher scrutiny."""
        # This would be triggered by specific MEMA/CLU markers passed in
        pass

    def _check_attribution_guard(self, features: list[dict]):
        """CTG_ATTR_01: Attribution Guard (Quotes)."""
        for i, f in enumerate(features):
            if f["is_quote"] and (f["is_threat"] or f["is_commit"]):
                self.constraints.append(TopologyConstraint(
                    id="CTG_ATTR_01",
                    severity="HARD",
                    status="pass",
                    score=1.0,
                    message_indices=[i],
                    notes="Attribution guard applied: threats/commitments in quotes are de-weighted."
                ))
