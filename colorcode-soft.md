## 1) Color Tokens

### Neutrals

`color.neutral.bg` — **#F6F5F3** (Canvas)

`color.neutral.surface` — **#FFFFFF** (Cards, Panels)

`color.neutral.surfaceElevated` — **#FBFAF8** (Hover/Sheets)

`color.neutral.border` — **#E6E3DF** (Dividers/Outlines)

`color.text.primary` — **#1F2430** (Haupttext)

`color.text.secondary` — **#4B5563** (Sekundärtext)

`color.text.muted` — **#6B7280** (Hints/Meta)

`color.focus.ring` — **#7C6FF2** (sichtbarer Fokus, nicht rot)

### Layer (ATO / SEM / CLU / MEMA)

Jeder Layer hat: **accent** (Controls/Badges), **border** (Outline), **soft** (Chips/States), **tint** (Interpretationsraum/Highlight), **wash** (große Flächen, sehr transparent).

**ATO (Observation) – warm coral**

`color.layer.ato.accent` — **#F26B63**

`color.layer.ato.border` — **#F9BCB9**

`color.layer.ato.soft` — **#FBD6D3**

`color.layer.ato.tint` — **#FDE4E3**

`color.layer.ato.wash` — **rgba(242,107,99,0.18)**

**SEM (Meaning) – lavender/indigo**

`color.layer.sem.accent` — **#7C6FF2**

`color.layer.sem.border` — **#C4BEF9**

`color.layer.sem.soft` — **#DAD7FB**

`color.layer.sem.tint` — **#E7E5FD**

`color.layer.sem.wash` — **rgba(124,111,242,0.18)**

**CLU (Clustering/Patterns) – aqua/teal**

`color.layer.clu.accent` — **#3FBCC1**

`color.layer.clu.border` — **#A9E1E3**

`color.layer.clu.soft` — **#C9ECEE**

`color.layer.clu.tint` — **#DCF3F4**

`color.layer.clu.wash` — **rgba(63,188,193,0.18)**

**MEMA (Meta) – soft amber**

`color.layer.mema.accent` — **#F2B35C**

`color.layer.mema.border` — **#F9DDB6**

`color.layer.mema.soft` — **#FBEAD1**

`color.layer.mema.tint` — **#FDF1E2**

`color.layer.mema.wash` — **rgba(242,179,92,0.18)**

**Nutzungsregel (wichtig für Lesbarkeit):**

Text bleibt fast immer `color.text.primary`.

Interpretationsräume im Text: **tint/wash** als Hintergrund + optional **1px border** (Layer border) – niemals farbigen Text auf farbigem Hintergrund erzwingen.

---

## 2) Radii Tokens (weich, keine harten Ecken)

`radius.sm` — **16px** (Chips, kleine Cards)

`radius.md` — **24px** (Standard Panels, Modals)

`radius.lg` — **28px** (Hero Cards / große Container)

optional praktisch: `radius.full` — **999px** (Pills)

---

## 3) Shadow Tokens (2 Stufen, sehr soft)

**Shadow 1 – Card/Control (Default)**

`shadow.1` — **0 6px 20px rgba(31,36,48,0.10), 0 1px 2px rgba(31,36,48,0.06)**

**Shadow 2 – Overlay/Modal (Elevated)**

`shadow.2` — **0 16px 50px rgba(31,36,48,0.14), 0 4px 10px rgba(31,36,48,0.08)**

**Regel:** Keine harten Drop-Shadows, lieber **2-lagig** + niedrige Opacity, damit Pastell “luftig” bleibt.

---

## 4) Typo Tokens (H1/H2/Body/Caption)

**Font Families**

`type.font.sans` — **Inter** (Fallback: system-ui)

`type.font.mono` — **ui-monospace** (für IDs/Exports/Codefragmente)

**Scale**

`type.h1` — **28px / 36px**, weight **650**, letter-spacing **-0.01em**

`type.h2` — **20px / 28px**, weight **600**, letter-spacing **-0.005em**

`type.body` — **16px / 26px**, weight **450** (oder 400), letter-spacing **0**

`type.caption` — **13px / 18px**, weight **500**, letter-spacing **0.01em**

**Lesbarkeitsregel:** Body-Line-Height **≥ 1.6** (hier 26/16 = 1.625), damit lange Annotierungs-Sessions angenehm bleiben.
