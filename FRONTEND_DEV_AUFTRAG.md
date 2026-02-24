# LeanDeep Frontend — Dev-Auftrag

## Produkt

LeanDeep ist ein deterministischer Analyse-Service fuer psychologische Muster in menschlicher Kommunikation. 848 Marker erkennen Emotionsdynamiken, Manipulationsmuster, Beziehungsgesundheit und Kommunikationsstile — ohne KI, rein regelbasiert, in <5ms.

**Live-API:** https://leandeep.fly.dev
**API-Docs:** https://leandeep.fly.dev/docs
**Domain:** leandeep.de

## Zielgruppe

- Coaches, Therapeuten, Mediatoren
- Beziehungsberater
- HR/People & Culture Teams
- Non-technical: kein Terminal, kein JSON, kein Fachjargon

## Ziel

Web-App unter leandeep.de: Texte und Konversationen automatisch analysieren, Ergebnisse visuell aufbereitet, ueber Zeit Persona-Profile aufbauen. Design und Usability muessen herausragend sein — das Frontend IST das Produkt.

---

## Tech-Stack

| Komponente | Technologie | Hinweis |
|---|---|---|
| Framework | Vite + React 19 | Kein Next.js. SPA reicht. |
| Styling | Tailwind CSS 4 | Mit Custom Theme (siehe Design-System) |
| Animations | Framer Motion | Spring-based, nicht linear |
| Icons | Lucide React | Konsistent, clean |
| Charts | Recharts oder tremor.so | Fuer VAD-Verlauf, Episoden-Timeline |
| Deployment | Vercel oder Fly.io Static | Custom Domain: leandeep.de |
| API Backend | REST API (https://leandeep.fly.dev) | Kein eigener Server noetig |
| Auth | Noch nicht noetig | Kommt spaeter |

---

## Design-System (vorgegeben, uebernehmen)

Ein Design-Konzept existiert bereits als Referenz. Das folgende Design-System ist daraus abgeleitet und **verbindlich**.

### Farben — Design Tokens

```css
/* Neutrals */
--color-bg: #F6F5F3;
--color-surface: #FFFFFF;
--color-surface-elevated: #FBFAF8;
--color-border: #E6E3DF;
--color-text-primary: #1F2430;
--color-text-secondary: #4B5563;
--color-text-muted: #6B7280;
--color-focus-ring: #7C6FF2;

/* Layer ATO — Warm Coral */
--color-ato-accent: #F26B63;
--color-ato-border: #F9BCB9;
--color-ato-soft: #FBD6D3;
--color-ato-tint: #FDE4E3;
--color-ato-wash: rgba(242,107,99,0.18);

/* Layer SEM — Lavender/Indigo */
--color-sem-accent: #7C6FF2;
--color-sem-border: #C4BEF9;
--color-sem-soft: #DAD7FB;
--color-sem-tint: #E7E5FD;
--color-sem-wash: rgba(124,111,242,0.18);

/* Layer CLU — Aqua/Teal */
--color-clu-accent: #3FBCC1;
--color-clu-border: #A9E1E3;
--color-clu-soft: #C9ECEE;
--color-clu-tint: #DCF3F4;
--color-clu-wash: rgba(63,188,193,0.18);

/* Layer MEMA — Soft Amber */
--color-mema-accent: #F2B35C;
--color-mema-border: #F9DDB6;
--color-mema-soft: #FBEAD1;
--color-mema-tint: #FDF1E2;
--color-mema-wash: rgba(242,179,92,0.18);
```

### Typografie

```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

/* Klassen */
.text-h1: 28px / 36px, weight 650, tracking -0.01em
.text-h2: 20px / 28px, weight 600, tracking -0.005em
.text-body: 16px / 26px, weight 450
.text-caption: 13px / 18px, weight 500, tracking 0.01em
```

### Shadows

```css
--shadow-card: 0 6px 20px rgba(31,36,48,0.10), 0 1px 2px rgba(31,36,48,0.06);
--shadow-elevated: 0 16px 50px rgba(31,36,48,0.14), 0 4px 10px rgba(31,36,48,0.08);
--shadow-inner: inset 0 2px 4px rgba(31,36,48,0.06);
```

### Radii

```
--radius-sm: 16px
--radius-md: 24px
--radius-lg: 28px
--radius-full: 999px
```

### Animationen

- `fadeIn`: opacity 0→1, translateY 4px→0, 0.2s ease-out
- `slideIn`: opacity 0→1, translateX -10px→0, 0.3s ease-out
- `pulse-soft`: opacity 1→0.7→1, 2s infinite
- `hover-lift`: translateY -2px + shadow-elevated on hover, 0.2s ease-out
- Springs (Framer Motion): damping 25, stiffness 200-300

### Glass-Effekt

```css
background: rgba(255, 255, 255, 0.7);
backdrop-filter: blur(10px);
```

### Design-Prinzipien

1. **Soft Neumorphic** — Weiche Schatten, keine harten Kanten, alles rounded-2xl (16px) oder groesser
2. **Weissraum** — Grosszuegig. Karten mit p-6 bis p-12, kein visuelles Gedraenge
3. **Layer-Farbkodierung** — Konsistent ueberall: ATO=Coral, SEM=Indigo, CLU=Teal, MEMA=Amber
4. **Animationen subtil** — Ergebnisse faden in, Panels sliden, keine Spielereien
5. **Mobile-first** — Alles muss ab 375px funktionieren
6. **Vertrauen** — "Made in Germany", "Keine KI", "DSGVO-konform" dezent sichtbar

---

## Seiten / Views

### 1. Landing Page (`/`)

**Zweck:** Erklaeren was LeanDeep kann, direkt ausprobieren lassen.

- Hero: Headline + Subline + CTA "Text analysieren"
- Inline-Demo: Textfeld mit Beispieltext, "Analysieren"-Button, Ergebnis erscheint darunter
- 4 Feature-Cards (eine pro Layer) mit Layer-Farben
- Trust-Badges: "Keine KI", "DSGVO", "Made in Germany", "<5ms Analyse"
- Footer: Impressum, Datenschutz, API-Docs

### 2. Einzeltext-Analyse (`/analyze`)

**Zweck:** Einen einzelnen Text analysieren.

**API:** `POST /v1/analyze`

**Input:**
- Textfeld (min-height 200px, rounded-[28px], shadow-card)
- Confidence-Slider (Standard 0.5)
- Button "Analysieren" (bg-text-primary, color-surface)

**Output:**
- Zusammenfassung: X Muster erkannt, Verarbeitungszeit
- Marker-Cards als Liste, jede Karte:
  - Marker-Name menschenlesbar (nicht `CLU_GASLIGHTING_SEQUENCE` sondern "Gaslighting-Sequenz")
  - Kurzbeschreibung
  - Konfidenz als visueller Balken (Layer-Farbe)
  - Layer-Badge farblich kodiert (wash-Background + accent-Text)
  - Aufklappbar: gematchter Text hervorgehoben
- Sortierung: Nach Konfidenz absteigend
- Layer-Filter: Toggle-Buttons im LeftSidebar-Stil (aus Design-Konzept uebernehmen)

### 3. Konversations-Analyse (`/conversation`)

**Zweck:** Einen Chat analysieren (WhatsApp-Export, Therapiesitzung, etc.)

**API:** `POST /v1/analyze/dynamics`

**Input:**
- Chat-Upload: Copy-Paste Textfeld ODER Datei-Upload (.txt)
- Automatische Sprecher-Erkennung
- Button "Konversation analysieren"

**Output — 4 Tabs:**

| Tab | Inhalt |
|---|---|
| Uebersicht | Nachrichten-Anzahl, Sprecher, Top-5-Marker als grosse Cards, Beziehungs-Score (Trust/Conflict/Deeskalation) |
| Emotionsverlauf | Linien-Chart: Valenz, Arousal, Dominanz pro Sprecher. Hover zeigt Nachricht. Layer-Farben nutzen. |
| Marker-Timeline | Horizontale Timeline, Marker als farbige Punkte/Balken nach Layer. Klick oeffnet Detail-Card. |
| Alle Marker | Vollstaendige Marker-Liste + in welchen Nachrichten erkannt + Temporal Pattern (steigend/fallend/stabil) |

### 4. Persona-Dashboard (`/persona`) — Pro Tier

**Zweck:** Laengerfristige Analyse ueber mehrere Sessions.

**APIs:**
- `POST /v1/personas` (erstellen)
- `GET /v1/personas/{token}` (Profil)
- `POST /v1/analyze/dynamics` mit `persona_token`
- `GET /v1/personas/{token}/predict` (Vorhersagen)

**Ansicht:**
- Persona erstellen oder per Token laden
- Session-History als Timeline
- EWMA-Verlauf: Langzeit-Emotionstrend ueber Sessions
- Episoden-Timeline: Farbkodiert (ATO-Coral=Eskalation, CLU-Teal=Repair, Grau=Rueckzug, MEMA-Amber=Ruptur, SEM-Indigo=Stabilisierung)
- Vorhersage-Widget: Shift-Wahrscheinlichkeiten als Balken
- Neue Session analysieren: Chat eingeben, wird Persona zugeordnet

### 5. API/Developers (`/developers`)

- Weiterleitung auf OpenAPI-Docs oder eigene Docs-Seite
- MCP-Server Konfiguration
- Code-Beispiele (curl, Python, JavaScript)

---

## Layout-Architektur

### 3-Panel-Layout (aus Design-Konzept uebernehmen)

```
┌──────────────────────────────────────────────────┐
│ TopBar (h-16, border-bottom)                     │
│  Logo · Navigation · Actions                     │
├────────┬───────────────────────────┬─────────────┤
│ Left   │ Main Content             │ Right Panel  │
│ Side-  │ (flex-1, overflow-y-auto)│ (w-96,       │
│ bar    │                          │  conditional) │
│ (w-64) │ Analyse-Ergebnisse       │ Marker-Detail│
│        │ Charts                   │ VAD-Werte    │
│ Layer  │ Timeline                 │ Confidence   │
│ Filter │                          │ Kontext      │
│        │                          │              │
└────────┴───────────────────────────┴─────────────┘
```

- **TopBar:** Logo, Navigation (Analyse/Konversation/Persona/API), optional: Undo/Redo, Export
- **LeftSidebar:** Layer-Filter (ATO/SEM/CLU/MEMA Toggles mit Farbpunkten), Legende. Design 1:1 aus Konzept.
- **Main Content:** Wechselt je nach Route
- **RightPanel:** Oeffnet bei Klick auf Marker, zeigt Detail (gematchter Text, Konfidenz, Layer, VAD-Werte, Beschreibung). Slide-in Animation.

### Komponenten-Struktur

```
src/
├── App.tsx                    # Router + Layout-Shell
├── index.css                  # Design Tokens (@theme)
├── types/index.ts             # TypeScript Typen
├── lib/
│   ├── layers.ts              # Layer-Farb-Konfiguration (aus Konzept)
│   ├── api.ts                 # API-Client (fetch-Wrapper)
│   └── chat-parser.ts         # WhatsApp/Generic Chat-Parser
├── context/
│   └── AppContext.tsx          # Globaler State (results, filters, selected marker)
├── components/
│   ├── layout/
│   │   ├── TopBar.tsx
│   │   ├── LeftSidebar.tsx     # Layer-Toggles (aus Konzept, 1:1)
│   │   └── RightPanel.tsx      # Marker-Detail (umgebaut: API-Daten statt manuell)
│   ├── analysis/
│   │   ├── TextInput.tsx       # Textfeld + Confidence-Slider + Analyse-Button
│   │   ├── MarkerCard.tsx      # Einzelner Marker als Karte
│   │   ├── MarkerList.tsx      # Sortierte/gefilterte Marker-Liste
│   │   └── ResultSummary.tsx   # "X Muster erkannt in Y ms"
│   ├── conversation/
│   │   ├── ChatInput.tsx       # Paste/Upload + Parser
│   │   ├── EmotionChart.tsx    # VAD-Linien-Chart
│   │   ├── MarkerTimeline.tsx  # Horizontale Marker-Timeline
│   │   └── ConversationTabs.tsx
│   ├── persona/
│   │   ├── PersonaCreate.tsx
│   │   ├── PersonaProfile.tsx
│   │   └── EpisodeTimeline.tsx
│   └── shared/
│       ├── LayerBadge.tsx      # Farbiges Layer-Label
│       ├── ConfidenceBar.tsx   # Visueller Konfidenz-Balken
│       └── EmptyState.tsx      # Leerzustand (aus Konzept: Icon + Text + CTA)
└── hooks/
    └── useAnalysis.ts          # API-Calls + Loading/Error State
```

---

## Kern-Unterschied zum Design-Konzept

Das Design-Konzept ist ein **manuelles Annotations-Tool** (User markiert Text, waehlt Layer, schreibt Begruendung). LeanDeep ist das Gegenteil — **automatische Analyse**:

| Design-Konzept (manuell) | LeanDeep (automatisch) |
|---|---|
| User markiert Text per Maus | Engine erkennt Marker automatisch |
| User waehlt Layer per Popover | Layer wird vom Marker bestimmt |
| User schreibt Begruendung | Engine liefert Confidence + VAD |
| Kein API-Call | `POST /v1/analyze` ist der Kern |
| Export als Markdown | Live-Ergebnisse mit Charts |
| Einzeltext Paste | Chat-Parser + Konversations-Analyse |

### Was uebernommen wird (~30%)

- **Design-System komplett:** Farben, Typography, Shadows, Radii, Animations, CSS Tokens
- **LeftSidebar:** Layer-Toggles 1:1 (filtern statt an/aus-schalten die API-Ergebnisse)
- **Layout-Shell:** 3-Panel-Architektur, TopBar, Panel-Slide-Animationen
- **Empty States:** Icon + Text + CTA Muster
- **Layer-Konfiguration:** `src/lib/layers.ts` mit Farb-Objekten pro Layer

### Was neu gebaut wird (~70%)

- **TextInput statt TextCanvas:** Einfaches Textfeld + Button statt markierbarer Text
- **MarkerCard/MarkerList statt AnnotationPopover:** API-Ergebnisse als Karten statt manuelle Annotation
- **RightPanel:** Zeigt Marker-Detail aus API-Response (confidence, VAD, matches) statt manuelle Interpretation
- **API-Client:** fetch-Wrapper fuer alle Endpoints
- **Chat-Parser:** WhatsApp/Telegram/Generic Format → messages Array
- **Charts:** VAD-Verlauf, Marker-Timeline, Episoden-Timeline
- **Router:** React Router fuer 5 Seiten
- **Persona-Workflow:** Create/Load/Analyze/Predict

---

## API-Anbindung

**Base URL:** `https://leandeep.fly.dev` (spaeter: `https://api.leandeep.de`)

**Kein Auth noetig** (wird spaeter ergaenzt).

### Einzeltext

```typescript
// POST /v1/analyze
const response = await fetch('https://leandeep.fly.dev/v1/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "...",
    threshold: 0.5,
    layers: ["ATO", "SEM", "CLU", "MEMA"]
  })
});
// -> { markers: [...], processing_time_ms: 2.3, layer_summary: {...} }
```

### Konversation mit Dynamics

```typescript
// POST /v1/analyze/dynamics
const response = await fetch('https://leandeep.fly.dev/v1/analyze/dynamics', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [
      { role: "A", text: "..." },
      { role: "B", text: "..." }
    ],
    threshold: 0.5,
    persona_token: null
  })
});
// -> { results: [...], vad_trajectory: [...], dynamics: {...}, state_indices: {...} }
```

### Vollstaendige API-Docs

Alle Request/Response Schemas: https://leandeep.fly.dev/docs

---

## Chat-Parser (Client-seitig)

Parser fuer Copy-Paste Chat-Exports:

**WhatsApp:**
```
21.02.26, 14:32 - Anna: Ich verstehe nicht was du meinst
21.02.26, 14:33 - Ben: Das ist doch offensichtlich
```

**Generisch:**
```
A: Ich verstehe nicht was du meinst
B: Das ist doch offensichtlich
```

Parser extrahiert `role` und `text`, erstellt `messages`-Array fuer API.

---

## Lesbarer Marker-Name

Marker-IDs in menschenlesbare deutsche Labels uebersetzen:

```
CLU_GASLIGHTING_SEQUENCE    -> "Gaslighting-Sequenz"
SEM_REPAIR_GESTURE          -> "Reparatur-Geste"
ATO_DEPRESSION_SELF_FOCUS   -> "Selbstfokus (Depression)"
```

Mapping aus `description`-Feld der API (`GET /v1/markers`) oder als separates JSON. Fallback: ID ohne Prefix, Underscores durch Leerzeichen.

---

## Nicht im Scope

- User-Accounts / Login
- Bezahl-Integration (Stripe)
- Multi-Language (erstmal nur Deutsch)
- Admin-Panel
- WebSocket / Live-Analyse
- Dark Mode (spaeter)

---

## Abnahmekriterien

1. Alle 5 Seiten funktionieren und sind responsiv (Desktop + Mobile ab 375px)
2. Design-System exakt wie spezifiziert (Farben, Radii, Shadows, Typography)
3. Layer-Farbkodierung konsistent auf allen Seiten
4. Analyse-Ergebnisse erscheinen innerhalb 2 Sekunden
5. Charts rendern korrekt fuer Konversationen mit 2-200 Nachrichten
6. Chat-Parser erkennt WhatsApp-Format und generisches A/B-Format
7. Lighthouse Performance Score >= 90
8. Animationen smooth (Framer Motion, spring-based)
9. Empty States fuer alle Zustaende (kein Text, keine Ergebnisse, kein Persona-Token)
10. Deployment auf Vercel/Fly, leandeep.de zeigt die App
