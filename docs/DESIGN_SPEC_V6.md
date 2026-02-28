# LeanDeep 6.0 — Design-Spezifikation

Dieses Dokument definiert das visuelle und funktionale Design für die LeanDeep 6.0 Plattform. Es dient als verbindliche Richtlinie für die Frontend-Entwicklung (Next.js, Tailwind CSS).

---

## 1. Visuelle Identität & Design Tokens

### 1.1 Farbpalette (Theming)
| Token | HEX | Anwendung |
| :--- | :--- | :--- |
| **Primary (Brand)** | `#0F172A` | Background (Slate-900), Sidebar |
| **Surface** | `#1E293B` | Cards, Elevated Panels (Slate-800) |
| **Border** | `#334155` | Dividers (Slate-700) |
| **Text Primary** | `#F8FAFC` | Headlines, Body (Slate-50) |
| **Text Muted** | `#94A3B8` | Subtitles, Footnotes (Slate-400) |

### 1.2 Layer-Farben (Die 4 Ebenen)
| Layer | HEX | Bedeutung |
| :--- | :--- | :--- |
| **ATO** | `#FACC15` | **Atomic:** Rohsignale, Keywords (Yellow-400) |
| **SEM** | `#FB923C` | **Semantic:** Kontext-Blends (Orange-400) |
| **CLU** | `#2DD4BF` | **Cluster:** Sequenzmuster (Teal-400) |
| **MEMA** | `#A855F7` | **Meta:** Diagnosen, Archetypen (Purple-500) |

### 1.3 Typografie
*   **Sans:** `Inter` (Standard für UI-Elemente)
*   **Mono:** `JetBrains Mono` (Für Marker-IDs, Metriken und Code-Ansichten)

---

## 2. Layout-Struktur (Analysis View)

Das Dashboard folgt einem **3-Spalten-Modell** (Masterplan `q8RPdK_`):

1.  **Sidebar (Left, 280px):**
    *   Navigation (Dashboard, Analysis, Personas).
    *   Layer-Filter (Checkboxes mit Farbindikatoren).
    *   System-Status (Health, Cloud-Security Badge).
2.  **Main Content (Center, Flexible):**
    *   **Header:** Anzeige des erkannten Beziehungsmusters (z.B. "Demand-Withdraw").
    *   **VAD Space Widget:** Interaktives 2D-Koordinatensystem für emotionalen Drift.
    *   **Transcript View:** Chatverlauf mit intelligentem Multi-Layer Highlighting.
3.  **Insight Panel (Right, 420px):**
    *   Detail-Ansicht für selektierte Marker.
    *   "Psychological Finding" (Warum schlägt dieser Marker an?).
    *   "Intervention Strategy" (Was bedeutet das für den Therapeuten?).

---

## 3. User Flow (UX)

1.  **Ingestion:** Nutzer lädt Chat hoch oder fügt Text ein.
2.  **Processing:** Progressive Loading State mit Anzeige der Layer-Aktivierung.
3.  **Instability Gate:** Das System prüft die topologische Integrität. Bei `instability: true` erscheint ein dezenter Hinweis: *"Analyse-Konfidenz reduziert: strukturelle Diskurs-Inkonsistenzen erkannt."*
4.  **Exploration:** Nutzer klickt auf einen Punkt im VAD-Space oder einen Marker im Text -> rechtes Panel aktualisiert sich sofort (Zustand Sync).
5.  **Action:** Generierung eines Kunden-Exports (PDF) oder Ableitung einer Handlungsstrategie.

---

## 4. Komponenten-Spezifikationen

### 4.1 Highlighting Engine
*   **Verschachtelung:** Wenn ein ATO-Marker innerhalb eines SEM-Markers liegt, wird der SEM-Marker durch einen Hintergrund (`bg-orange-400/10`) und der ATO-Marker durch eine doppelte Unterstreichung (`border-b-2 border-yellow-400`) markiert.
*   **Interaktion:** Hover über Marker zeigt Kurzinfo; Klick öffnet Deep Dive Panel.

### 4.2 VAD Space Chart
*   **Achsen:** Valence (X), Arousal (Y).
*   **Visualisierung:** Linienpfad mit Farbverlauf basierend auf der Zeit. Aktuelle Nachricht wird als pulsierender Punkt hervorgehoben.

### 4.3 Bento Grid (Dashboard)
*   Nutzung von Karten unterschiedlicher Größe für:
    *   Top 5 Marker-Frequenzen.
    *   Sprecher-Vergleich (Dominanz-Radar).
    *   Letzte 3 Analysen.

---

## 5. CRO & Trust Signale
*   **Security:** Permanentes Badge "GDPR Compliant & Locally Processed".
*   **Authority:** "Built on LeanDeep 6.0 Semantic Engine".
*   **Visuals:** Fokus auf Glassmorphism (`backdrop-blur-xl bg-white/5`) für ein technologisch fortgeschrittenes Gefühl.
