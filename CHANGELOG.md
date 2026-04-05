# Changelog

All notable changes to LeanDeep are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **Resonanzraum GUI** (`/resonanzraum`) — acoustic-aesthetic analysis interface
  - 3-column layout: Frame-Spektrum (270px) | Annotierter Verlauf (flex) | Narrative Obertöne (310px)
  - Animated waveform header (color shifts amber ↔ cyan per `emotional_tenor`)
  - 7-bar equalizer for SemanticFrame dimensions with 75ms stagger animation
  - Context meters for `context_validity` (cyan) and `offline_context_risk` (coral)
  - Marker span highlighting: ATO=amber, SEM=cyan, CLU=coral, MEMA=lavender
  - Hover tooltips (100ms delay, viewport-aware positioning)
  - Narrative cards with slide-in stagger, confidence fill bars, and marker ref chips
  - Bidirectional Marker ↔ Narrative linking via click
  - Equalizer morph when switching narrative perspectives
  - Page-load fadeUp stagger per column
  - Grain texture overlay (SVG feTurbulence, z-index:999)
  - Dialogue input parser for 3 formats: role-labelled (`A: text`), paragraph, single
  - Cmd/Ctrl+Enter shortcut to trigger analysis
  - Scan-line loading animation on panels
  - Pulse animation on active marker spans
  - Bridge helpers for LeanDeep 5.x API compatibility (TODOs for 6.0 upgrade)
  - Typography: Cormorant Garamond (display) + DM Mono (data)
- New FastAPI route `GET /resonanzraum` serving `api/static/resonanzraum.html`

### Fixed
- **[Security]** XSS vulnerability in narrative card innerHTML — all API-derived strings now passed through `escHtml()` helper (`n.narrative`, `n.text`, marker IDs, layer class names, EQ dimension values)
- **[Security]** XSS in equalizer `row.innerHTML` — `dim.fmt(val)` output escaped
- **[Bug]** Tooltip `z-index: 500` was below grain overlay `z-index: 999` → tooltip was hidden; raised to `z-index: 1001`
- **[Bug]** Overlapping marker spans caused incorrect text slicing; added `safeStart = Math.max(s.start, cursor)` guard and early-return for fully-subsumed spans
- **[Bug]** Error state in `runAnalysis()` destroyed `input-area` and `annotated-output` DOM nodes; `resetView()` then threw null-reference errors — replaced with non-destructive error overlay (`#error-overlay`)
- **[Perf]** `requestAnimationFrame` waveform loop ran continuously on hidden tabs (CPU waste) — paused via `document.hidden` check
- **[Perf]** Resize event handler fired on every pixel without debounce — added 100ms debounce
- **[Bug]** Waveform canvas initialised before fonts/layout rendered (possible zero-rect) — deferred init to `requestAnimationFrame`
- **[UX]** `language` was hardcoded to `'de'` — now inferred from `navigator.language` with `'de'` fallback
- **[Bug]** Marker span text sliced from `s.start` instead of `safeStart` after overlap guard — rendered duplicate text for overlapping markers
- **[Bug]** Concurrent analysis requests created race condition (markers from request A mixed with narratives from request B) — added `AbortController` with abort-on-resubmit
- **[Perf]** `requestAnimationFrame` handle not tracked — added `wRafId` + `cancelAnimationFrame` on `beforeunload`
- **[Security]** FastAPI `/resonanzraum` route lacked `try/except` — added `FileNotFoundError` + generic `Exception` handlers
- **[UX]** No minimum input length check — added 5-character guard with status message
- **[A11y]** Canvas missing `aria-label` and `role="img"` — added for screen reader support
- **[Bug]** `narrativeTypeInfo` used fragile prefix matching — now uses exact match first, then full substring fallback

---

## [6.0.0-alpha] — 2026-04-04

### SDLC Infrastructure
- Complete SDLC scaffold: `1-spec/`, `2-design/`, `3-code/`, `4-deploy/`, `decisions/`
- 8 SDLC skills (init, elicit, design, decompose, implementation-plan, execute-next-task, fix, status)
- Global `CLAUDE.md` + phase-specific `CLAUDE.spec.md`, `CLAUDE.design.md`, `CLAUDE.code.md`, `CLAUDE.deploy.md`

### Specification (Phase 1)
- 5 Goals: semantic-meaning-disclosure, professional-diagnostic-support, real-time-live-analysis, autonomous-marker-evolution, multi-channel-deployment
- 4 User Stories: post-analysis-interpretation, professional-bias-checking, autonomous-marker-enrichment, api-integration
- 6 Core Requirements: REQ-F-semantic-framing, REQ-F-marker-resonance-weighting, REQ-F-multi-narrative-analysis, REQ-USA-interactive-visualization, REQ-PERF-conversation-latency, REQ-F-candidate-detection
- 1 Assumption (ASM-ki-semantic-framing-sufficient), 1 Constraint (CON-no-compose-of-rules)
- 5 Stakeholders: api-consumer, researcher, maintainer, product-owner, infrastructure

### Architecture (Phase 2)
- 3 new processing layers documented: Semantic Framing, Frame Resonance Weighting, Multi-Narrative Interpretation
- Latency budget: p95 ≤ 500ms via parallel Framing (250ms) ∥ ATO Detection (50ms) + sequential Weighting (50ms) + Narrative Gen (150ms)
- Full caching strategy (dialogue-level, 24h TTL)
- Provider fallback: Gemini → OpenRouter → explicit error (no embedding fallback)
- `narrative_count = 3 + floor(offline_context_risk × 2)` — context uncertainty drives interpretive variance
- 3 Decision records: semantic-guided-multi-perspective-architecture, context-uncertainty-proportional-variance, no-compose-of-rules

### Planning (Phase 3 prep)
- `3-code/tasks.md`: P0/P1/P2 phased task breakdown with critical gates
- `STARTUP_CHECKLIST.md`: 8-week week-by-week plan
- 8 LLM prompt templates (`1-spec/prompts/gemini-templates.md`)
- Gold Standard Annotation Guide for Week 1 assumption validation
- ASM Validation Report Template
- `tests/conftest.py`: 19 pytest fixtures
- `scripts/init.sh`: one-command environment setup
- `requirements.txt`, `.env.example`, `DEVELOPER_QUICKSTART.md`
