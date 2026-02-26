# LeanDeep Frontend UI 6.0 — Anforderungen & Architektur

Dieses Dokument beschreibt die Spezifikationen für die Neuentwicklung des LeanDeep Frontends. Ziel ist der Übergang von einem technischen Debugger-Tool zu einem hochkarätigen **Expert Dashboard**, das psychologische Muster intuitiv erfassbar macht.

## 1. Vision: Das "Expert Dashboard"
Weg von linearen Listen, hin zum **synoptischen Blick**. Der Nutzer muss auf einen Blick sehen, wie Text (Beweis), VAD-Raum (Prozess) und Beziehungsmuster (Ergebnis) zusammenhängen.

---

## 2. Funktionale Anforderungen

### 2.1 Der synoptische Blick (3-Spalten-Layout)
*   **Spalte 1 (Transcript):** Vollständiger Chat-Verlauf mit intelligentem, mehrfarbigem Highlighting der Marker (ATO, SEM, CLU, MEMA).
*   **Spalte 2 (Dynamics):** 
    *   **VAD-Space:** Ein 2D-Koordinatensystem (Valenz/Arousal), in dem die Konversation als "Pfad" (Emotional Drift) gezeichnet wird.
    *   **Speaker-Radar:** Vergleich der Sprecherprofile (Intensität vs. Selbstbezug).
*   **Spalte 3 (Insights):**
    *   **Priorität 1: Beziehungsmuster.** Klare Benennung der Dynamik (z.B. "Demand-Withdraw").
    *   **Priorität 2: Narrative Deutung.** Fließtext über die psychologische Grundstimmung.
    *   **Resilienz-Profil:** Anzeige von "Grenz-Resilienz" (was wurde vermieden) und "Fehlenden Anteilen".

### 2.2 Layered Highlighting
Ein konsistentes Farbschema über alle Komponenten hinweg:
*   **ATO (Atomic):** Gelb (Rohsignale)
*   **SEM (Semantic):** Orange (Kontext-Blends)
*   **CLU (Cluster):** Türkis (Sequenz-Muster)
*   **MEMA (Meta):** Violett (Organismus-Diagnose)

---

## 3. Architektonische Anforderungen

*   **Framework:** **React** oder **Next.js** (TypeScript zwingend erforderlich für Typsicherheit der komplexen API-Modelle).
*   **State Management:** **Zustand**. Wir benötigen einen globalen Store für den `SelectedMessage`-State, damit Klicks im Chart sofort das Highlighting im Text und die Details in der Insight-Card aktualisieren.
*   **Komponenten-Struktur:**
    *   `<TranscriptView />`: Render-Logik für überlappende Annotationen.
    *   `<DynamicsPlot />`: Interaktive Visualisierung des emotionalen Raums.
    *   `<InsightEngine />`: Vorverarbeitung der semiotischen Daten für die Kundenansicht.
*   **API-Layer:** Abstraktion via **TanStack Query** (React Query) für effizientes Caching und Loading-States.

---

## 4. Technische Anforderungen (Stack)

*   **Styling:** **Tailwind CSS**. Fokus auf ein hochwertiges "Professional Dark Mode" Design (Slate/Zinc Paletten mit Akzentfarben).
*   **Daten-Visualisierung:** **D3.js** oder **Recharts**. Erforderlich für die Darstellung des VAD-Drifts und der Sprecher-Interaktion.
*   **Highlighting Engine:** Algorithmus zur Handhabung von verschachtelten Spans. Wenn ein ATO-Marker Teil eines SEM-Markers ist, muss die UI dies durch abgestufte Unterstreichungen oder Hover-Effekte verdeutlichen.
*   **Reaktivität:** Debounced Re-Analysis während der Texteingabe (< 300ms Delay).
*   **Client-Side Security:** Keine Speicherung von sensiblen Chat-Daten auf dem Server ohne explizite Anforderung (Privacy by Design).

---

## 5. Abgrenzung zur Version 5.0
*   **KEIN Güdelsatz:** Der Begriff ist für Kunden zu abstrakt. Die Logik wird in das "Beziehungsmuster" integriert.
*   **KEIN technisches Jargon:** Begriffe wie "Peirce-Klassifikation" oder "Abduktion" werden hinter Icons oder Tooltips versteckt; primär zählt die psychologische Deutung.
*   **Fokus auf Veränderung:** Visualisierung von emotionalen Wendepunkten (Inflection Points) direkt im Zeitverlauf.
