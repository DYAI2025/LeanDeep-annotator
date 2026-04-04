Phase-specific instructions for the **Specification** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase defines **what** we're building and **why**. Focus on clarity, measurability, and alignment with stakeholder needs.

For LeanDeep, this includes:
- Gaps in the current 5-layer architecture
- Marker enrichment requirements (examples, semantic affinity, negatives)
- Feature completeness (Pro tier features, Base tier stability)
- Quality targets for detection accuracy, performance, and reliability

## Phase Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Stakeholders | [`stakeholders.md`](stakeholders.md) | Roles with interests and influence |
| Goals | [`goals/`](goals/) | High-level outcomes |
| User Stories | [`user-stories/`](user-stories/) | User-facing capabilities and gaps |
| Requirements | [`requirements/`](requirements/) | Testable system requirements |
| Assumptions | [`assumptions/`](assumptions/) | Beliefs taken as true but not verified |
| Constraints | [`constraints/`](constraints/) | Hard limits on design and implementation |

---

## AI Guidelines

### Per-Artifact Guidance

**Stakeholders**: Users, maintainers, research consumers, API consumers. Identify influence level.

**Goals**: 
- Complete 5-layer architecture gaps
- Achieve quality targets (marker coverage, accuracy, API reliability)
- Stabilize Pro tier (personas, predictions)
Status: `Draft → Approved → Achieved → Deprecated`

**User Stories**: "As a [role], I want [capability], so that [benefit]."
Example: "As an API consumer, I want semantic affinity filtering to reduce false positives, so that analysis results are more clinically useful."
Status: `Draft → Approved → Implemented → Deprecated`

**Requirements**: Testable language (not "should be fast" — use metrics).
Classes: `REQ-F` Functional, `REQ-PERF` Performance, `REQ-SEC` Security, `REQ-REL` Reliability, `REQ-USA` Usability, `REQ-MNT` Maintainability, `REQ-PORT` Portability, `REQ-SCA` Scalability, `REQ-COMP` Compliance.
Status: `Draft → Approved → Implemented → Deprecated`

**Assumptions**: Record risk level and verification plan.
Example: "Swiss Ephemeris accuracy sufficient for Jieqi calculations (Medium risk; verify against astronomical almanac)"
Status: `Unverified → Verified | Invalidated`

**Constraints**: Technical, business, operational.
Example: "Marker file size < 5MB" or "Semantic provider must support streaming"
Status: `Active → Lifted`

### Conflict Resolution

A conflict exists when two or more requirements cannot both be satisfied.

**Never resolve silently.** Always surface before acting.

1. **Identify**: conflicting requirement IDs, sources, influence levels, incompatibility
2. **Ask the user**: what makes them incompatible, stakeholders, 2+ resolution options, recommended option
3. **Wait for explicit approval** before modifying any file
4. **Apply**: update affected requirements, user stories, goals
5. **Verify**: no conflicting artifacts remain

### Assumption Invalidation

When an assumption is found to be wrong:

1. **Identify impact**: list all artifacts depending on the assumption
2. **Ask the user**: present the invalidated assumption, affected artifacts, proposed adjustments
3. **Wait for explicit approval**
4. **Apply**: mark assumption as `Invalidated`, update/flag dependent artifacts
5. **Verify**: no artifacts remain based on invalidated assumption

### Artifact Deprecation

When an artifact is no longer relevant:

1. Propose deprecation with rationale and downstream impact
2. Wait for explicit approval
3. Change Status to `Deprecated`
4. Flag dependent artifacts

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| (TBD) | Marker rating lifecycle | When establishing quality gates |
| (TBD) | Semantic affinity enrichment scope | When prioritizing marker enhancement |
| (TBD) | Example enrichment strategy | When planning coverage targets |

---

## Stakeholders Index

(To be populated in `stakeholders.md`)

---

## Goals Index

| File | Priority | Status | Summary |
|------|----------|--------|---------|
| [GOAL-semantic-meaning-disclosure](goals/GOAL-semantic-meaning-disclosure.md) | Must-have | Approved | AI-guided post-analysis tool for semantic meaning revelation via marker resonance + context metrics |
| [GOAL-professional-diagnostic-support](goals/GOAL-professional-diagnostic-support.md) | Must-have | Approved | Support professionals with bias-resistant pattern detection + multi-perspective interpretation |
| [GOAL-real-time-live-analysis](goals/GOAL-real-time-live-analysis.md) | Should-have | Draft | Real-time stream analysis for fraud, negotiation, interrogation support (Phase 2+) |
| [GOAL-autonomous-marker-evolution](goals/GOAL-autonomous-marker-evolution.md) | Must-have | Approved | Self-learning marker system with weak marker clustering + autonomous enrichment |
| [GOAL-multi-channel-deployment](goals/GOAL-multi-channel-deployment.md) | Must-have | Approved | Multi-channel deployment (Native UI, REST API, Embedded) for integration |

---

## User Stories Index

| File | Role | Priority | Status | Summary |
|------|------|----------|--------|---------|
| [US-post-analysis-interpretation](user-stories/US-post-analysis-interpretation.md) | Researcher, API Consumer | Must-have | Draft | Upload dialogue → semantic frame + markers + multi-perspective interpretation |
| [US-professional-bias-checking](user-stories/US-professional-bias-checking.md) | Therapist, Psychologist | Must-have | Draft | Run session through LeanDeep to counteract personal interpretive bias |
| [US-autonomous-marker-enrichment](user-stories/US-autonomous-marker-enrichment.md) | Researcher, Maintainer | Must-have | Draft | System auto-proposes new examples + detects new marker candidates |
| [US-api-integration](user-stories/US-api-integration.md) | Developer, API Consumer | Must-have | Draft | Call REST API to embed semantic analysis in third-party platform |

---

## Requirements Index

| File | Type | Priority | Status | Summary |
|------|------|----------|--------|---------|
| [REQ-F-semantic-framing](requirements/REQ-F-semantic-framing.md) | Functional | Must-have | Draft | KI generates semantic frame for dialogue context (tone, themes, dynamics) |
| [REQ-F-marker-resonance-weighting](requirements/REQ-F-marker-resonance-weighting.md) | Functional | Must-have | Draft | Marker confidence weighted by semantic frame resonance (reduce false positives) |
| [REQ-F-multi-narrative-analysis](requirements/REQ-F-multi-narrative-analysis.md) | Functional | Must-have | Draft | Generate >= 3 alternative narrative interpretations per dialogue |
| [REQ-USA-interactive-visualization](requirements/REQ-USA-interactive-visualization.md) | Usability | Must-have | Draft | Color-coded text highlights + contextual tooltips + narrative linking |
| [REQ-PERF-conversation-latency](requirements/REQ-PERF-conversation-latency.md) | Performance | Must-have | Draft | Conversation analysis p95 < 500ms; full interpretation p95 < 1s |
| [REQ-F-candidate-detection](requirements/REQ-F-candidate-detection.md) | Functional | Must-have | Draft | Auto-detect new marker candidates from dialogue patterns |

---

## Assumptions Index

| File | Category | Status | Risk | Summary |
|------|----------|--------|------|---------|
| [ASM-ki-semantic-framing-sufficient](assumptions/ASM-ki-semantic-framing-sufficient.md) | Technology | Unverified | Medium | LLM semantic framing (Gemini/OpenAI) is accurate >= 80% and fast < 500ms |

---

## Constraints Index

| File | Category | Status | Summary |
|------|----------|--------|---------|
| [CON-no-compose-of-rules](constraints/CON-no-compose-of-rules.md) | Technical/Design | Active | No hard compose-of rules; marker creation free-form; learn from observation (Phase 2+ for rules) |
