# Resonanzraum GUI Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a visually distinctive single-page analysis interface (`/resonanzraum`) with acoustic/resonance aesthetic — 3-column layout: Equalizer (SemanticFrame) | Annotated Dialogue | Narrative Overtones — wired to the existing `/v1/analyze/conversation` API and designed to extend cleanly for LeanDeep 6.0's new frame/narrative endpoints.

**Architecture:** Single self-contained HTML file at `api/static/resonanzraum.html`, served by a new FastAPI route at `/resonanzraum`. All styling and JS is inline. First built with mock data (Tasks 1–8), then wired to the real API (Task 9). No build tool, no framework — pure HTML/CSS/JS.

**Tech Stack:** HTML5, CSS custom properties, vanilla JS (async/await), SVG, Google Fonts (Cormorant Garamond + DM Mono), existing FastAPI route pattern from `api/main.py:893`.

**Visual Identity:**
```
Colors:   #0D0D14 bg | #E8B44B amber | #7ECFED cyan | #F0EEE8 pearl
Fonts:    Cormorant Garamond (display) + DM Mono (data)
Layers:   ATO=amber | SEM=cyan | CLU=#FF7A7A coral | MEMA=#B4A0FF lavender
```

---

## Task 1: Register `/resonanzraum` Route

**Files:**
- Modify: `api/main.py` — insert after line ~906 (after `/playground` route)

**Step 1: Add the route**

Open `api/main.py` and insert after the existing `@app.get("/playground")` block:

```python
@app.get("/resonanzraum", response_class=HTMLResponse)
async def resonanzraum():
    """Serve the Resonanzraum analysis interface."""
    html_path = Path(__file__).parent / "static" / "resonanzraum.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>resonanzraum.html not found</h1>", status_code=404)
```

**Step 2: Create the empty HTML file**

Create `api/static/resonanzraum.html`:

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeanDeep – Resonanzraum</title>
</head>
<body>
  <h1 style="color:white;background:#0D0D14;padding:2rem;font-family:serif">
    Resonanzraum — Scaffold
  </h1>
</body>
</html>
```

**Step 3: Verify route works**

```bash
# Start server (if not running)
cd /Users/benjaminpoersch/Projects/LeanDeep6
source venv/bin/activate
python3 -m uvicorn api.main:app --port 8420 --reload &
sleep 2
curl -s http://localhost:8420/resonanzraum | grep -o "Resonanzraum"
# Expected: Resonanzraum
```

**Step 4: Commit**

```bash
git add api/main.py api/static/resonanzraum.html
git commit -m "feat(ui): add /resonanzraum route + empty scaffold"
```

---

## Task 2: CSS Foundation — Colors, Fonts, Layout Shell

**Files:**
- Modify: `api/static/resonanzraum.html` — replace body with full CSS foundation

**Step 1: Replace the entire file with the CSS foundation + empty 3-column shell**

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeanDeep – Resonanzraum</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* ── TOKENS ──────────────────────────────────────────── */
:root {
  --bg:          #0D0D14;
  --bg-panel:    #13131E;
  --bg-card:     #1A1A28;
  --bg-input:    #0F0F1A;
  --amber:       #E8B44B;
  --amber-dim:   rgba(232, 180, 75, 0.18);
  --amber-glow:  rgba(232, 180, 75, 0.06);
  --cyan:        #7ECFED;
  --cyan-dim:    rgba(126, 207, 237, 0.15);
  --pearl:       #F0EEE8;
  --pearl-mid:   rgba(240, 238, 232, 0.6);
  --pearl-dim:   rgba(240, 238, 232, 0.25);
  --coral:       #FF7A7A;
  --lavender:    #B4A0FF;
  --border:      rgba(240, 238, 232, 0.08);
  --border-lit:  rgba(232, 180, 75, 0.3);

  /* Marker layer colors */
  --ato:    #E8B44B;
  --sem:    #7ECFED;
  --clu:    #FF7A7A;
  --mema:   #B4A0FF;

  --font-display: 'Cormorant Garamond', Georgia, serif;
  --font-mono:    'DM Mono', 'Courier New', monospace;
  --radius:       6px;
  --radius-lg:    12px;
}

/* ── RESET ──────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--pearl);
  font-family: var(--font-display);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── GRAIN OVERLAY ──────────────────────────────────── */
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 128px;
  pointer-events: none;
  z-index: 999;
  opacity: 0.6;
}

/* ── HEADER ─────────────────────────────────────────── */
#header {
  height: 64px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 20px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.header-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--amber);
  white-space: nowrap;
  z-index: 1;
}

.header-subtitle {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--pearl-dim);
  letter-spacing: 0.08em;
  z-index: 1;
}

#waveform-canvas {
  flex: 1;
  height: 40px;
  opacity: 0.5;
}

.header-status {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--pearl-dim);
  text-align: right;
  white-space: nowrap;
  z-index: 1;
}

.status-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--pearl-dim);
  margin-right: 6px;
  transition: background 0.3s, box-shadow 0.3s;
}
.status-dot.active {
  background: #4ADE80;
  box-shadow: 0 0 8px #4ADE80;
}

/* ── MAIN 3-COLUMN GRID ─────────────────────────────── */
#main {
  display: grid;
  grid-template-columns: 270px 1fr 310px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* ── PANEL SHARED ────────────────────────────────────── */
.panel {
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel:last-child { border-right: none; }

.panel-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.panel-label {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--pearl-dim);
  margin-bottom: 2px;
}
.panel-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--pearl);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

/* Center panel has no bg override */
#panel-center {
  background: var(--bg);
  border-right: 1px solid var(--border);
}
</style>
</head>
<body>

<!-- HEADER -->
<header id="header">
  <div>
    <div class="header-title">Resonanzraum</div>
    <div class="header-subtitle">LeanDeep Semantic Analysis</div>
  </div>
  <canvas id="waveform-canvas"></canvas>
  <div class="header-status">
    <span class="status-dot" id="status-dot"></span>
    <span id="status-text">bereit</span>
  </div>
</header>

<!-- 3-COLUMN MAIN -->
<main id="main">
  <!-- LEFT: Equalizer / Frame -->
  <div class="panel" id="panel-left">
    <div class="panel-header">
      <div class="panel-label">Semantischer Rahmen</div>
      <div class="panel-title">Frame-Spektrum</div>
    </div>
    <div class="panel-body" id="frame-body">
      <!-- Task 3 fills this -->
      <p style="color:var(--pearl-dim);font-size:0.8rem">Analyse ausstehend...</p>
    </div>
  </div>

  <!-- CENTER: Dialogue -->
  <div class="panel" id="panel-center">
    <div class="panel-header">
      <div class="panel-label">Dialogtext</div>
      <div class="panel-title">Annotierter Verlauf</div>
    </div>
    <div class="panel-body" id="dialogue-body">
      <!-- Task 4 fills this -->
      <p style="color:var(--pearl-dim);font-size:0.85rem">Text eingeben und analysieren...</p>
    </div>
  </div>

  <!-- RIGHT: Narratives -->
  <div class="panel" id="panel-right">
    <div class="panel-header">
      <div class="panel-label">Interpretation</div>
      <div class="panel-title">Narrative Obertöne</div>
    </div>
    <div class="panel-body" id="narrative-body">
      <!-- Task 5 fills this -->
      <p style="color:var(--pearl-dim);font-size:0.85rem">Keine Analyse aktiv.</p>
    </div>
  </div>
</main>

<script>
// Placeholder — Tasks 3–9 add functionality here
console.log('Resonanzraum scaffold loaded');
</script>
</body>
</html>
```

**Step 2: Reload and verify layout**

```bash
open http://localhost:8420/resonanzraum
# Expected:
# - Dark background (#0D0D14)
# - "RESONANZRAUM" header in amber
# - 3 columns visible (270px | flex | 310px)
# - Grain texture overlay
# - "Analyse ausstehend..." placeholder texts
```

**Step 3: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): resonanzraum css foundation + 3-column layout shell"
```

---

## Task 3: Animated Waveform Header + Equalizer Panel

**Files:**
- Modify: `api/static/resonanzraum.html` — add `<script>` functions for waveform + equalizer

**Step 1: Add CSS for equalizer bars (inside `<style>`)**

Add to the existing CSS block:

```css
/* ── EQUALIZER ──────────────────────────────────────── */
.eq-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.eq-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.eq-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.eq-dimension {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pearl-dim);
}

.eq-value {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--amber);
}

.eq-track {
  height: 5px;
  background: rgba(240, 238, 232, 0.06);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.eq-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--amber);
  box-shadow: 0 0 8px rgba(232, 180, 75, 0.4);
}

.eq-bar.dim { background: var(--cyan); box-shadow: 0 0 8px rgba(126, 207, 237, 0.3); }
.eq-bar.risk { background: var(--coral); box-shadow: 0 0 8px rgba(255, 122, 122, 0.3); }

/* ── CONTEXT METERS ─────────────────────────────────── */
.meter-group {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.meter-title {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--pearl-mid);
  letter-spacing: 0.06em;
  margin-bottom: 14px;
  text-transform: uppercase;
}

.meter-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.meter-name {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--pearl-dim);
  width: 80px;
  flex-shrink: 0;
}

.meter-arc-wrap {
  flex: 1;
  height: 4px;
  background: rgba(240, 238, 232, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.meter-arc-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.meter-val {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--pearl-dim);
  width: 28px;
  text-align: right;
}
```

**Step 2: Add the JS waveform + equalizer functions (inside `<script>`)**

Replace the placeholder `<script>` block:

```javascript
/* ══════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════ */
const state = {
  frame: null,
  markers: [],
  narratives: [],
  activeNarrative: null,
  activeMarker: null,
  tenor: 0,          // emotional_tenor: -1..+1
  analysing: false,
};

/* ══════════════════════════════════════════════════════
   WAVEFORM HEADER
══════════════════════════════════════════════════════ */
const wCanvas = document.getElementById('waveform-canvas');
const wCtx = wCanvas.getContext('2d');
let wPhase = 0;

function resizeWaveform() {
  wCanvas.width = wCanvas.offsetWidth * devicePixelRatio;
  wCanvas.height = wCanvas.offsetHeight * devicePixelRatio;
  wCtx.scale(devicePixelRatio, devicePixelRatio);
}

function drawWaveform() {
  const W = wCanvas.offsetWidth, H = wCanvas.offsetHeight;
  wCtx.clearRect(0, 0, W, H);

  const tenor = state.tenor;            // -1..+1
  const amplitude = 8 + Math.abs(tenor) * 6;
  const baseY = H / 2;
  const freq = 0.025 + Math.abs(tenor) * 0.01;

  // gradient: amber (positive) ↔ cyan (negative)
  const t = (tenor + 1) / 2;           // 0..1
  const r = Math.round(126 + (232 - 126) * t);
  const g = Math.round(207 + (180 - 207) * t);
  const b = Math.round(237 + (75 - 237) * t);

  wCtx.beginPath();
  wCtx.strokeStyle = `rgba(${r},${g},${b}, 0.6)`;
  wCtx.lineWidth = 1.5;

  for (let x = 0; x < W; x++) {
    const y = baseY
      + Math.sin(x * freq + wPhase) * amplitude
      + Math.sin(x * freq * 1.7 + wPhase * 0.8) * (amplitude * 0.4);
    x === 0 ? wCtx.moveTo(x, y) : wCtx.lineTo(x, y);
  }
  wCtx.stroke();
  wPhase += state.analysing ? 0.06 : 0.015;
  requestAnimationFrame(drawWaveform);
}

window.addEventListener('resize', resizeWaveform);
resizeWaveform();
drawWaveform();

/* ══════════════════════════════════════════════════════
   EQUALIZER (SemanticFrame)
══════════════════════════════════════════════════════ */
const EQ_DIMS = [
  { key: 'tone',               label: 'Ton',       bar: '',    fmt: v => v || '—' },
  { key: 'intent',             label: 'Absicht',   bar: '',    fmt: v => v || '—' },
  { key: 'relational_dynamics',label: 'Dynamik',   bar: '',    fmt: v => v || '—' },
  { key: 'emotional_tenor',    label: 'Tenör',     bar: 'dim', fmt: v => typeof v === 'number' ? v.toFixed(2) : '—' },
  { key: 'themes',             label: 'Themen',    bar: 'dim', fmt: v => Array.isArray(v) ? v.slice(0,2).join(' · ') : '—' },
  { key: 'context_validity',   label: 'Kontext',   bar: 'dim', fmt: v => typeof v === 'number' ? (v * 100).toFixed(0) + '%' : '—' },
  { key: 'offline_context_risk',label: 'Ext. Risiko', bar: 'risk', fmt: v => typeof v === 'number' ? (v * 100).toFixed(0) + '%' : '—' },
];

function renderEqualizer(frame) {
  const body = document.getElementById('frame-body');
  body.innerHTML = '';

  const container = document.createElement('div');
  container.className = 'eq-container';

  EQ_DIMS.forEach(dim => {
    const val = frame ? frame[dim.key] : null;

    // Compute bar width (0–100%)
    let pct = 0;
    if (typeof val === 'number') {
      pct = Math.min(100, Math.max(0,
        dim.key === 'emotional_tenor' ? ((val + 1) / 2 * 100) : val * 100
      ));
    } else if (val) {
      pct = 60; // non-numeric: show 60%
    }

    const row = document.createElement('div');
    row.className = 'eq-row';
    row.innerHTML = `
      <div class="eq-label">
        <span class="eq-dimension">${dim.label}</span>
        <span class="eq-value">${dim.fmt(val)}</span>
      </div>
      <div class="eq-track">
        <div class="eq-bar ${dim.bar}" style="width:0%" data-target="${pct}"></div>
      </div>`;
    container.appendChild(row);
  });

  // Context meters block
  if (frame) {
    const meters = document.createElement('div');
    meters.className = 'meter-group';
    meters.innerHTML = `<div class="meter-title">Kontext-Metriken</div>`;

    const cv = frame.context_validity ?? 0;
    const ocr = frame.offline_context_risk ?? 0;

    [
      { name: 'Kontext-Validität', val: cv,  color: 'var(--cyan)' },
      { name: 'Ext. Risiko',       val: ocr, color: 'var(--coral)' },
    ].forEach(m => {
      const item = document.createElement('div');
      item.className = 'meter-item';
      item.innerHTML = `
        <span class="meter-name">${m.name}</span>
        <div class="meter-arc-wrap">
          <div class="meter-arc-fill" style="width:${m.val*100}%;background:${m.color}"></div>
        </div>
        <span class="meter-val">${(m.val*100).toFixed(0)}%</span>`;
      meters.appendChild(item);
    });

    container.appendChild(meters);
  }

  body.appendChild(container);

  // Animate bars in with stagger
  requestAnimationFrame(() => {
    body.querySelectorAll('.eq-bar').forEach((bar, i) => {
      setTimeout(() => {
        bar.style.width = bar.dataset.target + '%';
      }, i * 80);
    });
  });
}

// Initial render with no frame
renderEqualizer(null);
```

**Step 3: Verify equalizer appears**

```bash
open http://localhost:8420/resonanzraum
# Expected:
# - Header waveform animating slowly (soft amber/cyan wave)
# - Left panel: 7 eq-bars visible at 0% width
# - Run in browser console to test animation:
#   state.frame = { emotional_tenor: -0.35, context_validity: 0.75, offline_context_risk: 0.45, tone: 'zögernd', intent: 'explorativ', relational_dynamics: 'seeking-support', themes: ['Zweifel', 'Entscheidung'] };
#   renderEqualizer(state.frame);
# Expected: bars animate to their target widths with 80ms stagger
```

**Step 4: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): equalizer component + animated header waveform"
```

---

## Task 4: Annotated Dialogue Panel

**Files:**
- Modify: `api/static/resonanzraum.html`

**Step 1: Add dialogue CSS (inside `<style>`)**

```css
/* ── DIALOGUE PANEL ─────────────────────────────────── */
.dialogue-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.dialogue-textarea {
  width: 100%;
  min-height: 120px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--pearl-mid);
  font-family: var(--font-mono);
  font-size: 0.8rem;
  padding: 12px 14px;
  resize: vertical;
  line-height: 1.6;
  outline: none;
  transition: border-color 0.2s;
}
.dialogue-textarea:focus {
  border-color: var(--border-lit);
}
.dialogue-textarea::placeholder {
  color: var(--pearl-dim);
  font-style: italic;
}

.analyse-btn {
  align-self: flex-end;
  background: var(--amber-dim);
  border: 1px solid var(--amber);
  color: var(--amber);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 8px 20px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
}
.analyse-btn:hover {
  background: rgba(232, 180, 75, 0.25);
  box-shadow: 0 0 16px rgba(232, 180, 75, 0.2);
}
.analyse-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Annotated text output */
.annotated-text {
  font-family: var(--font-display);
  font-size: 1.05rem;
  line-height: 2;
  color: var(--pearl);
  letter-spacing: 0.01em;
}

/* Individual marker spans */
.m-span {
  border-radius: 3px;
  padding: 1px 3px;
  cursor: pointer;
  transition: opacity 0.2s, box-shadow 0.15s;
  position: relative;
}
.m-span:hover { opacity: 0.85; }
.m-span.dimmed { opacity: 0.3; }
.m-span.highlighted { box-shadow: 0 0 10px currentColor; }

.m-span.ato  { background: rgba(232, 180, 75, 0.22); color: var(--ato);  border-bottom: 1px solid var(--ato); }
.m-span.sem  { background: rgba(126, 207, 237, 0.18); color: var(--sem); border-bottom: 1px solid var(--sem); }
.m-span.clu  { background: rgba(255, 122, 122, 0.18); color: var(--clu); border-bottom: 1px solid var(--clu); }
.m-span.mema { background: rgba(180, 160, 255, 0.18); color: var(--mema);border-bottom: 1px solid var(--mema); }

/* Message blocks */
.msg-block {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.msg-block:last-child { border-bottom: none; }

.msg-role {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--pearl-dim);
  margin-bottom: 4px;
}

/* ── TOOLTIP ─────────────────────────────────────────── */
#tooltip {
  position: fixed;
  z-index: 100;
  background: var(--bg-card);
  border: 1px solid var(--border-lit);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  max-width: 260px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
#tooltip.visible { opacity: 1; }

.tt-id {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--amber);
  margin-bottom: 4px;
}

.tt-layer {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--pearl-dim);
  margin-bottom: 8px;
}

.tt-desc {
  font-family: var(--font-display);
  font-size: 0.85rem;
  color: var(--pearl);
  line-height: 1.5;
  font-style: italic;
}

.tt-conf {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tt-conf-bar-wrap {
  flex: 1;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
}
.tt-conf-bar {
  height: 100%;
  background: var(--amber);
  border-radius: 2px;
}

.tt-conf-val {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--amber);
}
```

**Step 2: Replace center panel body HTML**

Change `<div class="panel-body" id="dialogue-body">` to:

```html
<div class="panel-body" id="dialogue-body">
  <!-- Input area -->
  <div class="dialogue-input-area" id="input-area">
    <textarea class="dialogue-textarea" id="dialogue-input"
      placeholder="Dialog einfügen...&#10;&#10;A: Ich glaube... vielleicht wäre das falsch.&#10;B: Was meinst du damit?&#10;A: Ich weiß nicht. Es ist schwer zu sagen."
      rows="6"></textarea>
    <button class="analyse-btn" id="analyse-btn" onclick="runAnalysis()">
      ▶ Analysieren
    </button>
  </div>
  <!-- Annotated output (hidden until analysis) -->
  <div id="annotated-output" style="display:none"></div>
</div>

<!-- Tooltip (global, outside columns) -->
<div id="tooltip">
  <div class="tt-id" id="tt-id"></div>
  <div class="tt-layer" id="tt-layer"></div>
  <div class="tt-desc" id="tt-desc"></div>
  <div class="tt-conf">
    <div class="tt-conf-bar-wrap"><div class="tt-conf-bar" id="tt-conf-bar"></div></div>
    <span class="tt-conf-val" id="tt-conf-val"></span>
  </div>
</div>
```

**Step 3: Add dialogue rendering + tooltip JS (append to `<script>`)**

```javascript
/* ══════════════════════════════════════════════════════
   TOOLTIP
══════════════════════════════════════════════════════ */
const tooltip = document.getElementById('tooltip');
let tooltipTimer = null;

function showTooltip(marker, x, y) {
  clearTimeout(tooltipTimer);
  tooltipTimer = setTimeout(() => {
    document.getElementById('tt-id').textContent = marker.id;
    document.getElementById('tt-layer').textContent = `Layer: ${marker.layer.toUpperCase()} · Konfidenz`;
    document.getElementById('tt-desc').textContent = marker.description || 'Kein Beschreibung verfügbar.';
    document.getElementById('tt-conf-bar').style.width = (marker.confidence * 100) + '%';
    document.getElementById('tt-conf-val').textContent = (marker.confidence * 100).toFixed(0) + '%';

    // Layer color
    const layerColors = { ato: '#E8B44B', sem: '#7ECFED', clu: '#FF7A7A', mema: '#B4A0FF' };
    const col = layerColors[marker.layer] || '#E8B44B';
    tooltip.style.borderColor = col + '66';
    document.getElementById('tt-conf-bar').style.background = col;

    // Position
    const pad = 12;
    const tw = 260, th = 120;
    let left = x + pad, top = y - th / 2;
    if (left + tw > window.innerWidth) left = x - tw - pad;
    if (top < 8) top = 8;
    if (top + th > window.innerHeight - 8) top = window.innerHeight - th - 8;
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.classList.add('visible');
  }, 100);
}

function hideTooltip() {
  clearTimeout(tooltipTimer);
  tooltip.classList.remove('visible');
}

/* ══════════════════════════════════════════════════════
   ANNOTATED DIALOGUE RENDERER
══════════════════════════════════════════════════════ */
function renderAnnotatedDialogue(messages, markers) {
  const output = document.getElementById('annotated-output');
  output.innerHTML = '';

  // Build span map: messageIndex → list of {start, end, markerId}
  const spanMap = {};
  markers.forEach(m => {
    m.message_indices.forEach(mi => {
      if (!spanMap[mi]) spanMap[mi] = [];
      m.matches.forEach(match => {
        spanMap[mi].push({
          start: match.span[0],
          end: match.span[1],
          marker: m,
        });
      });
    });
  });

  messages.forEach((msg, idx) => {
    const block = document.createElement('div');
    block.className = 'msg-block';

    const roleEl = document.createElement('div');
    roleEl.className = 'msg-role';
    roleEl.textContent = msg.role || `Sprecher ${idx + 1}`;
    block.appendChild(roleEl);

    const textEl = document.createElement('div');
    textEl.className = 'annotated-text';

    const spans = (spanMap[idx] || []).sort((a, b) => a.start - b.start);

    if (spans.length === 0) {
      textEl.textContent = msg.text;
    } else {
      let cursor = 0;
      const text = msg.text;
      spans.forEach(s => {
        if (s.start > cursor) {
          textEl.appendChild(document.createTextNode(text.slice(cursor, s.start)));
        }
        const span = document.createElement('span');
        span.className = `m-span ${s.marker.layer}`;
        span.dataset.markerId = s.marker.id;
        span.textContent = text.slice(s.start, s.end);

        span.addEventListener('mouseenter', e => showTooltip(s.marker, e.clientX, e.clientY));
        span.addEventListener('mousemove', e => {
          if (tooltip.classList.contains('visible')) {
            tooltip.style.left = (e.clientX + 12) + 'px';
            tooltip.style.top = (e.clientY - 60) + 'px';
          }
        });
        span.addEventListener('mouseleave', hideTooltip);
        span.addEventListener('click', () => onMarkerClick(s.marker.id));
        textEl.appendChild(span);
        cursor = s.end;
      });
      if (cursor < text.length) {
        textEl.appendChild(document.createTextNode(text.slice(cursor)));
      }
    }

    block.appendChild(textEl);
    output.appendChild(block);
  });

  document.getElementById('input-area').style.display = 'none';
  output.style.display = 'block';
}

/* ══════════════════════════════════════════════════════
   MARKER ↔ NARRATIVE INTERACTION
══════════════════════════════════════════════════════ */
function onMarkerClick(markerId) {
  state.activeMarker = markerId;
  // Highlight spans for this marker
  document.querySelectorAll('.m-span').forEach(el => {
    el.classList.toggle('dimmed', el.dataset.markerId !== markerId);
    el.classList.toggle('highlighted', el.dataset.markerId === markerId);
  });
  // Highlight narrative cards referencing this marker
  document.querySelectorAll('.narrative-card').forEach(card => {
    const refs = card.dataset.markerRefs || '';
    const references = refs.split(',');
    card.classList.toggle('relevant', references.includes(markerId));
  });
}

function resetHighlights() {
  state.activeMarker = null;
  state.activeNarrative = null;
  document.querySelectorAll('.m-span').forEach(el => {
    el.classList.remove('dimmed', 'highlighted');
  });
  document.querySelectorAll('.narrative-card').forEach(c => {
    c.classList.remove('active', 'dimmed', 'relevant');
  });
}
```

**Step 4: Verify with mock data in browser console**

```javascript
// Paste in browser console at http://localhost:8420/resonanzraum:
const mockMessages = [
  { role: "A", text: "Ich glaube vielleicht, dass das falsch wäre." },
  { role: "B", text: "Was meinst du damit genau?" }
];
const mockMarkers = [
  {
    id: "ATO_HESITATION", layer: "ato", confidence: 0.85,
    description: "Zögernde Sprechweise — Signal für Unsicherheit.",
    message_indices: [0], matches: [{ span: [3, 10], matched_text: "glaube " }]
  },
  {
    id: "ATO_QUALIFIER", layer: "ato", confidence: 0.72,
    description: "Qualifizierende Sprache — Abschwächung der Aussage.",
    message_indices: [0], matches: [{ span: [11, 21], matched_text: "vielleicht" }]
  }
];
renderAnnotatedDialogue(mockMessages, mockMarkers);
// Expected: colored spans, tooltips on hover
```

**Step 5: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): annotated dialogue renderer + marker tooltips"
```

---

## Task 5: Narrative Cards Panel

**Files:**
- Modify: `api/static/resonanzraum.html`

**Step 1: Add CSS for narrative cards (inside `<style>`)**

```css
/* ── NARRATIVE CARDS ─────────────────────────────────── */
.narrative-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.narrative-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, opacity 0.2s;
  position: relative;
  overflow: hidden;
}

.narrative-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: var(--amber);
  opacity: 0;
  transition: opacity 0.2s;
}

.narrative-card:hover {
  border-color: rgba(232, 180, 75, 0.25);
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
}

.narrative-card.active {
  border-color: var(--border-lit);
  box-shadow: 0 0 24px rgba(232, 180, 75, 0.12);
}
.narrative-card.active::before { opacity: 1; }

.narrative-card.dimmed { opacity: 0.35; }

.narrative-card.relevant {
  border-color: rgba(126, 207, 237, 0.4);
}
.narrative-card.relevant::before {
  background: var(--cyan);
  opacity: 1;
}

.nc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  gap: 8px;
}

.nc-type {
  font-family: var(--font-mono);
  font-size: 0.56rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--amber);
  flex-shrink: 0;
}

.nc-type.alt  { color: var(--cyan); }
.nc-type.novel { color: var(--coral); }
.nc-type.uncertain { color: var(--lavender); }
.nc-type.cluster { color: var(--pearl-dim); }

.nc-confidence {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--pearl-dim);
}

.nc-text {
  font-family: var(--font-display);
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--pearl-mid);
  font-style: italic;
}

.nc-markers {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.nc-marker-ref {
  font-family: var(--font-mono);
  font-size: 0.55rem;
  padding: 2px 7px;
  border-radius: 10px;
  letter-spacing: 0.06em;
}

.nc-marker-ref.ato  { background: rgba(232,180,75,0.15); color: var(--ato); }
.nc-marker-ref.sem  { background: rgba(126,207,237,0.15); color: var(--sem); }
.nc-marker-ref.clu  { background: rgba(255,122,122,0.15); color: var(--clu); }
.nc-marker-ref.mema { background: rgba(180,160,255,0.15); color: var(--mema); }

/* Confidence ring on card */
.nc-conf-track {
  margin-top: 10px;
  height: 2px;
  background: var(--border);
  border-radius: 1px;
  overflow: hidden;
}
.nc-conf-fill {
  height: 100%;
  border-radius: 1px;
  background: var(--amber);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Uncertainty warning */
.nc-warning {
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--lavender);
  opacity: 0.8;
}
```

**Step 2: Add narrative rendering JS (append to `<script>`)**

```javascript
/* ══════════════════════════════════════════════════════
   NARRATIVE RENDERER
══════════════════════════════════════════════════════ */
const NARRATIVE_TYPES = {
  primary:   { label: 'Grundton',    cls: '' },
  alternative: { label: 'Oberton I',  cls: 'alt' },
  novel:     { label: 'Oberton II',  cls: 'novel' },
  uncertain: { label: 'Ungewiss',   cls: 'uncertain' },
  cluster:   { label: 'Cluster',    cls: 'cluster' },
};

function renderNarratives(narratives, markers) {
  const body = document.getElementById('narrative-body');
  body.innerHTML = '';

  if (!narratives || narratives.length === 0) {
    body.innerHTML = '<p style="color:var(--pearl-dim);font-size:0.85rem;font-style:italic">Keine Interpretationen verfügbar.</p>';
    return;
  }

  const stack = document.createElement('div');
  stack.className = 'narrative-stack';

  narratives.forEach((n, i) => {
    const typeKey = (n.type || 'primary').toLowerCase()
      .replace('primary reading', 'primary')
      .replace('alternative reading', 'alternative')
      .replace('novel pattern', 'novel')
      .replace('high-uncertainty variant', 'uncertain')
      .replace('weak cluster perspective', 'cluster');

    const typeInfo = NARRATIVE_TYPES[typeKey] || NARRATIVE_TYPES.primary;
    const refs = (n.supporting_markers || []).map(m => typeof m === 'string' ? m : m.id);

    const card = document.createElement('div');
    card.className = 'narrative-card';
    card.dataset.narrativeIdx = i;
    card.dataset.markerRefs = refs.join(',');

    card.innerHTML = `
      <div class="nc-header">
        <span class="nc-type ${typeInfo.cls}">${typeInfo.label}</span>
        <span class="nc-confidence">${((n.confidence || 0) * 100).toFixed(0)}%</span>
      </div>
      <div class="nc-text">${n.narrative || n.text || ''}</div>
      ${refs.length ? `
        <div class="nc-markers">
          ${refs.map(id => {
            const m = markers.find(mk => mk.id === id);
            const layer = m ? m.layer : 'ato';
            return `<span class="nc-marker-ref ${layer}" data-marker-id="${id}">${id}</span>`;
          }).join('')}
        </div>` : ''}
      ${n.uncertainty_flag ? '<div class="nc-warning">⚠ Hohe Kontextunsicherheit</div>' : ''}
      <div class="nc-conf-track">
        <div class="nc-conf-fill" style="width:0%" data-target="${(n.confidence||0)*100}"></div>
      </div>`;

    // Click: activate narrative, highlight its markers
    card.addEventListener('click', () => onNarrativeClick(i, refs, narratives));
    // Click on marker ref chip: highlight marker
    card.querySelectorAll('.nc-marker-ref').forEach(chip => {
      chip.addEventListener('click', e => {
        e.stopPropagation();
        onMarkerClick(chip.dataset.markerId);
      });
    });

    stack.appendChild(card);
  });

  body.appendChild(stack);

  // Stagger in confidence fills
  requestAnimationFrame(() => {
    body.querySelectorAll('.nc-conf-fill').forEach((fill, i) => {
      setTimeout(() => {
        fill.style.width = fill.dataset.target + '%';
      }, 200 + i * 120);
    });
    // Stagger card appearance
    body.querySelectorAll('.narrative-card').forEach((card, i) => {
      card.style.opacity = '0';
      card.style.transform = 'translateX(12px)';
      card.style.transition = 'opacity 0.3s, transform 0.3s';
      setTimeout(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateX(0)';
      }, 100 + i * 80);
    });
  });
}

function onNarrativeClick(idx, markerRefs, narratives) {
  state.activeNarrative = idx;

  // Card states
  document.querySelectorAll('.narrative-card').forEach((card, i) => {
    card.classList.toggle('active', i === idx);
    card.classList.toggle('dimmed', i !== idx);
  });

  // Highlight corresponding marker spans
  if (markerRefs.length > 0) {
    document.querySelectorAll('.m-span').forEach(el => {
      const isRef = markerRefs.includes(el.dataset.markerId);
      el.classList.toggle('dimmed', !isRef);
      el.classList.toggle('highlighted', isRef);
    });
  }

  // Morph equalizer if frame available (placeholder for LeanDeep 6.0)
  if (state.frame) {
    // future: apply narrative-specific frame weights
  }
}
```

**Step 3: Verify with mock data in browser console**

```javascript
// After running renderAnnotatedDialogue from Task 4, also run:
const mockNarratives = [
  {
    type: 'Primary Reading',
    narrative: 'Der Sprecher zeigt ausgeprägte Selbstzweifel. Das zögernde Sprachmuster deutet auf einen inneren Konflikt zwischen dem Wunsch nach Entscheidung und der Angst vor Fehlern hin.',
    confidence: 0.82,
    supporting_markers: ['ATO_HESITATION', 'ATO_QUALIFIER'],
  },
  {
    type: 'Alternative Reading',
    narrative: 'Alternativ könnte die zurückhaltende Sprache auf eine intellektuelle Sorgfalt hinweisen — ein Zeichen bewusster Reflexion, nicht Unsicherheit.',
    confidence: 0.65,
    supporting_markers: ['ATO_QUALIFIER'],
  },
  {
    type: 'Novel Pattern',
    narrative: 'Ein ungewöhnliches Muster: Der Sprecher fragt nie direkt, sondern stellt Hypothesen auf. Das könnte eine Strategie sein, Verantwortung zu vermeiden.',
    confidence: 0.54,
    supporting_markers: ['ATO_HESITATION'],
  }
];
renderNarratives(mockNarratives, mockMarkers);
// Expected:
# - 3 cards appear with stagger animation
# - Click card → dim others, highlight markers
# - Click marker chip → onMarkerClick fires
# - Hover over spans → tooltip appears
```

**Step 4: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): narrative overtone cards + bidirectional marker linking"
```

---

## Task 6: Reset + Pulse Animations

**Files:**
- Modify: `api/static/resonanzraum.html`

**Step 1: Add CSS pulse animation (inside `<style>`)**

```css
/* ── ANIMATIONS ──────────────────────────────────────── */
@keyframes markerPulse {
  0%, 100% { box-shadow: 0 0 0px currentColor; }
  50%       { box-shadow: 0 0 12px currentColor; }
}

.m-span.highlighted {
  animation: markerPulse 1.5s ease-in-out infinite;
}

@keyframes scanLine {
  from { transform: translateX(-100%); }
  to   { transform: translateX(100%); }
}

.panel-body.loading::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(232,180,75,0.06) 50%, transparent 100%);
  animation: scanLine 1.4s ease-in-out infinite;
  pointer-events: none;
}

.panel-body { position: relative; }
```

**Step 2: Add reset button to dialogue panel header (in HTML)**

Find the `<div class="panel-header">` of `#panel-center` and change it to:

```html
<div class="panel-header" style="display:flex;align-items:center;justify-content:space-between">
  <div>
    <div class="panel-label">Dialogtext</div>
    <div class="panel-title">Annotierter Verlauf</div>
  </div>
  <button id="reset-btn"
    onclick="resetView()"
    style="display:none;background:transparent;border:1px solid var(--border);color:var(--pearl-dim);
           font-family:var(--font-mono);font-size:0.58rem;letter-spacing:0.1em;text-transform:uppercase;
           padding:5px 12px;border-radius:var(--radius);cursor:pointer">
    ↺ Neu
  </button>
</div>
```

**Step 3: Add resetView() and loading state JS (append to `<script>`)**

```javascript
function resetView() {
  state.markers = [];
  state.narratives = [];
  state.frame = null;
  state.tenor = 0;
  resetHighlights();

  document.getElementById('annotated-output').style.display = 'none';
  document.getElementById('annotated-output').innerHTML = '';
  document.getElementById('input-area').style.display = 'flex';
  document.getElementById('reset-btn').style.display = 'none';

  document.getElementById('narrative-body').innerHTML =
    '<p style="color:var(--pearl-dim);font-size:0.85rem;font-style:italic">Keine Analyse aktiv.</p>';

  renderEqualizer(null);
  state.tenor = 0;
  setStatus('bereit', false);
}

function setStatus(text, active) {
  document.getElementById('status-text').textContent = text;
  document.getElementById('status-dot').classList.toggle('active', active);
  state.analysing = active;
}

function setLoading(isLoading) {
  document.getElementById('analyse-btn').disabled = isLoading;
  ['frame-body', 'narrative-body'].forEach(id => {
    document.getElementById(id).classList.toggle('loading', isLoading);
  });
}
```

**Step 4: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): pulse animations + loading states + reset"
```

---

## Task 7: Parse Dialogue Input

**Files:**
- Modify: `api/static/resonanzraum.html` — add input parser

**Step 1: Add input parsing JS (append to `<script>`)**

```javascript
/* ══════════════════════════════════════════════════════
   DIALOGUE INPUT PARSER
   Accepts:
     "A: text\nB: text"   → role-labelled messages
     "text\n\ntext"       → auto-role as "Sprecher 1", "Sprecher 2" etc.
     single block         → one message
══════════════════════════════════════════════════════ */
function parseDialogueInput(raw) {
  const lines = raw.trim().split('\n').filter(l => l.trim());

  // Format 1: "A: text" or "Person: text"
  const rolePattern = /^([A-Za-z0-9äöüÄÖÜß\s]{1,20}):\s*(.+)$/;
  const labelled = lines.every(l => rolePattern.test(l.trim()));

  if (labelled) {
    return lines.map(l => {
      const [, role, text] = l.match(rolePattern);
      return { role: role.trim(), text: text.trim() };
    });
  }

  // Format 2: Blank-line-separated paragraphs
  const paragraphs = raw.trim().split(/\n{2,}/);
  if (paragraphs.length > 1) {
    return paragraphs.map((p, i) => ({
      role: String.fromCharCode(65 + (i % 26)),
      text: p.replace(/\n/g, ' ').trim(),
    }));
  }

  // Format 3: Single message
  return [{ role: 'A', text: raw.trim() }];
}
```

**Step 2: Test in browser console**

```javascript
// Test all 3 formats:
console.log(parseDialogueInput("A: Ich bin unsicher.\nB: Warum das?"));
// Expected: [{role:'A', text:'Ich bin unsicher.'}, {role:'B', text:'Warum das?'}]

console.log(parseDialogueInput("Ich bin unsicher.\n\nWieso sagst du das?"));
// Expected: [{role:'A', ...}, {role:'B', ...}]

console.log(parseDialogueInput("Nur ein Satz."));
// Expected: [{role:'A', text:'Nur ein Satz.'}]
```

**Step 3: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): dialogue input parser (3 format variants)"
```

---

## Task 8: Wire Up to Real API

**Files:**
- Modify: `api/static/resonanzraum.html` — implement `runAnalysis()`

**Step 1: Add API integration JS (append to `<script>`)**

```javascript
/* ══════════════════════════════════════════════════════
   API INTEGRATION
   Calls: POST /v1/analyze/conversation
   Extends for: LeanDeep 6.0 semantic frame when ready
══════════════════════════════════════════════════════ */
async function runAnalysis() {
  const raw = document.getElementById('dialogue-input').value.trim();
  if (!raw) return;

  const messages = parseDialogueInput(raw);
  if (!messages.length) return;

  setLoading(true);
  setStatus('analysiere...', true);

  try {
    // ── 1. Conversation analysis (existing API) ──────
    const resp = await fetch('/v1/analyze/conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages,
        layers: ['ato', 'sem', 'clu', 'mema'],
        threshold: 0.35,
        language: 'de',
      }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    state.markers = data.markers || [];

    // ── 2. Build narratives from existing `reasoning` ──
    // (placeholder until LeanDeep 6.0 /v1/analyze/narrative endpoint)
    const narratives = buildNarrativesFromResponse(data);
    state.narratives = narratives;

    // ── 3. Build mock frame from markers ─────────────
    // (placeholder until LeanDeep 6.0 /v1/analyze/frame endpoint)
    const frame = buildFrameFromMarkers(state.markers, data.reasoning);
    state.frame = frame;
    if (frame) state.tenor = frame.emotional_tenor || 0;

    // ── 4. Render ─────────────────────────────────────
    renderEqualizer(frame);
    renderAnnotatedDialogue(messages, state.markers);
    renderNarratives(narratives, state.markers);

    document.getElementById('reset-btn').style.display = 'block';
    setStatus(`${state.markers.length} Marker · ${narratives.length} Narrative`, false);
    setLoading(false);

  } catch (err) {
    setStatus('Fehler: ' + err.message, false);
    setLoading(false);
    document.getElementById('dialogue-body').innerHTML = `
      <div style="color:var(--coral);font-family:var(--font-mono);font-size:0.8rem;padding:16px">
        ⚠ ${err.message}
        <br><br>
        <button onclick="resetView()" style="background:transparent;border:1px solid var(--coral);
          color:var(--coral);font-family:var(--font-mono);font-size:0.65rem;padding:6px 14px;
          border-radius:4px;cursor:pointer;letter-spacing:0.1em">↺ Zurücksetzen</button>
      </div>`;
  }
}

/* ══════════════════════════════════════════════════════
   BRIDGE HELPERS
   Adapt current API response → Resonanzraum structures
   Replace with direct LeanDeep 6.0 endpoints when ready
══════════════════════════════════════════════════════ */
function buildNarrativesFromResponse(data) {
  const narratives = [];
  const markers = data.markers || [];

  // Use existing reasoning.narrative as primary
  if (data.reasoning && data.reasoning.narrative) {
    narratives.push({
      type: 'Primary Reading',
      narrative: data.reasoning.narrative,
      confidence: data.reasoning.confidence_score || 0.75,
      supporting_markers: data.reasoning.evidence_marker_ids || [],
    });
  }

  // Synthesize alternative from high-confidence markers
  const strong = markers.filter(m => m.confidence >= 0.7).slice(0, 3);
  if (strong.length >= 2) {
    narratives.push({
      type: 'Alternative Reading',
      narrative: `${strong.map(m => m.description).join(' ')} — Eine alternative Lesart betont die Stärke dieser Signale als aktive Strategie statt passiver Reaktion.`,
      confidence: strong.reduce((a, m) => a + m.confidence, 0) / strong.length * 0.8,
      supporting_markers: strong.map(m => m.id),
    });
  }

  // Novel: temporal patterns
  if (data.temporal_patterns && data.temporal_patterns.length > 0) {
    const notable = data.temporal_patterns.find(t => t.trend !== 'stable');
    if (notable) {
      narratives.push({
        type: 'Novel Pattern',
        narrative: `Muster "${notable.marker_id}" zeigt eine ${notable.trend === 'increasing' ? 'zunehmende' : 'abnehmende'} Tendenz über den Gesprächsverlauf — ein emergentes Signal das auf Eskalation oder Deeskalation hindeutet.`,
        confidence: 0.58,
        supporting_markers: [notable.marker_id],
      });
    }
  }

  // Fallback: at least 1 narrative if empty
  if (narratives.length === 0 && markers.length > 0) {
    narratives.push({
      type: 'Primary Reading',
      narrative: `${markers.length} Marker erkannt. Dominantes Muster: ${markers[0].id} (${(markers[0].confidence * 100).toFixed(0)}% Konfidenz).`,
      confidence: markers[0].confidence,
      supporting_markers: [markers[0].id],
    });
  }

  return narratives;
}

function buildFrameFromMarkers(markers, reasoning) {
  if (!markers.length && !reasoning) return null;

  // Estimate emotional tenor from marker balance
  const negMarkers = markers.filter(m =>
    m.family && (m.family.includes('distress') || m.family.includes('conflict') || m.family.includes('hesitation'))
  );
  const tenor = markers.length
    ? Math.max(-0.8, Math.min(0.8, -negMarkers.length / markers.length * 1.2))
    : 0;

  return {
    tone: reasoning?.relational_pattern || 'unbekannt',
    themes: [...new Set(markers.map(m => m.family).filter(Boolean))].slice(0, 3),
    relational_dynamics: reasoning?.relational_pattern || '—',
    intent: '—',
    emotional_tenor: tenor,
    context_validity: 0.7,      // placeholder until LeanDeep 6.0
    offline_context_risk: 0.4,  // placeholder until LeanDeep 6.0
  };
}

/* ══════════════════════════════════════════════════════
   KEYBOARD SHORTCUT: Cmd+Enter to analyse
══════════════════════════════════════════════════════ */
document.getElementById('dialogue-input').addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') runAnalysis();
});

/* Click outside annotations → reset highlights */
document.addEventListener('click', e => {
  if (!e.target.closest('.m-span, .narrative-card, .nc-marker-ref')) {
    resetHighlights();
  }
});
```

**Step 2: End-to-end test**

```bash
# Ensure server is running
curl -s http://localhost:8420/v1/health
# Expected: {"status":"ok",...}

open http://localhost:8420/resonanzraum
```

In the browser:
1. Paste: `A: Ich glaube vielleicht, dass ich einen Fehler gemacht habe.\nB: Was meinst du?\nA: Ich weiß nicht... vielleicht war es falsch.`
2. Click "▶ Analysieren"
3. Expected:
   - Loading state activates (scan line animation)
   - Equalizer bars animate to values
   - Dialogue text shows colored marker spans
   - 1-3 narrative cards appear on right
   - Status bar shows "N Marker · M Narrative"

**Step 3: Test error handling**

```bash
# Stop the server briefly or make bad request
# Expected: coral error message with "↺ Zurücksetzen" button
```

**Step 4: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): real API integration + bridge helpers for LeanDeep 6.0"
```

---

## Task 9: Polish — Page Load Stagger + Equalizer Morph

**Files:**
- Modify: `api/static/resonanzraum.html`

**Step 1: Add page load stagger animation CSS**

```css
/* ── PAGE LOAD STAGGER ─────────────────────────────── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

#header          { animation: fadeUp 0.4s ease both; }
#panel-left      { animation: fadeUp 0.5s 0.1s ease both; }
#panel-center    { animation: fadeUp 0.5s 0.2s ease both; }
#panel-right     { animation: fadeUp 0.5s 0.3s ease both; }
```

**Step 2: Add equalizer morph on narrative select**

Inside `onNarrativeClick()`, replace the comment `// future: apply narrative-specific frame weights` with:

```javascript
// Morph equalizer bars to reflect narrative emphasis
const card = document.querySelectorAll('.narrative-card')[idx];
const refs = (card.dataset.markerRefs || '').split(',').filter(Boolean);
const relatedMarkers = state.markers.filter(m => refs.includes(m.id));

if (state.frame && relatedMarkers.length) {
  // Boost context risk dimension when uncertain narrative selected
  const typeClass = card.querySelector('.nc-type').className;
  const morphedFrame = { ...state.frame };
  if (typeClass.includes('uncertain')) {
    morphedFrame.offline_context_risk = Math.min(1, (state.frame.offline_context_risk || 0.4) + 0.2);
  } else if (typeClass.includes('alt')) {
    morphedFrame.emotional_tenor = -(state.frame.emotional_tenor || 0);
  }
  renderEqualizer(morphedFrame);
}
```

**Step 3: Add hover glow to entire left panel**

```css
/* Ambient glow from EQ on hover */
#panel-left:hover {
  box-shadow: inset 0 0 40px rgba(232, 180, 75, 0.03);
}
```

**Step 4: Final visual check checklist**

```
Open http://localhost:8420/resonanzraum and verify:

Layout:
  □ 3 columns visible (270px | flex | 310px)
  □ Grain texture overlay subtle but present
  □ Panels stagger in on page load

Header:
  □ Waveform animates continuously
  □ Title "RESONANZRAUM" in amber
  □ Status dot green during analysis, neutral at rest

Left Panel:
  □ 7 EQ bars animate to 0% on empty state
  □ After analysis: bars animate to values with 80ms stagger
  □ Context meters visible with cyan/coral fills
  □ Click narrative → equalizer morphs

Center Panel:
  □ Textarea accepts dialogue input
  □ Cmd+Enter triggers analysis
  □ After analysis: colored spans visible
  □ Hover span → tooltip appears after 100ms
  □ Click span → highlights this marker, dims others, marks relevant narratives

Right Panel:
  □ 3 narrative cards appear with stagger
  □ Click card → dims others, highlights relevant markers
  □ Confidence fill bar animates
  □ Marker ref chips clickable
  □ "↺ Neu" button resets to input state

Status:
  □ Error shows in coral with reset option
  □ Loading shows scan-line animation on panels
```

**Step 5: Commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): page load stagger, equalizer morph, final polish"
```

---

## Task 10: LeanDeep 6.0 Extension Points (Comments)

**Files:**
- Modify: `api/static/resonanzraum.html` — add `// TODO: LeanDeep 6.0` comments

**Step 1: Mark all bridge helpers with upgrade TODOs**

In `runAnalysis()`, after the existing API call, add comments:

```javascript
// ── TODO: LeanDeep 6.0 — replace with parallel calls ──────────────────
// const [frameResp, narrativeResp] = await Promise.all([
//   fetch('/v1/analyze/frame', { method: 'POST', ... }),       // SemanticFrame
//   fetch('/v1/analyze/narrative', { method: 'POST', ... }),    // Multi-Narrative
// ]);
// const frame = await frameResp.json();     // SemanticFrame {7 dims}
// const narratives = await narrativeResp.json();  // Narrative[]
// ──────────────────────────────────────────────────────────────────────
```

In `buildFrameFromMarkers()`, add at the top:

```javascript
// TODO: LeanDeep 6.0 — Replace this entire function with real SemanticFrame
// from /v1/analyze/frame when api/semantic.py is implemented (TASK-semantic-framing-implementation)
```

**Step 2: Document upgrade path in a comment at top of `<script>`**

```javascript
/*
 * Resonanzraum GUI — LeanDeep Analysis Interface
 *
 * Current state (LeanDeep 5.x compatible):
 *   - Uses /v1/analyze/conversation
 *   - Builds SemanticFrame from markers (approximate)
 *   - Builds narratives from reasoning + markers (bridge helpers)
 *
 * Upgrade to LeanDeep 6.0 (Week 3+):
 *   1. Replace buildFrameFromMarkers() → call /v1/analyze/frame
 *   2. Replace buildNarrativesFromResponse() → call /v1/analyze/narrative
 *   3. SemanticFrame: use real context_validity + offline_context_risk
 *   4. Narratives: use dynamic count (3 + floor(ocr * 2))
 *   5. Resonance weighting: use adjusted_confidence from API
 *
 * See: 3-code/tasks.md for API implementation plan
 */
```

**Step 3: Final commit**

```bash
git add api/static/resonanzraum.html
git commit -m "feat(ui): resonanzraum complete — leandeep 6.0 extension points documented"
```

---

## Done When

- [ ] `http://localhost:8420/resonanzraum` serves the interface
- [ ] 3-column layout: Equalizer | Dialogue | Narratives
- [ ] Dialogue text accepted in 3 formats (role-labelled, paragraph, single)
- [ ] POST to `/v1/analyze/conversation` works; markers appear as colored spans
- [ ] Tooltips appear on hover (100ms delay)
- [ ] Narrative cards appear with stagger animation
- [ ] Click narrative → highlights markers; click marker → marks narratives
- [ ] Equalizer morphs when switching narratives
- [ ] Page load stagger animation runs
- [ ] Error state handled gracefully
- [ ] LeanDeep 6.0 TODOs documented for Week 3 upgrade

---

## Plan complete and saved to `docs/plans/2026-04-04-resonanzraum-gui.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
