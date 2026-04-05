# Specification Gap Resolution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve all Important (I1-I4) and Minor (M1-M3) findings from the 2026-04-05 gap analysis to achieve a clean Specification phase.

**Architecture:** Pure artifact work — no code changes. Create 2 missing requirements (REQ-SEC, REQ-REL), update assumption risk note, approve 5 Draft requirements, approve 4 Draft user stories, approve 1 Proposed decision. All changes in `1-spec/` and `decisions/`.

**Tech Stack:** Markdown files following SDLC artifact templates. Index sync in `1-spec/CLAUDE.spec.md`, state sync in `CLAUDE.md`.

---

## Task 1: Create REQ-SEC-data-handling (resolves I1)

**Files:**
- Create: `1-spec/requirements/REQ-SEC-data-handling.md`
- Modify: `1-spec/CLAUDE.spec.md` (add row to Requirements Index)
- Modify: `1-spec/user-stories/US-api-integration.md` (add requirement link)

**Step 1: Create the requirement file**

Create `1-spec/requirements/REQ-SEC-data-handling.md`:

```markdown
# REQ-SEC-data-handling

**Class**: Security  
**Priority**: Must-have  
**Status**: Draft

## Requirement

The system must **protect dialogue data in transit and at rest**, enforce authentication in production, sanitize all user input, and never persist raw dialogue content beyond the analysis request lifecycle without explicit consent.

### Specification

1. **Authentication Enforcement**:
   - Production deployments must have `LEANDEEP_REQUIRE_AUTH=true`
   - API key validation on every request (except /v1/health)
   - Invalid/missing keys return 401 with no data leakage in error body

2. **Transport Security**:
   - HTTPS required in production (enforced via Fly.io TLS termination)
   - No sensitive data in URL query parameters (use POST body)

3. **Input Sanitization**:
   - All user-supplied text is sanitized before processing (no injection vectors)
   - Maximum input size enforced (configurable, default 100KB per request)
   - Malformed JSON returns 400 with generic error (no stack traces)

4. **Data Lifecycle**:
   - Raw dialogue text is NOT persisted after analysis response is returned
   - Semantic frames and marker results may be cached (TTL-based, configurable)
   - Persona data (Pro tier) is stored only with explicit user consent via API
   - No dialogue content in application logs (log marker IDs, not text)

5. **Error Response Safety**:
   - Production error responses never include stack traces, internal paths, or debug info
   - Error codes are generic (not revealing implementation details)

### Acceptance Criteria

- [ ] Auth enforced when LEANDEEP_REQUIRE_AUTH=true (401 for missing/invalid key)
- [ ] No raw dialogue text persisted after response (verified via storage audit)
- [ ] No dialogue content in application logs (verified via log audit)
- [ ] Input size limit enforced (> 100KB returns 413)
- [ ] Malformed input returns 400 with safe error message (no stack trace)
- [ ] HTTPS enforced in production deployment
- [ ] Error responses in production contain no internal paths or debug info

## Related Artifacts

- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-rest-api](REQ-F-rest-api.md)

## Design Notes

See [2-design/api-design.md](../../2-design/api-design.md) for API error handling patterns. Auth middleware already exists (configurable via env var). Focus is on formalizing and testing the security posture.

## Test Plan

- Unit test: `tests/test_security.py::test_auth_required` — 401 without key when auth enabled
- Unit test: `tests/test_security.py::test_input_size_limit` — 413 for oversized input
- Unit test: `tests/test_security.py::test_safe_error_response` — no stack traces in 500 responses
- Integration test: `tests/test_security.py::test_no_dialogue_in_logs` — analyze request, grep logs for input text
- Audit: Manual review of log output and storage after analysis request

## Notes

Therapeutic dialogue data is sensitive by nature. Even without formal HIPAA/GDPR scope in MVP, treating data as confidential builds trust and avoids technical debt when compliance becomes required.
```

**Step 2: Add row to Requirements Index in `1-spec/CLAUDE.spec.md`**

Add after the REQ-SCA-rate-limiting row:

```markdown
| [REQ-SEC-data-handling](requirements/REQ-SEC-data-handling.md) | Security | Must-have | Draft | Protect dialogue data, enforce auth, sanitize input, no persistent storage without consent |
```

**Step 3: Add requirement link to `1-spec/user-stories/US-api-integration.md`**

In the Related Artifacts section, add:

```markdown
- Requirements: [REQ-SEC-data-handling](../requirements/REQ-SEC-data-handling.md)
```

**Step 4: Commit**

```bash
git add 1-spec/requirements/REQ-SEC-data-handling.md 1-spec/CLAUDE.spec.md 1-spec/user-stories/US-api-integration.md
git commit -m "feat(spec): add REQ-SEC-data-handling requirement

Resolves gap analysis finding I1: no security requirements.
Covers auth enforcement, input sanitization, data lifecycle,
and error response safety for sensitive dialogue data."
```

---

## Task 2: Create REQ-REL-provider-fallback (resolves I2)

**Files:**
- Create: `1-spec/requirements/REQ-REL-provider-fallback.md`
- Modify: `1-spec/CLAUDE.spec.md` (add row to Requirements Index)

**Step 1: Create the requirement file**

Create `1-spec/requirements/REQ-REL-provider-fallback.md`:

```markdown
# REQ-REL-provider-fallback

**Class**: Reliability  
**Priority**: Must-have  
**Status**: Draft

## Requirement

The system must **gracefully degrade when semantic providers (LLM APIs) are unavailable or slow**, automatically falling back to alternative providers or embedding-based analysis, and never returning a hard failure for analysis requests due to provider issues alone.

### Specification

1. **Provider Fallback Chain**:
   - Primary: configured provider (Gemini, OpenAI, Anthropic, Ollama)
   - Secondary: next available provider from configured list
   - Tertiary: embedding-based semantic profile (local, no external dependency)
   - Final: analysis without semantic frame (markers only, no frame-based weighting)

2. **Timeout & Retry**:
   - Provider timeout: 2s (configurable via LEANDEEP_SEMANTIC_TIMEOUT)
   - One retry with exponential backoff (2s, 4s)
   - After timeout + retry: switch to next provider in fallback chain
   - Total fallback resolution: < 5s

3. **Degraded Mode Signaling**:
   - Response includes `degraded: true` flag when fallback was used
   - Response includes `provider_used` field (which provider actually served the request)
   - Response includes `fallback_reason` field ("timeout", "error", "unavailable")
   - UI shows degradation warning to user

4. **Partial Results**:
   - If semantic framing fails entirely: return marker detection results without frame weighting
   - If narrative generation fails: return semantic frame + markers without narratives
   - Never return empty response due to provider failure

### Acceptance Criteria

- [ ] Analysis request succeeds even when primary provider is down (returns results via fallback)
- [ ] Fallback chain executes within 5s total (not stacking timeouts)
- [ ] Response includes degraded flag and fallback_reason when fallback is used
- [ ] Embedding-based fallback works without any external API dependency
- [ ] Partial results returned when only some pipeline stages fail
- [ ] Provider timeout is configurable via environment variable

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-semantic-framing](REQ-F-semantic-framing.md)
- Requirements: [REQ-PERF-conversation-latency](REQ-PERF-conversation-latency.md)

## Design Notes

See [2-design/architecture.md](../../2-design/architecture.md) for semantic provider architecture. The provider-agnostic design in `api/semantic.py` already supports multiple providers. This requirement formalizes the fallback behavior and degraded mode signaling.

## Test Plan

- Unit test: `tests/test_provider_fallback.py::test_primary_timeout_triggers_fallback` — mock primary timeout, verify secondary called
- Unit test: `tests/test_provider_fallback.py::test_all_providers_down_uses_embedding` — mock all providers failing, verify embedding fallback
- Unit test: `tests/test_provider_fallback.py::test_degraded_flag_in_response` — verify response metadata
- Integration test: `tests/test_provider_fallback.py::test_partial_results` — semantic framing fails, markers still returned
- Performance test: Total fallback resolution < 5s

## Notes

Reliability is critical for professional users. A therapist reviewing a session cannot tolerate "service unavailable" errors. The system should always return something useful, even if degraded.
```

**Step 2: Add row to Requirements Index in `1-spec/CLAUDE.spec.md`**

Add after REQ-SEC-data-handling row:

```markdown
| [REQ-REL-provider-fallback](requirements/REQ-REL-provider-fallback.md) | Reliability | Must-have | Draft | Graceful degradation with provider fallback chain and partial results |
```

**Step 3: Commit**

```bash
git add 1-spec/requirements/REQ-REL-provider-fallback.md 1-spec/CLAUDE.spec.md
git commit -m "feat(spec): add REQ-REL-provider-fallback requirement

Resolves gap analysis finding I2: no reliability requirements.
Covers provider fallback chain, degraded mode signaling,
partial results, and timeout configuration."
```

---

## Task 3: Update assumption risk note (resolves I3)

**Files:**
- Modify: `1-spec/assumptions/ASM-ki-semantic-framing-sufficient.md`

**Step 1: Add verification timeline note**

In `ASM-ki-semantic-framing-sufficient.md`, update the `## Timeline` section:

Replace:
```markdown
## Timeline

- **Phase 1**: Run verification in parallel with MVP development (2-3 weeks)
- **Gate**: Before deploying production (must resolve assumption)
```

With:
```markdown
## Timeline

- **Phase 1**: Run verification in parallel with P0 implementation (Week 1-2 of Code phase)
- **Decision Gate (Week 2)**: If F1 < 0.75 on 3+ dimensions → STOP and evaluate alternatives
- **Production Gate**: Must be Verified before production deployment
- **Risk Accepted for Design Phase**: Proceeding to Design with assumption Unverified; verification runs in parallel with Code phase per tasks.md critical gates
```

**Step 2: Commit**

```bash
git add 1-spec/assumptions/ASM-ki-semantic-framing-sufficient.md
git commit -m "docs(spec): add verification timeline to ASM-ki-semantic-framing-sufficient

Resolves gap analysis finding I3: clarify that risk is accepted
for Design phase entry, with verification running in parallel."
```

---

## Task 4: Approve 5 Draft requirements (resolves I4)

**Files:**
- Modify: `1-spec/requirements/REQ-COMP-professional-interpretability.md` (Status: Draft → Approved)
- Modify: `1-spec/requirements/REQ-F-example-auto-enrichment.md` (Status: Draft → Approved)
- Modify: `1-spec/requirements/REQ-MNT-marker-evolution-tracking.md` (Status: Draft → Approved)
- Modify: `1-spec/requirements/REQ-F-rest-api.md` (Status: Draft → Approved)
- Modify: `1-spec/requirements/REQ-SCA-rate-limiting.md` (Status: Draft → Approved)
- Modify: `1-spec/CLAUDE.spec.md` (update 5 rows from Draft → Approved)

**Step 1: Update status in each requirement file**

In each of these 5 files, change:
```markdown
**Status**: Draft
```
To:
```markdown
**Status**: Approved
```

**Step 2: Update Requirements Index in `1-spec/CLAUDE.spec.md`**

Change the Status column from `Draft` to `Approved` for all 5 rows:
- REQ-COMP-professional-interpretability
- REQ-F-example-auto-enrichment
- REQ-MNT-marker-evolution-tracking
- REQ-F-rest-api
- REQ-SCA-rate-limiting

**Step 3: Commit**

```bash
git add 1-spec/requirements/REQ-COMP-professional-interpretability.md \
       1-spec/requirements/REQ-F-example-auto-enrichment.md \
       1-spec/requirements/REQ-MNT-marker-evolution-tracking.md \
       1-spec/requirements/REQ-F-rest-api.md \
       1-spec/requirements/REQ-SCA-rate-limiting.md \
       1-spec/CLAUDE.spec.md
git commit -m "feat(spec): approve 5 Draft requirements

Approve REQ-COMP-professional-interpretability,
REQ-F-example-auto-enrichment, REQ-MNT-marker-evolution-tracking,
REQ-F-rest-api, REQ-SCA-rate-limiting.

Resolves gap analysis finding I4."
```

**IMPORTANT:** This step requires human approval. The executing agent must confirm with the user before changing Status to Approved.

---

## Task 5: Approve 4 Draft user stories (resolves M1)

**Files:**
- Modify: `1-spec/user-stories/US-post-analysis-interpretation.md` (Status: Draft → Approved)
- Modify: `1-spec/user-stories/US-professional-bias-checking.md` (Status: Draft → Approved)
- Modify: `1-spec/user-stories/US-autonomous-marker-enrichment.md` (Status: Draft → Approved)
- Modify: `1-spec/user-stories/US-api-integration.md` (Status: Draft → Approved)
- Modify: `1-spec/CLAUDE.spec.md` (update 4 rows from Draft → Approved)

**Step 1: Update status in each user story file**

In each of these 4 files, change:
```markdown
**Status**: Draft
```
To:
```markdown
**Status**: Approved
```

**Step 2: Update User Stories Index in `1-spec/CLAUDE.spec.md`**

Change the Status column from `Draft` to `Approved` for all 4 rows.

**Step 3: Commit**

```bash
git add 1-spec/user-stories/US-post-analysis-interpretation.md \
       1-spec/user-stories/US-professional-bias-checking.md \
       1-spec/user-stories/US-autonomous-marker-enrichment.md \
       1-spec/user-stories/US-api-integration.md \
       1-spec/CLAUDE.spec.md
git commit -m "feat(spec): approve 4 Draft user stories

Approve US-post-analysis-interpretation,
US-professional-bias-checking, US-autonomous-marker-enrichment,
US-api-integration.

Resolves gap analysis finding M1."
```

**IMPORTANT:** This step requires human approval. The executing agent must confirm with the user before changing Status to Approved.

---

## Task 6: Approve DEC-semantic-guided-multi-perspective-architecture (resolves M2)

**Files:**
- Modify: `decisions/DEC-semantic-guided-multi-perspective-architecture.md`

**Step 1: Update decision status**

Change:
```markdown
**Status**: Proposed  
**Made By**: ai-proposed/human-approval-pending
```
To:
```markdown
**Status**: Approved  
**Made By**: human-decided
```

**Step 2: Commit**

```bash
git add decisions/DEC-semantic-guided-multi-perspective-architecture.md
git commit -m "feat(spec): approve DEC-semantic-guided-multi-perspective-architecture

Foundational architecture decision approved by product owner.
Resolves gap analysis finding M2."
```

**IMPORTANT:** This step requires human approval. The executing agent must confirm with the user before approving this architectural decision.

---

## Task 7: Update Current State and record final gap analysis (closes all findings)

**Files:**
- Modify: `CLAUDE.md` (Current State section)

**Step 1: Update the Specification line in Current State**

Replace the current Specification line with:

```markdown
- **Specification**: 5 stakeholders; 4 goals (3 Approved, 1 Draft); 4 user stories (all Approved); 13 requirements (all Approved); 1 assumption (Unverified, risk accepted for Design); 1 constraint (Active). Gap analysis (2026-04-05): 0 Critical, 0 Important, 1 Minor (REQ-PORT empty — acceptable)
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update Current State after gap analysis resolution

All Critical, Important, and Minor findings resolved except
REQ-PORT (accepted as not needed for API service)."
```

---

## Verification: Final State

After all tasks complete, the project should have:

| Artifact | Total | Approved | Draft |
|----------|-------|----------|-------|
| Goals | 4 | 3 | 1 (Phase 2+) |
| User Stories | 4 | 4 | 0 |
| Requirements | 13 | 13 | 0 |
| Assumptions | 1 | 0 | 0 (Unverified, risk noted) |
| Constraints | 1 | 0 | 0 (Active) |
| Decisions | 2 | 2 | 0 |

**Spec → Design gate**: All preconditions met. Ready for `/SDLC-design`.

| Requirement Class | Count |
|-------------------|-------|
| REQ-F | 5 |
| REQ-PERF | 1 |
| REQ-USA | 1 |
| REQ-COMP | 1 |
| REQ-MNT | 1 |
| REQ-SCA | 1 |
| REQ-SEC | 1 |
| REQ-REL | 1 |
| REQ-PORT | 0 (accepted) |
