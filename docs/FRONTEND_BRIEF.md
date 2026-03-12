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

Eine Web-App unter leandeep.de die es Nutzern ermoeglicht, Texte und Konversationen zu analysieren, Ergebnisse visuell aufbereitet zu sehen, und ueber Zeit Persona-Profile aufzubauen. Design und Usability muessen herausragend sein — das Frontend IST das Produkt.

---

## Tech-Stack

| Komponente | Technologie |
|---|---|
| Framework | Next.js 15 (App Router) |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| Charts | Recharts oder tremor.so |
| Deployment | Vercel (Custom Domain: leandeep.de) |
| API Backend | Bestehende REST API (https://leandeep.fly.dev) |
| Auth | Noch nicht noetig (kommt spaeter) |

---

## Seiten / Views

### 1. Landing Page (`/`)

**Zweck:** Erklaeren was LeanDeep kann, direkt ausprobieren lassen.

- Hero-Bereich: Headline + Subline + CTA "Text analysieren"
- Inline-Demo: Textfeld mit Beispieltext vorbelegt, "Analysieren"-Button
- Ergebnis erscheint direkt darunter (kein Seitenwechsel)
- 3-4 Feature-Cards: Was LeanDeep erkennt (Emotionsmuster, Manipulation, Beziehungsgesundheit, Kommunikationsstile)
- Footer: Impressum, Datenschutz, API-Docs Link

### 2. Einzeltext-Analyse (`/analyze`)

**Zweck:** Einen einzelnen Text analysieren.

**API:** `POST /v1/analyze`

**Input:**
- Grosses Textfeld (Placeholder: "Fuege hier einen Text ein...")
- Confidence-Slider (Standard 0.5, Range 0.0-1.0)
- Button "Analysieren"

**Output:**
- **Zusammenfassung oben:** X Muster erkannt, Verarbeitungszeit
- **Marker-Cards:** Jeder erkannte Marker als Karte:
  - Marker-Name in menschenlesbarer Form (nicht `CLU_GASLIGHTING_SEQUENCE` sondern "Gaslighting-Sequenz")
  - Kurzbeschreibung was das bedeutet
  - Konfidenz als visueller Balken
  - Layer-Badge (ATO/SEM/CLU/MEMA) farblich kodiert
  - Aufklappbar: gematchter Text hervorgehoben im Original
- **Sortierung:** Nach Konfidenz absteigend
- **Filter:** Nach Layer (ATO/SEM/CLU/MEMA)

### 3. Konversations-Analyse (`/conversation`)

**Zweck:** Einen Chat (WhatsApp-Export, Therapiesitzung, etc.) analysieren.

**API:** `POST /v1/analyze/dynamics`

**Input:**
- Chat-Upload: Copy-Paste Textfeld ODER Datei-Upload (.txt)
- Automatische Erkennung von Sprechern (A/B oder Namen)
- Alternativ: Manuell Nachrichten eingeben (Rolle + Text, Zeilen hinzufuegen)
- Button "Konversation analysieren"

**Output — 4 Tabs:**

**Tab 1: Uebersicht**
- Anzahl Nachrichten, Sprecher, erkannte Marker
- Top 5 Marker als grosse Karten (wie Einzelanalyse)
- Beziehungs-Score: Trust / Conflict / Deeskalation als 3 Gauges oder Balken

**Tab 2: Emotionsverlauf**
- Linien-Chart (X-Achse: Nachricht-Index, Y-Achse: Wert)
  - Linie 1: Valenz (positiv/negativ)
  - Linie 2: Arousal (aktiviert/ruhig)
  - Linie 3: Dominanz (dominant/submissiv)
- Pro Sprecher farblich getrennt
- Hover ueber Datenpunkt zeigt die Nachricht

**Tab 3: Marker-Timeline**
- Horizontale Timeline (X-Achse: Nachrichten)
- Jeder Marker als farbiger Punkt/Balken an der Position wo er auftritt
- Farbkodierung nach Layer
- Klick auf Marker zeigt Detail-Card

**Tab 4: Alle Marker**
- Vollstaendige Marker-Liste wie bei Einzelanalyse
- Zusaetzlich: In welchen Nachrichten erkannt (message_indices)
- Temporal Patterns: "Steigend", "Fallend", "Stabil"

### 4. Persona-Dashboard (`/persona`) — Pro Tier

**Zweck:** Laengerfristige Analyse ueber mehrere Sessions.

**APIs:**
- `POST /v1/personas` (erstellen)
- `GET /v1/personas/{token}` (Profil laden)
- `POST /v1/analyze/dynamics` mit `persona_token` (Session analysieren)
- `GET /v1/personas/{token}/predict` (Vorhersagen)

**Ansicht:**
- Persona erstellen oder per Token laden
- Session-History: Liste bisheriger Sessions mit Datum und Kurzstatus
- EWMA-Verlauf: Langzeit-Emotionstrend ueber Sessions als Chart
- Episoden-Timeline: Farbkodierte Balken (Rot=Eskalation, Gruen=Repair, Grau=Rueckzug, Orange=Ruptur, Blau=Stabilisierung)
- Vorhersage-Widget: Wahrscheinlichkeiten fuer naechste Shifts als Donut-Chart oder Balken
- Neue Session analysieren: Chat eingeben, wird der Persona zugeordnet

### 5. API-Dokumentation (`/developers`)

**Zweck:** Entwickler-orientierte Seite fuer API-Integration.

- Weiterleitung auf OpenAPI-Docs oder eigene schoene Docs-Seite
- MCP-Server Konfiguration erklaeren
- Code-Beispiele (curl, Python, JavaScript)

---

## Design-Anforderungen

### Farbschema

| Rolle | Farbe | Verwendung |
|---|---|---|
| Primaer | Indigo/Violett (#6366f1 Bereich) | Buttons, Links, Akzente |
| Sekundaer | Warmgrau (#78716c Bereich) | Text, Hintergruende |
| Hintergrund | Off-White (#fafaf9) | Seitengrund |
| Surface | Weiss (#ffffff) | Karten, Panels |
| Erfolg/Positiv | Sanftes Gruen (#22c55e) | Repair, Trust, positive Marker |
| Warnung | Amber (#f59e0b) | Mittlere Konfidenz, Hinweise |
| Kritisch | Gedaempftes Rot (#ef4444) | Manipulation, Eskalation, kritische Marker |
| ATO-Layer | Blau (#3b82f6) | ATO-Badges |
| SEM-Layer | Violett (#8b5cf6) | SEM-Badges |
| CLU-Layer | Orange (#f97316) | CLU-Badges |
| MEMA-Layer | Rot (#ef4444) | MEMA-Badges |

### Typografie

- Headlines: Inter oder Geist (clean, modern)
- Body: System-Font-Stack oder Inter
- Monospace fuer Marker-IDs: JetBrains Mono oder Fira Code
- Groessen: Klare Hierarchie, grosszuegige Line-Height

### Design-Prinzipien

1. **Weniger ist mehr:** Nicht alle 848 Marker auf einmal zeigen. Top 5 gross, Rest auf Klick.
2. **Storytelling:** Marker-Namen menschenlesbar uebersetzen. "Wiederholte Rueckversicherung" statt "CLU_REASSURANCE_SEEKING_LOOP".
3. **Weissraum:** Grosszuegig. Karten mit Padding, kein visuelles Gedraenge.
4. **Animationen:** Subtil. Ergebnisse faden in, Charts bauen sich auf. Keine Spielereien.
5. **Mobile-first:** Coaches schauen zwischen Sessions aufs Handy. Alles muss ab 375px funktionieren.
6. **Dark Mode:** Optional, aber von Anfang an mit Tailwind dark: Klassen vorbereiten.
7. **Vertrauen signalisieren:** "Made in Germany", "Keine KI", "Daten werden nicht gespeichert", DSGVO-konform. Dezent aber sichtbar im Footer oder als Badge.

### Lesbarer Marker-Name

Das Frontend soll Marker-IDs in menschenlesbare deutsche Labels uebersetzen. Mapping-Tabelle aus dem `description`-Feld der API oder als separates JSON im Frontend:

```
CLU_GASLIGHTING_SEQUENCE    → "Gaslighting-Sequenz"
CLU_REASSURANCE_SEEKING_LOOP → "Wiederholte Rueckversicherung"
SEM_REPAIR_GESTURE          → "Reparatur-Geste"
ATO_DEPRESSION_SELF_FOCUS   → "Selbstfokus (Depression)"
```

Fallback wenn kein Label: ID ohne Prefix, Underscores durch Leerzeichen.

---

## API-Anbindung

**Base URL:** `https://leandeep.fly.dev` (spaeter eigene Domain)

**Alle Endpoints brauchen:**
- `Content-Type: application/json`
- Kein Auth-Header noetig (wird spaeter ergaenzt)

**Wichtigste Requests:**

```typescript
// Einzeltext
const result = await fetch('/v1/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "...",
    threshold: 0.5,
    layers: ["ATO", "SEM", "CLU", "MEMA"]
  })
});

// Konversation mit Dynamics
const result = await fetch('/v1/analyze/dynamics', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [
      { role: "A", text: "..." },
      { role: "B", text: "..." }
    ],
    threshold: 0.5,
    persona_token: null  // oder UUID fuer Pro
  })
});
```

**Response-Struktur:** Vollstaendige Schemas unter https://leandeep.fly.dev/docs

---

## Chat-Parser

Das Frontend braucht einen Client-seitigen Parser fuer Copy-Paste Chat-Exports:

**WhatsApp-Format:**
```
21.02.26, 14:32 - Anna: Ich verstehe nicht was du meinst
21.02.26, 14:33 - Ben: Das ist doch offensichtlich
```

**Generisches Format:**
```
A: Ich verstehe nicht was du meinst
B: Das ist doch offensichtlich
```

Parser extrahiert `role` und `text`, erstellt `messages`-Array fuer die API.

---

## Nicht im Scope (kommt spaeter)

- User-Accounts / Login
- Bezahl-Integration (Stripe)
- Multi-Language (erstmal nur Deutsch)
- Admin-Panel
- WebSocket/Live-Analyse
- SEO-Optimierung (erstmal funktional)

---

## Abnahmekriterien

1. Alle 5 Seiten funktionieren und sind responsiv (Desktop + Mobile)
2. Analyse-Ergebnisse werden innerhalb von 2 Sekunden angezeigt
3. Charts rendern korrekt fuer Konversationen mit 2-200 Nachrichten
4. Design folgt dem beschriebenen Farbschema und den Prinzipien
5. Lighthouse Performance Score >= 90
6. Deployment auf Vercel funktioniert, leandeep.de zeigt die App
7. Chat-Parser erkennt WhatsApp-Format und generisches A/B-Format
