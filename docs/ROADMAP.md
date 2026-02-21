# LeanDeep Annotator — Product Roadmap

> Last updated: 2026-02-21
> Status: Active development, Pre-launch

## Vision

Deterministischer Annotations-Layer für menschliche Kommunikation. Kein LLM nötig für die Kernanalyse — 850+ Marker erkennen psychologische Muster, Emotionsdynamiken und Beziehungsgesundheit in Echtzeit (~1ms/Nachricht). Das System liefert harte Signale, die entweder standalone oder als Input für LLM-gestützte Interpretation dienen.

**Zwei Tiers:**
- **Base** (stateless): Einzeltext- und Konversationsanalyse, VAD-Trajektorien, UED-Metriken, Prosody-Emotionserkennung
- **Pro** (persistent): Persona-Profile mit EWMA-Warm-Start, Episode-Tracking, Shift-Prädiktionen über Sessions hinweg

---

## Current State (v5.1-LD5)

| Dimension | Status | Metric |
|-----------|--------|--------|
| Markers total | 849 | 714 Rating-1, 125 Rating-2 |
| VAD-Coverage | 72% | 618/849 mit vad_estimate + effect_on_state |
| ATO Detection | Solid | 0.905 avg confidence, 251 unique feuern |
| SEM Detection | Schwach | Nur 27/238 feuern (11.3%), 96.6% patternlos |
| CLU Detection | Fast tot | 30 Detections auf 99K Nachrichten, 40.5% broken refs |
| MEMA Detection | MVP | detect_class heuristisch, kein stateful tracking |
| Persona System | Neu | CRUD + warm-start + episodes + predictions |
| Prosody | Stabil | 6 Emotionen, 17 Features, 20K+ Trainingsdaten |
| Gold-Corpus | 99K msgs | 1543 Chunks, 6 Jahre WhatsApp, DE-fokussiert |
| Tests | 72 pass | API, dynamics, VAD, personas, engine |
| Englisch | Untested | 620 msgs im Corpus, Patterns DE-lastig |

---

## Initiatives — Priorisiert nach Kundenwert

### P0 — Kritisch (SEM/CLU-Layer reparieren)

Ohne funktionierenden SEM/CLU-Layer ist das System ein glorifizierter Regex-Matcher. Die 4-Layer-Hierarchie ist das Alleinstellungsmerkmal — aktuell arbeiten nur 2 von 4 Layern zuverlässig.

#### P0-1: SEM-Layer Reanimation
**Impact:** Hoch — verdreifacht die Analysetiefe
**Aufwand:** Mittel (2-3 Tage)

> *Spec: [SPEC-P0-1]*

#### P0-2: CLU Reference Repair
**Impact:** Hoch — aktiviert Cluster-Erkennung (Eskalationsmuster, Grief-Cluster)
**Aufwand:** Mittel (1-2 Tage)

> *Spec: [SPEC-P0-2]*

#### P0-3: Dead Marker Cleanup
**Impact:** Mittel — reduziert Rauschen, beschleunigt Engine
**Aufwand:** Klein (halber Tag)

> *Spec: [SPEC-P0-3]*

---

### P1 — Hoch (Nutzer-facing Features)

#### P1-1: Persona Dashboard UI
**Impact:** Sehr hoch — macht Pro-Tier greifbar
**Aufwand:** Mittel (2-3 Tage)

> *Spec: [SPEC-P1-1]*

#### P1-2: Annotator-as-a-Service API Hardening
**Impact:** Hoch — Voraussetzung für externen Zugang
**Aufwand:** Mittel (1-2 Tage)

> *Spec: [SPEC-P1-2]*

#### P1-3: LLM-Bridge Endpoint
**Impact:** Hoch — ermöglicht "Marker + LLM"-Workflow
**Aufwand:** Klein-Mittel (1-2 Tage)

> *Spec: [SPEC-P1-3]*

#### P1-4: Monetarisierung — Freemium API + Tiered Pricing
**Impact:** Sehr hoch — Revenue-Grundlage
**Aufwand:** Mittel (2-3 Tage)

> *Spec: [SPEC-P1-4]*

---

### P2 — Mittel (Qualität & Abdeckung)

#### P2-1: Englisch-Expansion
**Impact:** Mittel-Hoch — öffnet internationalen Markt
**Aufwand:** Groß (5+ Tage)

> *Spec: [SPEC-P2-1]*

#### P2-2: Marker-Beschreibungen vervollständigen
**Impact:** Mittel — verbessert API-Dokumentation und LLM-Bridge-Qualität
**Aufwand:** Mittel (2-3 Tage)

> *Spec: [SPEC-P2-2]*

#### P2-3: MEMA Stateful Upgrade
**Impact:** Mittel — macht Organismus-Diagnose produktionsreif
**Aufwand:** Groß (3-5 Tage)

> *Spec: [SPEC-P2-3]*

---

### P3 — Nice-to-have

#### P3-1: Eval-Pipeline CI/CD
**Impact:** Niedrig-Mittel — automatisierte Qualitätssicherung
**Aufwand:** Klein (1 Tag)

> *Spec: [SPEC-P3-1]*

#### P3-2: Deployment (Vercel/Fly.io)
**Impact:** Mittel — macht API öffentlich erreichbar
**Aufwand:** Klein (halber Tag)

> *Spec: [SPEC-P3-2]*

#### P3-3: WebSocket Streaming für Echtzeit-Analyse
**Impact:** Niedrig — Feature für Live-Chat-Integration
**Aufwand:** Mittel (2 Tage)

> *Spec: [SPEC-P3-3]*

#### P3-4: Skyll + MCP Distribution
**Impact:** Mittel — macht LeanDeep für jeden AI-Agent entdeckbar
**Aufwand:** Klein (halber Tag)

> *Spec: [SPEC-P3-4]*

---

## Initiative Specifications

---

### SPEC-P0-1: SEM-Layer Reanimation

**Problem:**
96.6% der SEM-Marker (230/238) haben keine eigenen Regex-Patterns und verlassen sich ausschließlich auf `composed_of` ATO-Referenzen. Viele dieser Referenzen zeigen auf ATO-IDs die nicht existieren oder nie feuern. Ergebnis: Nur 27 von 238 SEMs detektieren überhaupt.

9 SEMs sind vollständig verwaist — weder Patterns noch composed_of.

**Ziel:**
≥ 120 SEMs feuern auf dem Gold-Corpus (5x Steigerung).

**Schritte:**

1. **Audit composed_of-Chains** (Tool: `tools/audit_sem_chains.py` — NEU)
   - Für jeden SEM: prüfe ob alle composed_of ATO-Refs im Registry existieren
   - Für jeden SEM: prüfe ob die referenzierten ATOs auf dem Gold-Corpus feuern
   - Output: `docs/sem_audit.json` mit Status pro SEM (alive/broken_ref/dead_ato/orphan)

2. **Fix broken ATO-Referenzen** (Tool: `tools/fix_sem_refs.py` — NEU)
   - Fuzzy-Mapping: `SEM_ANGER_ESCALATION` → `composed_of: [ATO_ANGER_WORD, ATO_ESCALATION_PHRASE]`
   - Strategie: SEM-ID-Keywords → passende existierende ATOs matchen
   - Review-Output: CSV mit Vorschlägen, manuelles Approval

3. **Eigene Patterns für Top-50 SEMs** (manuell + Tool-unterstützt)
   - Die 50 SEMs mit höchstem erwartetem Impact (basierend auf Family, CLU-Abhängigkeiten) bekommen eigene Regex-Patterns
   - Tool `tools/discover_patterns.py` nutzen für Bigram/Collocation-Discovery
   - Patterns in source YAML (`build/markers_rated/`) eintragen

4. **Orphan-Cleanup**
   - 9 verwaiste SEMs: entweder mit Patterns bestücken oder als Rating-4 markieren und aus Registry entfernen

**Erfolgskriterium:**
```bash
python3 tools/eval_corpus.py  # SEM unique_markers >= 120 (aktuell: 27)
```

**Dateien:**
- NEU: `tools/audit_sem_chains.py`
- NEU: `tools/fix_sem_refs.py`
- EDIT: `build/markers_rated/1_approved/SEM/*.yaml` (Pattern-Ergänzungen)
- EDIT: `build/markers_normalized/SEM/*.yaml` (nach Normalize-Run)

---

### SPEC-P0-2: CLU Reference Repair

**Problem:**
49/121 CLU-Marker (40.5%) referenzieren SEM-IDs die nicht existieren. 77 einzigartige broken Refs. Einige CLUs haben malformed composed_of (JSON-Dicts statt Strings). Der CLU-Layer produziert nur 30 Detections auf 99K Nachrichten — praktisch inaktiv.

**Ziel:**
- 0 broken Refs
- ≥ 50 CLUs feuern auf dem Gold-Corpus

**Schritte:**

1. **Systematic Ref-Audit** (Tool: `tools/fix_clu_refs.py` — existiert, erweitern)
   - Bestehenden Fuzzy-Matcher verbessern: semantische Äquivalenz-Tabelle
   - Malformed dict-Refs (`{'marker_ids': [...]}`) → Strings normalisieren
   - Output: Mapping-Tabelle broken_ref → resolved_ref (oder "UNRESOLVABLE")

2. **SEM-ID Alignment** — hängt von P0-1 ab
   - Sobald SEM-Layer reanimiert: CLU-Refs gegen die neuen/fixierten SEM-IDs abgleichen
   - Automatisches Re-Mapping wo eindeutig

3. **Window-Parameter tunen**
   - Default `window.messages: 10` ist für kurze Chats zu eng
   - Für WhatsApp-Konversationen: `window.messages: 20` evaluieren
   - A/B-Eval auf Gold-Corpus

**Abhängigkeit:** P0-1 (SEM-Reanimation) sollte zuerst laufen.

**Erfolgskriterium:**
```bash
python3 tools/eval_corpus.py  # CLU unique_markers >= 50, 0 broken refs in audit
```

**Dateien:**
- EDIT: `tools/fix_clu_refs.py` (erweitern)
- EDIT: `build/markers_rated/*/CLU/*.yaml`
- EDIT: `build/markers_rated/*/MEMA/*.yaml` (gleiche Ref-Probleme)

---

### SPEC-P0-3: Dead Marker Cleanup

**Problem:**
- 7 Marker mit Layer "UNKNOWN" (ACT_*, EMO_* Prefixes)
- 9 verwaiste SEMs (weder Patterns noch composed_of)
- 92 Marker in 7 Families (SD, INTUITION, ABSENCE, CONFLICT, REPAIR, PERSONA, SELF) mit 0% Detection Rate
- Tote Marker verlangsamen Engine und erzeugen Noise in der API-Ausgabe

**Ziel:**
Jeder Marker im Registry feuert entweder oder ist explizit als `draft` getaggt.

**Schritte:**

1. **UNKNOWN-Layer reklassifizieren**
   - `ACT_*` → ATO (Verhaltensmarker) oder SEM (wenn komplex)
   - `EMO_*` → ATO (Emotionslexikon) mit `ATO_EMO_` Prefix
   - Oder entfernen wenn redundant

2. **Zero-Detection Marker triagen**
   - 92 Marker prüfen: Pattern-Problem (fixbar) oder konzeptionell tot?
   - Fixbare → Patterns ergänzen (Teil von P0-1)
   - Konzeptionell tote → Rating auf 4 setzen, aus 1_approved/2_good verschieben

3. **Registry-Rebuild**
   ```bash
   python3 tools/normalize_schema.py
   python3 -m pytest tests/ -x -q  # Keine Regression
   ```

**Dateien:**
- EDIT: `build/markers_rated/` (verschieben/löschen)
- EDIT: `tools/normalize_schema.py` (UNKNOWN-Layer handling)

---

### SPEC-P1-1: Persona Dashboard UI

**Problem:**
Das Persona-System (Pro Tier) hat 4 API-Endpoints aber kein UI. Nutzer können Personas nur via curl/Postman nutzen. Für Coaching/Therapie-Anwendungen braucht es eine visuelle Darstellung von Verlauf, Episoden und Prädiktionen.

**Ziel:**
Eine HTML-Seite `/persona` mit:
- Persona erstellen / auswählen
- Session-History mit VAD-Trajectory (Chart.js Line Chart)
- Episode-Timeline (farbcodiert: rot=Eskalation, grün=Repair, grau=Withdrawal, orange=Rupture, blau=Stabilization)
- State-Indices-Verlauf (Trust/Conflict/Deesc über Sessions)
- Prediction-Widget (Shift-Wahrscheinlichkeiten als Donut-Chart)
- Konversation analysieren mit gewählter Persona

**Schritte:**

1. **HTML/JS Page** (`api/static/persona.html`)
   - Dark Theme konsistent mit bestehenden UIs (#1a1a2e bg, #e94560 accent)
   - Chart.js für VAD-Trajectory + State-Indices (2 Charts)
   - Episode-Timeline als horizontale Bar mit Tooltips
   - Persona-Selector Dropdown + "New Persona" Button
   - Textarea für Konversations-Input (gleich wie Playground)

2. **Route** in `api/main.py`
   ```python
   @app.get("/persona", response_class=HTMLResponse)
   ```

3. **API-Calls vom Frontend:**
   - `POST /v1/personas` → Persona erstellen
   - `POST /v1/analyze/dynamics` mit `persona_token` → Analysieren + akkumulieren
   - `GET /v1/personas/{token}` → Profil laden für Dashboard
   - `GET /v1/personas/{token}/predict` → Prädiktionen anzeigen

**Abhängigkeit:** Keine (Persona-API existiert bereits).

**Dateien:**
- NEU: `api/static/persona.html`
- EDIT: `api/main.py` (1 Route)

---

### SPEC-P1-2: API Hardening für Produktion

**Problem:**
Die API ist aktuell ein Dev-Server: Auth deaktiviert, kein HTTPS, keine Input-Validierung über Pydantic hinaus, keine Dokumentation der Fehler-Codes, keine API-Versionierung-Strategie.

**Ziel:**
Produktionsreife API die extern genutzt werden kann.

**Schritte:**

1. **Auth-System aktivieren**
   - `LEANDEEP_REQUIRE_AUTH=true` als Prod-Default
   - API-Key-Management: Create/Revoke via Admin-Endpoint oder CLI-Tool
   - Rate-Limiting pro Key (bereits implementiert, testen)

2. **Input Sanitization**
   - Max-Text-Length Enforcement (50K chars — bereits in Pydantic, in Engine doppelt prüfen)
   - Persona-Token: UUID-Validierung (bereits implementiert)
   - Injection-Schutz: Regex-Patterns nicht aus User-Input bauen (aktuell safe, dokumentieren)

3. **Error Response Schema**
   - Standardisiertes Error-Format: `{"error": {"code": "...", "message": "...", "detail": ...}}`
   - Dokumentierte HTTP-Status-Codes pro Endpoint
   - 429 Rate-Limit mit Retry-After Header

4. **OpenAPI-Dokumentation**
   - Endpoint-Beschreibungen vervollständigen (aktuell teilweise leer)
   - Request/Response-Examples in OpenAPI-Schema
   - `/docs` und `/redoc` aktiviert lassen

5. **CORS konfigurieren**
   - `allow_origins=["*"]` → konfigurierbar via Env-Variable
   - Für Prod: explizite Origin-Liste

**Dateien:**
- EDIT: `api/main.py` (Error handling, CORS)
- EDIT: `api/auth.py` (Key management)
- EDIT: `api/config.py` (Prod-Defaults)
- EDIT: `api/models.py` (Error-Schema)

---

### SPEC-P1-3: LLM-Bridge Endpoint

**Problem:**
Die Marker liefern harte Signale (welche Patterns erkannt, VAD-Werte, State-Indices). Aber die **Interpretation** — was bedeutet das für diese Beziehung, was ist der nächste Schritt — braucht kontextuelle Intelligenz. LLMs sind dafür ideal, aber ohne strukturierten Marker-Kontext halluzinieren sie.

**Ziel:**
Ein Endpoint der Marker-Annotationen als strukturierten Kontext für einen LLM-Prompt aufbereitet.

**Schritte:**

1. **Endpoint** `POST /v1/analyze/interpret`
   - Input: `ConversationRequest` + `model: str` (optional, für Routing)
   - Intern: ruft `analyze_conversation()` auf
   - Output: Strukturierter Kontext-Block (Markdown oder JSON) der direkt als LLM-System-Prompt oder User-Kontext nutzbar ist

2. **Kontext-Template:**
   ```markdown
   ## Marker Analysis Context

   **Conversation:** {n} messages between {speakers}
   **Emotional State:** Valence {v}, Arousal {a} (home base)
   **State Indices:** Trust {trust}, Conflict {conflict}, De-escalation {deesc}

   ### Detected Patterns
   - {marker_id}: {description} (confidence {conf}, messages {indices})
   ...

   ### Temporal Dynamics
   - {trend}: {marker_id} {direction} over conversation

   ### Speaker Baselines
   - {speaker}: baseline valence {v}, {shift_count} shifts detected

   ### Episode Indicators
   - {episode_type}: {duration} messages, VAD delta {delta}
   ```

3. **Optionaler LLM-Call** (wenn API-Key konfiguriert)
   - `LEANDEEP_LLM_PROVIDER=anthropic|openai|none`
   - Wenn `none`: gibt nur den Kontext-Block zurück (Nutzer ruft LLM selbst)
   - Wenn Provider konfiguriert: sendet Kontext + Conversation an LLM, gibt Interpretation zurück

**Dateien:**
- EDIT: `api/main.py` (1 neuer Endpoint)
- NEU: `api/interpret.py` (Kontext-Template-Builder)
- EDIT: `api/config.py` (LLM-Provider Settings)
- EDIT: `api/models.py` (InterpretRequest/Response)

---

### SPEC-P2-1: Englisch-Expansion

**Problem:**
98.7% des Gold-Corpus ist Deutsch. Die meisten Regex-Patterns sind DE-spezifisch (Compound-Words, Modalpartikeln). Englische Texte werden nur von den wenigen bilingualen Patterns erkannt. ATO_DEPRESSION_SELF_FOCUS matcht "me"/"I" — viel zu breit für Englisch.

**Ziel:**
≥ 200 ATO-Patterns mit englischen Varianten. Separater EN-Eval-Corpus.

**Schritte:**

1. **Pattern-Audit: DE-only vs. bilingual**
   - Alle 936 kompilierten Patterns klassifizieren: DE-only / EN-only / bilingual
   - Tool: `tools/audit_language_coverage.py` (NEU)

2. **EN-Patterns für Top-100 ATOs**
   - Die 100 meistfeuernden ATOs: englische Regex-Varianten erstellen
   - Word-Boundaries (`\b`) für englische Wörter (keine Compound-Words)
   - Vorsicht: "I"/"me" Pronomen nicht als Marker-Trigger (zu breit)

3. **EN-Eval-Corpus**
   - Mindestens 5K englische Nachrichten (Quelle: öffentliche Conversation-Datasets)
   - Oder: synthetisch via LLM-Translation des DE-Corpus (mit manueller Stichprobe)

4. **ATO_DEPRESSION_SELF_FOCUS Fix**
   - DE: Pattern beibehalten (funktioniert)
   - EN: Restriktivere Patterns (`I feel worthless`, `I can't do anything right`, nicht `I`/`me` standalone)

**Dateien:**
- NEU: `tools/audit_language_coverage.py`
- EDIT: `build/markers_rated/*/ATO/*.yaml` (EN-Patterns)
- NEU: `eval/gold_corpus_en.jsonl`

---

### SPEC-P2-2: Marker-Beschreibungen vervollständigen

**Problem:**
Nur 30% der Marker (255/849) haben Beschreibungen >20 Zeichen. Für die API-Dokumentation, den LLM-Bridge-Endpoint (P1-3), und das Nutzer-Verständnis sind gute Beschreibungen essentiell.

**Ziel:**
100% der Rating-1 Marker haben Beschreibungen ≥50 Zeichen.

**Schritte:**

1. **Tool: Batch-Description-Generator** (`tools/enrich_descriptions.py` — NEU)
   - Input: Marker-YAML mit ID, frame, tags, patterns, examples
   - Output: 1-2 Satz Beschreibung basierend auf Frame-Semantik
   - Logik: Frame-Felder (signal, concept, pragmatics, narrative) → Template-basierte Description
   - Fallback: ID-Parsing (`ATO_BLAME_SHIFT` → "Detects linguistic patterns associated with blame-shifting behavior")

2. **Review-Pass**
   - Generierte Beschreibungen als PR, manuelles Review der Top-100

**Dateien:**
- NEU: `tools/enrich_descriptions.py`
- EDIT: `build/markers_rated/*/ATO/*.yaml`, `*/SEM/*.yaml` etc.

---

### SPEC-P2-3: MEMA Stateful Upgrade

**Problem:**
MEMA detect_class ist aktuell ein stateless Keyword-Matcher. Echte Meta-Diagnose braucht Session-State: "Kommunikationsmuster X hat sich über 3 Sessions verschlechtert" statt "Keyword Y ist in diesem Gespräch aktiv".

**Ziel:**
MEMA-Layer nutzt Persona-Daten (wenn verfügbar) für longitudinale Diagnose.

**Schritte:**

1. **Persona-aware MEMA Detection**
   - `engine.detect_mema()` bekommt optionalen Persona-Kontext
   - detect_class `trend_analysis`: prüft `state_trajectory` über Sessions
   - detect_class `cycle_detection`: prüft `episodes` auf wiederkehrende Muster
   - detect_class `absence_meta`: prüft ob historisch vorhandene positive Marker verschwunden sind

2. **Neue detect_classes**
   - `longitudinal_regression`: State-Index verschlechtert sich über ≥3 Sessions
   - `pattern_consolidation`: Gleiche Episode-Typen häufen sich
   - `baseline_shift`: Speaker-EWMA hat sich signifikant verschoben vs. erste Session

**Abhängigkeit:** Persona-System (bereits implementiert).

**Dateien:**
- EDIT: `api/engine.py` (detect_mema erweitern)
- EDIT: `api/main.py` (Persona-Kontext durchreichen)

---

### SPEC-P3-1: Eval-Pipeline CI/CD

**Ziel:**
Automatische Qualitätsprüfung bei jedem Push.

**Schritte:**

1. **GitHub Action** (`.github/workflows/eval.yml`)
   ```yaml
   on: push
   jobs:
     test:
       - pytest tests/ -x -q
     eval:
       - python3 tools/eval_corpus.py --threshold 0.3 --quick
       - Assert: ATO unique_markers >= 250
       - Assert: SEM unique_markers >= 27  # Erhöhen nach P0-1
       - Assert: avg_confidence ATO >= 0.85
   ```

2. **Eval-Badge** im README

**Dateien:**
- NEU: `.github/workflows/eval.yml`
- NEU: `README.md` (mit Badges)

---

### SPEC-P3-2: Deployment

**Ziel:**
API öffentlich erreichbar auf eigener Domain.

**Optionen:**
- **Fly.io** (empfohlen): Docker-Container, $5/Monat, auto-scaling
- **Vercel**: Serverless, cold-start-Probleme bei großem Registry-Load
- **VPS** (srv1308064.hstgr.cloud): Bereits vorhanden, aber überlastet

**Schritte:**

1. **Dockerfile**
   ```dockerfile
   FROM python:3.12-slim
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY api/ api/
   COPY build/markers_normalized/ build/markers_normalized/
   COPY personas/ personas/
   CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8420"]
   ```

2. **Env-Konfiguration**
   - `LEANDEEP_REQUIRE_AUTH=true`
   - `LEANDEEP_PERSONAS_DIR=/data/personas` (persistentes Volume)

**Dateien:**
- NEU: `Dockerfile`
- NEU: `fly.toml` oder `vercel.json`

---

### SPEC-P3-3: WebSocket Streaming

**Ziel:**
Echtzeit-Analyse für Live-Chat-Integration (z.B. Therapie-Tool das während der Sitzung annotiert).

**Schritte:**

1. **WebSocket Endpoint** (`/ws/analyze`)
   - Client sendet Nachrichten einzeln
   - Server antwortet mit inkrementellen Detections + VAD-Updates
   - Persona-Token optional für Session-Tracking

2. **Inkrementelle Engine**
   - ATO/SEM: per-message (bereits möglich)
   - CLU: sliding window über letzte N Nachrichten
   - State-Indices: akkumulierend

**Dateien:**
- EDIT: `api/main.py` (WebSocket Route)
- NEU: `api/streaming.py` (inkrementelle Analyse-Logik)

---

### SPEC-P1-4: Monetarisierung — Freemium API + Tiered Pricing

**Problem:**
LeanDeep hat einen funktionierenden Annotator mit 850+ Markern, VAD-Tracking, Persona-System und Prosody-Erkennung — aber kein Revenue-Modell. Die Engine ist zu wertvoll für rein Open-Source und zu komplex für einfaches SaaS-Pricing.

**Monetarisierungsstrategie: 3-Tier Freemium**

#### Tier 1: Free (Developer / Trial)
- **Rate Limit:** 100 Requests/Tag
- **Endpoints:** `/v1/analyze` (Einzeltext), `/v1/markers` (Read-only)
- **Features:** ATO-Layer only, keine VAD, keine Dynamics
- **Auth:** API-Key (self-service via Landing Page)
- **Zweck:** Entwickler testen, Integrationen bauen, Lock-in erzeugen

#### Tier 2: Base ($29/Monat oder $290/Jahr)
- **Rate Limit:** 10.000 Requests/Tag
- **Endpoints:** Alle stateless Endpoints (analyze, conversation, dynamics, markers)
- **Features:** Alle 4 Layer, VAD-Tracking, UED-Metriken, Prosody, State-Indices
- **Kein:** Persona-System, Predictions, WebSocket
- **Zielgruppe:** Indie-Entwickler, kleine Apps, Dating-App-Integrationen

#### Tier 3: Pro ($99/Monat oder $990/Jahr)
- **Rate Limit:** 100.000 Requests/Tag
- **Endpoints:** Alles inkl. Personas, Predictions, LLM-Bridge, WebSocket (wenn verfügbar)
- **Features:** Persona-Profiles, EWMA Warm-Start, Episode-Tracking, Shift-Predictions, Priority Support
- **Zielgruppe:** Therapie-Plattformen, Coaching-Tools, Forschung, Enterprise

#### Revenue-Projektion (konservativ)

| Monat | Free | Base | Pro | MRR |
|-------|------|------|-----|-----|
| M1 | 50 | 5 | 1 | $244 |
| M3 | 200 | 15 | 3 | $732 |
| M6 | 500 | 40 | 10 | $2,150 |
| M12 | 1000 | 100 | 30 | $5,870 |

Konversion: Free→Base ~3%, Base→Pro ~10% (Branchenstandard für Developer-Tools).

#### Implementierung

1. **Stripe-Integration** (`api/billing.py` — NEU)
   - Stripe Checkout Sessions für Subscription-Start
   - Webhook für `invoice.paid`, `customer.subscription.deleted`
   - API-Key ↔ Stripe Customer ID Mapping
   - Kein eigenes Payment-UI — Stripe Hosted Checkout

2. **Tier-basiertes Rate-Limiting** (`api/auth.py` — erweitern)
   - API-Key hat Tier-Attribut (free/base/pro)
   - Rate-Limit pro Key: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
   - Endpoint-Gating: Free-Keys bekommen 403 auf `/v1/analyze/dynamics`
   ```python
   TIER_LIMITS = {
       "free":  {"daily": 100,    "endpoints": ["analyze", "markers", "health"]},
       "base":  {"daily": 10000,  "endpoints": ["analyze", "conversation", "dynamics", "markers", "health"]},
       "pro":   {"daily": 100000, "endpoints": ["*"]},
   }
   ```

3. **Self-Service Key Management** (`api/static/signup.html` — NEU)
   - E-Mail + Stripe Checkout → API-Key per Mail
   - Dashboard: Usage-Stats, Tier-Upgrade, Key-Rotation
   - Kein eigenes User-System — Stripe Customer Portal für Billing

4. **Landing Page** (statisch, `/` Route)
   - Pricing-Tabelle (3 Tiers)
   - Live-Demo (Free-Tier Playground)
   - API-Dokumentation Link
   - "Get API Key" → Stripe Checkout

5. **Usage-Tracking** (`api/usage.py` — NEU)
   - Request-Counter pro API-Key (in-memory + periodic flush to SQLite/JSON)
   - Daily Reset um Mitternacht UTC
   - Usage-Stats Endpoint: `GET /v1/usage` (authenticated)

**Zusätzliche Revenue-Streams:**

- **Corpus-as-a-Service:** Anonymisierte Gold-Corpus-Statistiken als Benchmark-Dataset ($499 einmalig)
- **Custom Marker Packs:** Branchenspezifische Marker (Dating-Safety, HR-Screening, Therapie) als Add-ons ($49/Pack)
- **White-Label API:** Für Plattformen die LeanDeep unter eigenem Branding einbetten (Enterprise, Preis auf Anfrage)

**Abhängigkeiten:**
- P1-2 (API Hardening) muss zuerst laufen (Auth, Rate-Limiting, Error-Schema)
- P3-2 (Deployment) muss parallel laufen (API muss öffentlich erreichbar sein)

**Erfolgskriterium:**
- Woche 1: Stripe-Integration live, 3 Tiers funktional
- Monat 1: ≥50 Free-Keys, ≥5 Base-Subscriptions
- Monat 3: $500+ MRR

**Dateien:**
- NEU: `api/billing.py` (Stripe-Integration)
- NEU: `api/usage.py` (Usage-Tracking)
- NEU: `api/static/signup.html` (Self-Service Key Management)
- NEU: `api/static/landing.html` (Pricing + Demo)
- EDIT: `api/auth.py` (Tier-basiertes Gating)
- EDIT: `api/config.py` (Stripe Keys, Tier-Limits)
- EDIT: `api/main.py` (Usage-Middleware, Landing-Route)
- EDIT: `requirements.txt` (+stripe)

---

### SPEC-P3-4: Skyll + MCP Distribution

**Problem:**
LeanDeep ist nur nutzbar wenn Entwickler aktiv davon erfahren und die API manuell integrieren. Im AI-Agent-Ökosystem entdecken Agents Skills zur Laufzeit — über Plattformen wie Skyll (REST API + MCP für Skill-Discovery) und skills.sh.

**Ziel:**
Jeder AI-Agent (Claude Code, Cursor, custom agents) kann LeanDeep per `search_skills("conversation analysis")` finden und sofort nutzen. Zwei Distributionswege:

#### Weg 1: SKILL.md für Skyll/skills.sh Registry

Eine `SKILL.md` die Agents erklärt wie sie die LeanDeep API nutzen:

```markdown
---
name: LeanDeep Annotator
description: Detect psychological patterns in conversations with VAD emotion tracking
version: 5.1
tools: [Bash, WebFetch]
---

# LeanDeep Conversation Annotator

Analyze text for 850+ psychological/communication markers across 4 layers...

## Usage
curl -X POST https://api.leandeep.app/v1/analyze \
  -H "Authorization: Bearer $LEANDEEP_API_KEY" \
  -d '{"text": "Du hörst mir nie zu!"}'
```

Registrierung:
1. `SKILL.md` im LeanDeep-annotator Repo erstellen
2. PR an `assafelovic/skyll` → `registry/SKILLS.md` Eintrag
3. Automatisch über `api.skyll.app/search?q=conversation+analysis` auffindbar

#### Weg 2: LeanDeep als MCP-Server

Nativer MCP-Server der direkt in Claude Desktop / Cursor / any MCP-Client eingebunden wird:

```json
{
  "mcpServers": {
    "leandeep": {
      "url": "https://api.leandeep.app/mcp"
    }
  }
}
```

MCP-Tools:
- `analyze_text` — Einzeltext-Analyse
- `analyze_conversation` — Multi-Message mit VAD + State
- `create_persona` — Persona erstellen (Pro)
- `get_persona_prediction` — Shift-Prädiktionen (Pro)

Implementierung: FastMCP Wrapper um bestehende FastAPI-Endpoints.

**Monetarisierung über Distribution:**
- Skyll/skills.sh = kostenlose Entdeckung → treibt Traffic zur API
- Free-Tier-Key = Einstieg → Konversion zu Base/Pro
- MCP = nahtlose Integration → höhere Retention (Agent nutzt API automatisch)
- Jeder MCP-Call = API-Request = zählt gegen Rate-Limit = Revenue

**Aufwand:**
- SKILL.md + Registry-PR: 2 Stunden
- MCP-Server (FastMCP Wrapper): 4 Stunden

**Abhängigkeiten:**
- P3-2 (Deployment) — API muss öffentlich erreichbar sein
- P1-4 (Monetarisierung) — API-Keys müssen funktionieren

**Dateien:**
- NEU: `SKILL.md` (Agent-Skill-Definition)
- NEU: `mcp_server.py` (FastMCP Wrapper)
- EDIT: `requirements.txt` (+fastmcp)
