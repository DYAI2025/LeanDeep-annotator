# LeanDeep Frontend 6.0 — Master Entwicklungsplan

Dieses Dokument beschreibt die Zusammenführung der Prototypen `e0z4ZRJ` (Dashboard & Rahmen) und `q8RPdK_` (Analyse-Deep-Dive) zu einer produktionsreifen LeanDeep 6.0 Web-Applikation.

## 1. Architektur-Vision
Wir bauen eine **Single-Page-Application (SPA)** auf Basis von **React (Next.js)**, die zwei Hauptmodi bietet:
1.  **Observability Mode:** Überwachung der Marker-Aktivität und System-Statistiken (Basis: `e0z4ZRJ`).
2.  **Clinical/Analysis Mode:** Detail-Untersuchung von Gesprächen mit Fokus auf Beziehungsmuster (Basis: `q8RPdK_`).

---

## 2. Komponenten-Mapping

### 2.1 Der äußere Rahmen (Shell) — Aus `e0z4ZRJ`
*   **Sidebar:** Navigation zwischen Dashboard, Analyse, Persona-Management und API-Docs.
*   **Topbar:** Status-Anzeigen (DSGVO-Konformität, System-Gesundheit), Benachrichtigungen und User-Profil.
*   **Globaler State:** Nutzung von **Zustand** (aus `q8RPdK_` übernommen) zur Verwaltung der aktiven Layer und der Route.

### 2.2 Dashboard (Overview) — Aus `e0z4ZRJ`
*   **Activity-Chart:** Visualisierung der Marker-Frequenz über Zeit.
*   **Layer-KPIs:** Zusammenfassung der Trefferraten pro Ebene (ATO, SEM, CLU, MEMA).
*   **Recent Analysis:** Liste der zuletzt verarbeiteten Texte als Einstiegspunkte.

### 2.3 Analyse-Modul (Herzstück) — Aus `q8RPdK_`
*   **3-Spalten-Layout:**
    *   **Links (Filter):** Layer-Toggles mit konsistenter Farbcodierung.
    *   **Mitte (Transcript):** Der Konversations-Flow mit der intelligenten Highlighting-Engine für überlappende Marker.
    *   **Rechts (Details):** Das Slide-in Panel für psychologische Deutungen, Confidence-Scores und Interventionsstrategien.
*   **VAD-Integration:** Erweiterung der Mitte oder Spalte 3 um das VAD-Koordinatensystem (aus den ursprünglichen Anforderungen).

---

## 3. Technischer Implementierungspfad

### Phase 1: Setup & Shell (Woche 1)
*   Initialisierung Next.js + Tailwind CSS.
*   Implementierung der Sidebar und Topbar Logik aus `e0z4ZRJ/app.js`.
*   Einrichtung des Zustand-Stores (`store.js` aus `q8RPdK_`).

### Phase 2: Transkript & Highlighting (Woche 2)
*   Portierung der `renderTranscript`-Logik aus `q8RPdK_/components.js`.
*   Entwicklung des Highlighting-Algorithmus für verschachtelte Marker (Deduplizierung auf UI-Ebene).
*   Anbindung der `/v1/analyze/conversation` API.

### Phase 3: Psychologische Insights (Woche 3)
*   Implementierung des rechten Detail-Panels.
*   Mapping der `interpret.py`-Response auf die UI-Komponenten (Beziehungsmuster, Bias-Check, Resilienz-Profil).
*   Integration der VAD-Space Visualisierung (D3.js).

### Phase 4: Dashboard & Polishing (Woche 4)
*   Vervollständigung der Dashboard-Metriken.
*   Implementierung von Dark Mode / Light Mode Support.
*   Finales Testing gegen den Gold-Corpus.

---

## 4. Design-Konventionen (Theming)
*   **ATO:** Gelb (#FACC15) — Fokus auf Rohsignale.
*   **SEM:** Orange (#FB923C) — Fokus auf Kontext.
*   **CLU:** Türkis (#2DD4BF) — Fokus auf Sequenz.
*   **MEMA:** Violett (#A855F7) — Fokus auf Diagnose.
*   **Background:** Slate-950 (Dark) / Slate-50 (Light).

## 5. Datei-Referenzen im Repo
*   Logik-Referenz Dashboard: `masterplan/e0z4ZRJ/`
*   Logik-Referenz Analyse: `masterplan/q8RPdK_/`
*   Anforderungsliste: `FRONTEND_REQUIREMENTS_V6.md`
