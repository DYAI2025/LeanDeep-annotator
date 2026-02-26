## Wireframe-Konvention

**[ ]** Container/Panel (R24), **( )** Button/Pill (R999), **{ }** Chip/Badge (R16)

**Highlight**: Interpretationsraum als **wash** im Text + optional 1px **border**

**Minimale Controls**: 2–4 Primäraktionen sichtbar, alles Weitere via **Popover / Tooltip / Kebab**

---

# Konzept 1 — Soft Canvas Neumorph (3 Screens)

## 1A — Workspace Leerzustand

**Ziel:** Start ohne Überforderung, klare 1-2 CTAs.

**Layout-Map**

Code

┌──────────────── Top Bar ────────────────┐
│ Lean Deep Annotator | (Import) (Export) │  Help(?)  |
└─────────────────────────────────────────┘
┌─ Left Rail ─┐ ┌──────────── Main Canvas ────────────┐ ┌─ Right Panel ─────┐
│ Layers      │ │ [Empty Card]                         │ │ [Context/Details] │
│ {ATO} {SEM} │ │  "Text einfügen oder importieren"    │ │  (eingeklappt)     │
│ {CLU} {MEMA}│ │  (Paste Text)  (Datei hochladen)     │ │                    │
│ Filter: All │ │  kleine Hinweise:                   │ │                    │
│ Legend      │ │  - Hover erklärt Layer              │ │                    │
└─────────────┘ └──────────────────────────────────────┘ └──────────────────┘

**Komponenten**

**Top Bar:** Projektname (editable), (Import), (Export disabled), Undo/Redo (icon-only), Help(?)

**Left Rail:** Layer-Toggles als Chips + Mini-Legende (Farbfleck + Label)

**Main Empty Card (Shadow.1):**

CTA 1: **(Paste Text)**

CTA 2: **(Datei hochladen .txt/.md)**

Hinweis: “Markiere Textstellen → wähle Layer → füge Interpretation hinzu”

**Right Panel:** collapsed (nur Tab sichtbar: “Details”)

**Interaktionen**

Hover auf Layer-Chip → Tooltip: „ATO = Beobachtung (objektiv).“

Paste/Upload → Wechsel in 1B.

---

## 1B — Workspace Aktive Annotation

**Ziel:** Selektion → schneller Layer-Entscheid → Interpretationsraum sauber erfassen.

**Layout-Map**

Code

┌──────────────── Top Bar ─────────────────────────────┐
│ Project ▾ | (Import) (Export)  Undo  Redo   Help(?)  │
└───────────────────────────────────────────────────────┘
┌─ Left Rail ─┐ ┌──────────── Text Canvas ─────────────┐ ┌──── Right Panel ───┐
│ Layers      │ │ Absatz mit Highlights (wash/tint)     │ │ Annotation Editor  │
│ {ATO on}    │ │  ─ selected span ─                   │ │ Layer: {ATO}{SEM}  │
│ {SEM on}    │ │   [Context Popover]                  │ │ {CLU}{MEMA}        │
│ {CLU off}   │ │   {ATO} {SEM} {CLU} {MEMA}           │ │ Begründung (1 Satz)│
│ {MEMA off}  │ │   (Interpretation hinzufügen)        │ │ Kontext (optional) │
│ Filter: All │ │   (Abbrechen)                        │ │ Evidenz: auto-Zitat│
│ Search…     │ │                                      │ │ Confidence ▓▓▓░░   │
│ Legend      │ │                                      │ │ (Speichern)        │
└─────────────┘ └──────────────────────────────────────┘ └───────────────────┘

**Komponenten**

**Text Canvas:**

Selektion zeigt **Context Popover** (Shadow.2, R24) direkt über Markierung

Bereits bestehende Marker: Hintergrund **wash** + feine Outline **border**

**Right Panel (Details offen):**

**Layer-Switch** als Chips (max 4 sichtbar)

Feld „**Begründung**“ (Pflicht, 1–2 Zeilen)

„**Kontext**“ (optional, Accordion)

„**Evidenz**“ (auto: zitiertes Textfragment + Sprunglink)

„**Confidence**“ als dezenter Balken

Primär: **(Speichern)**, Sekundär: (Verwerfen)

**Interaktionen**

Hover über Highlight → Tooltip: „Warum markiert? (Kurzbegründung + Layer)“

Klick auf Highlight → Right Panel springt zur Annotation, pulsiert subtil

Layer-Toggle im Left Rail filtert Canvas (andere Layer “ghosted” statt versteckt)

---

## 1C — Export-Preview (Modal Sheet)

**Ziel:** Export ohne UI-Chaos: Optionen links, Preview rechts.

**Layout-Map**

Code

┌──────────────────────── Export Sheet (R28, Shadow.2) ───────────────────────┐
│ Exportieren  | Format: (Markdown) (PDF)                                      │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ Optionen     │ Preview                                                      │
│ [x] ATO      │  Dokumentansicht mit sauberem Text                            │
│ [x] SEM      │  Layer-Legende oben                                           │
│ [ ] CLU      │  Highlights als inline Markup (MD) / Farbflächen (PDF)        │
│ [ ] MEMA     │  Interpretationsräume als Blöcke unter den Zitaten            │
│ Style:       │  Seitenumbrüche/Absatzspiegel (PDF)                           │
│  (Clean)     │                                                             │
│  (Report)    │                                                             │
│ [x] Begründung│                                                             │
│ [x] Confidence│                                                             │
│ (Zurück)     │                          (Export starten)                    │
└──────────────┴──────────────────────────────────────────────────────────────┘

**Interaktionen**

Toggle “Report” zeigt zusätzlich: Zusammenfassung je Layer, Index der Marker

PDF Preview zeigt Print-Layout (A4), Markdown Preview zeigt Syntax-Snippet (read-only)

---

# Konzept 2 — Ribbon-Layers Infographic (3 Screens)

## 2A — Workspace Leerzustand (Tracks vorbereitet)

**Ziel:** Layer als „Spuren“ erklären, ohne zu überladen.

**Layout-Map**

Code

┌────────────── Top Bar ──────────────┐
│ Project | (Import) (Export) Help(?) │
└─────────────────────────────────────┘
┌─ Sidebar Tabs ─┐ ┌─ Track Column ─┐ ┌──────── Text Area ────────┐
│ (All) (ATO)    │ │ ATO | SEM |…   │ │ [Empty State]             │
│ (SEM) (CLU)    │ │ • • • (placeholder) │ "Text einfügen…"      │
│ (MEMA)         │ │                  │ │ (Paste) (Upload)        │
└────────────────┘ └──────────────────┘ └─────────────────────────┘

**Komponenten**

Tabs als **Segmented Control** (All/ATO/SEM/CLU/MEMA)

Track Column zeigt leere Skalen/Marker-Platzhalter (sehr dezent)

**Interaktionen**

Hover auf Track-Header „SEM“ → Mini-Tooltip: „Bedeutung – kann auf aktive Hypothesen referenzieren.“

---

## 2B — Aktive Annotation (Track-Dots + Ribbon Labels)

**Ziel:** Selektion erzeugt Marker in **Track-Spur** + Ribbon-Label am Text.

**Layout-Map**

Code

┌────────────── Top Bar ──────────────┐
│ Project | (Import) (Export) Help(?) │
└─────────────────────────────────────┘
┌─ Tabs ─────────┐ ┌─ Track Column ───────────────┐ ┌──── Text Area ─────────┐
│ All | ATO |…   │ │ ATO:  •   •                   │ │ Text mit Ribbon Labels │
│ Filter ▾        │ │ SEM:    •      •              │ │ [ATO] am Rand          │
└────────────────┘ │ CLU:  (ghosted)               │ │ Selektion → Popover    │
                   │ MEMA: (ghosted)               │ │ {Layer Chips} (Add)    │
                   └───────────────────────────────┘ └─────────┬─────────────┘
                                                                │
                                                   ┌────────────▼───────────┐
                                                   │ Details Sheet (slide)  │
                                                   │ Kurzbegründung         │
                                                   │ Kontext/Referenzen     │
                                                   │ Confidence             │
                                                   │ (Speichern)            │
                                                   └────────────────────────┘

**Interaktionen**

Klick auf Track-Dot → scrollt zu Textstelle, öffnet Details Sheet

Hover auf Dot → Mini-Card (1 Satz + Confidence)

Layer-Tab “SEM” blendet nur SEM-Spur + SEM-Highlights ein (andere ausgegraut)

---

## 2C — Export-Preview (mit Track-Zusammenfassung)

**Ziel:** Export kann optional „Layer-Tracks“ als Index darstellen.

**Layout-Map**

Code

┌──────────── Export ────────────┐
│ Format: (Markdown) (PDF)       │
├───────────┬────────────────────┤
│ Optionen  │ Preview            │
│ [x] Tracks│  PDF: Indexseite   │
│ [x] Legende│  - ATO/SEM…       │
│ [x] Gründe │  - Track-Timeline │
│ (Clean)   │  dann Text + Notes │
│ (Report)  │                    │
│           │        (Export)    │
└───────────┴────────────────────┘

---

# Konzept 3 — Editorial Margin Notes (3 Screens)

## 3A — Leerzustand (Reading-First)

**Ziel:** Dokument-Gefühl, weniger „Tool“, mehr „Lesen & Notieren“.

**Layout-Map**

Code

┌────────────── Top Bar ──────────────┐
│ Project | (Import) (Export) Help(?) │
└─────────────────────────────────────┘
┌────────────── Document Canvas (max width ~72–78ch) ──────────────┐ ┌─ Index ─┐
│ [Empty] "Text einfügen…" (Paste) (Upload)                         │ │ 0 Notes │
│                                                                   │ │ Search  │
└───────────────────────────────────────────────────────────────────┘ └─────────┘

**Komponenten**

Document Canvas wie Papier (Surface), viel Luft, klare Typo

Rechter Index ist leer und klein (nicht dominant)

---

## 3B — Aktive Annotation (Randnotiz-Composer)

**Ziel:** Annotation als **Margin Note Card** statt Popover-Overload.

**Layout-Map**

Code

┌────────────── Top Bar ──────────────┐
│ Project | (Import) (Export) Help(?) │
└─────────────────────────────────────┘
┌──────── Document Canvas ─────────────────────────────────────────┐ ┌─ Index ─────┐
│ Text… [highlight wash]                                           │ │ Filter Layer │
│  └──── feine Verbindungslinie ───► [Margin Note Card]            │ │ {ATO}{SEM}   │
│                               Layer: {ATO}{SEM}{CLU}{MEMA}       │ │ Sort: Conf ↓ │
│                               Begründung (1 Satz)                │ │ Notes (list) │
│                               Kontext (optional)                 │ │              │
│                               Confidence ▓▓▓░░                   │ │              │
│                               (Speichern) (Verwerfen)            │ │              │
└──────────────────────────────────────────────────────────────────┘ └──────────────┘

**Interaktionen**

Klick auf Note im Index → springt zur Stelle, Note „glow“ kurz (sehr soft)

Hover auf Highlight → zeigt Mini-Preview der Randnotiz (Caption)

---

## 3C — Export-Preview (Print-optimiert)

**Ziel:** PDF als „Bericht“, Markdown als „clean notes“.

**Layout-Map**

Code

┌──────────── Export ────────────┐
│ Format: (PDF) (Markdown)       │
├───────────┬────────────────────┤
│ Optionen  │ Preview            │
│ [x] Margin│  PDF: Seitenlayout │
│ [x] Layer │  - Text links      │
│ [x] Gründe│  - Randnotizen     │
│ [ ] Index │  - Legende         │
│ (Clean)   │                    │
│ (Report)  │        (Export)    │
└───────────┴────────────────────┘

---

## Mini-Checkliste „1-Tag Wireframe Output“

Damit du wirklich nach 1 Tag „fertig“ bist, würde ich **pro Screen** genau diese Artefakte abliefern:

**Layout-Boxes** (Top/Left/Main/Right oder Document/Index)

**Component-Labels** (Buttons/Chips/Popover/Sheet)

**1–2 Key-States** (Hover Tooltip + Selected Highlight)

**Microcopy** (Empty State + Tooltip-Text)

**Export-Optionen** (Layer toggles + Format switch)
