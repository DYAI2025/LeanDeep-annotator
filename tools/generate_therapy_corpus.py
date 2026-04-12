#!/usr/bin/env python3
"""Template-Replay Dialog Generator for LeanDeep 6.0 Gold Standard Corpus.

Generates 50 simulated German therapy dialogues (5 per theme, 10 themes)
using phase templates, marker co-occurrence data, and VAD profiles.

Two paths:
  A) LLM generation via Gemini (if LEANDEEP_GOOGLE_API_KEY is set)
  B) Offline/heuristic generation (always works, no API needed)

Usage:
    uv run python3 tools/generate_therapy_corpus.py --output-dir build/eval/corpus/simulated/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root (works from repo root or tools/ directory)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_TEMPLATES_DIR = _PROJECT_ROOT / "build" / "eval" / "templates"
_SCHEMA_PATH = _PROJECT_ROOT / "build" / "eval" / "schema" / "dialog_schema.json"

# ---------------------------------------------------------------------------
# Phase dialogue bank — canned German therapeutic phrases per phase
# ---------------------------------------------------------------------------
PHASE_DIALOGUES: dict[str, list[tuple[str, str]]] = {
    "Containment": [
        ("Client", "Ich weiss nicht, wo ich anfangen soll heute."),
        ("Therapist", "Nehmen Sie sich die Zeit, die Sie brauchen. Was beschaeftigt Sie gerade am meisten?"),
        ("Client", "Es ist alles so viel gerade. Ich fuehle mich ueberwaeltigt."),
        ("Therapist", "Das hoert sich belastend an. Lassen Sie uns gemeinsam schauen, was gerade am draengendsten ist."),
    ],
    "Koerpersignal": [
        ("Client", "Mein Koerper fuehlt sich ganz schwer an, besonders in der Brust."),
        ("Therapist", "Koennen Sie mir beschreiben, was Sie koerperlich wahrnehmen?"),
        ("Client", "Es ist wie ein Druck. Und mein Kopf fuehlt sich benebelt an."),
        ("Therapist", "Mhm. Der Koerper speichert manchmal das, was wir noch nicht in Worte fassen koennen."),
    ],
    "Scham_Fassade": [
        ("Client", "Ich zeige nie, wie es mir wirklich geht. Alle denken, mir geht es gut."),
        ("Therapist", "Was wuerde passieren, wenn jemand sehen wuerde, wie es Ihnen wirklich geht?"),
        ("Client", "Dann wuerden sie mich fuer schwach halten. Das kann ich nicht ertragen."),
        ("Therapist", "Es klingt, als ob die Fassade Sie schuetzt, aber gleichzeitig auch sehr einsam macht."),
    ],
    "Selbstwert_Shift": [
        ("Client", "Vielleicht bin ich doch nicht so wertlos, wie ich immer dachte."),
        ("Therapist", "Was hat sich veraendert, dass Sie das jetzt so sehen koennen?"),
        ("Client", "Letzte Woche hat mir jemand gesagt, dass er mich schaetzt. Das hat mich sehr beruehrt."),
        ("Therapist", "Das ist ein wichtiger Moment. Sie erlauben sich, das anzunehmen."),
    ],
    "Ressource": [
        ("Client", "Eigentlich bin ich ganz gut darin, Probleme zu loesen. Das vergesse ich manchmal."),
        ("Therapist", "Was sind denn Situationen, in denen Sie das gut koennen?"),
        ("Client", "Auf der Arbeit zum Beispiel. Da bin ich die, die immer Loesungen findet."),
        ("Therapist", "Das klingt nach einer echten Staerke. Wie koennten Sie die auch hier nutzen?"),
    ],
    "Vermeidung": [
        ("Client", "Ich gehe bestimmten Situationen einfach aus dem Weg. Das ist einfacher."),
        ("Therapist", "Was genau vermeiden Sie, und was befuerchten Sie dabei?"),
        ("Client", "Menschenmengen, oeffentliche Verkehrsmittel... Ich habe Angst, die Kontrolle zu verlieren."),
        ("Therapist", "Die Vermeidung gibt Ihnen kurzfristig Sicherheit, aber langfristig wird der Radius kleiner."),
    ],
    "Exposition_Andeutung": [
        ("Client", "Vielleicht koennte ich ja mal versuchen, mit dem Bus zu fahren. Nur eine Station."),
        ("Therapist", "Das waere ein mutiger Schritt. Was brauchten Sie dafuer?"),
        ("Client", "Jemanden, der mitkommt. Alleine schaffe ich das noch nicht."),
        ("Therapist", "Das ist voellig in Ordnung. Wir gehen in Ihrem Tempo."),
    ],
    "Pace_Regulation": [
        ("Client", "Das wird mir gerade zu viel. Koennen wir kurz pausieren?"),
        ("Therapist", "Natuerlich. Atmen Sie einmal tief durch. Wir machen weiter, wenn Sie bereit sind."),
        ("Client", "Danke. Ich merke, dass mein Herz schneller schlaegt."),
        ("Therapist", "Gut, dass Sie das wahrnehmen. Das ist ein wichtiges Signal Ihres Koerpers."),
    ],
    "Eroeffnung": [
        ("Client", "Letzte Woche ist etwas passiert, darueber moechte ich heute sprechen."),
        ("Therapist", "Ich hoere Ihnen zu. Erzaehlen Sie mir, was vorgefallen ist."),
        ("Client", "Es geht um einen Streit mit meinem Partner. Das hat mich sehr aufgewaehlt."),
        ("Therapist", "Lassen Sie uns das gemeinsam anschauen. Was genau ist passiert?"),
    ],
    "Konflikt_Schilderung": [
        ("Client", "Er hat mir vorgeworfen, dass ich nie zuhoere. Dabei hoere ich staendig zu!"),
        ("Therapist", "Wie haben Sie sich in dem Moment gefuehlt?"),
        ("Client", "Wuetend und unverstanden. Ich mache doch so viel fuer uns."),
        ("Therapist", "Es klingt, als fuehlen Sie sich in Ihren Bemuehungen nicht gesehen."),
    ],
    "Muster_Erkennung": [
        ("Client", "Jetzt wo ich darueber nachdenke... das kommt immer wieder vor."),
        ("Therapist", "Was genau wiederholt sich da?"),
        ("Client", "Ich gebe und gebe, und dann werde ich wuetend, wenn nichts zurueckkommt."),
        ("Therapist", "Da scheint ein Muster zu sein: Aufopferung, dann Enttaeuschung, dann Rueckzug."),
    ],
    "Perspektivwechsel": [
        ("Client", "Vielleicht hat er ja auch recht, dass ich manchmal abwesend bin."),
        ("Therapist", "Was meinen Sie damit? Koennen Sie sich in seine Perspektive versetzen?"),
        ("Client", "Er will wahrscheinlich einfach, dass ich praesent bin. Nicht nur koerperlich."),
        ("Therapist", "Das ist ein wichtiger Unterschied. Praesenz bedeutet mehr als Anwesenheit."),
    ],
    "Handlungsplan": [
        ("Client", "Ich koennte ihm mal direkt sagen, was ich brauche, statt es zu schlucken."),
        ("Therapist", "Wie koennte das konkret aussehen?"),
        ("Client", "Vielleicht so: Ich brauche, dass du mich fragst, wie mein Tag war."),
        ("Therapist", "Das klingt klar und respektvoll. Wollen Sie das diese Woche ausprobieren?"),
    ],
    "Herkunftsraum": [
        ("Client", "Bei uns zuhause wurde nie ueber Gefuehle gesprochen."),
        ("Therapist", "Wie war das fuer Sie als Kind?"),
        ("Client", "Ich habe gelernt, dass man funktionieren muss. Weinen war nicht erlaubt."),
        ("Therapist", "Das klingt nach einem sehr engen Rahmen fuer ein Kind."),
    ],
    "Bindungsmuster": [
        ("Client", "Ich halte Menschen immer auf Abstand. Naeher als bis hierhin kommt niemand."),
        ("Therapist", "Wann haben Sie angefangen, sich so zu schuetzen?"),
        ("Client", "Schon als Kind. Meine Mutter war unberechenbar. Mal liebevoll, mal eiskalt."),
        ("Therapist", "Das macht Sinn, dass Sie dann gelernt haben, Naehe als gefaehrlich zu erleben."),
    ],
    "Abloesung": [
        ("Client", "Ich muss mich nicht mehr dafuer verantwortlich fuehlen, ob es meiner Mutter gut geht."),
        ("Therapist", "Was veraendert sich, wenn Sie diesen Gedanken zulassen?"),
        ("Client", "Ich fuehle mich leichter. Aber auch schuldig."),
        ("Therapist", "Beides darf da sein. Abloesung bedeutet nicht Lieblosigkeit."),
    ],
    "Eigenverantwortung": [
        ("Client", "Ich kann nicht mein ganzes Leben damit verbringen, andere zu retten."),
        ("Therapist", "Was moechten Sie stattdessen fuer sich tun?"),
        ("Client", "Meine eigenen Beduerfnisse ernst nehmen. Das faellt mir noch schwer."),
        ("Therapist", "Es ist ein Prozess. Aber Sie haben bereits angefangen, sich selbst wahrzunehmen."),
    ],
    "Stabilisierung": [
        ("Client", "Ich brauche heute erst mal einen sicheren Boden."),
        ("Therapist", "Lassen Sie uns mit einer Uebung beginnen. Spueren Sie Ihre Fuesse auf dem Boden."),
        ("Client", "Ja, das hilft. Ich fuehle mich schon etwas ruhiger."),
        ("Therapist", "Gut. Dieser sichere Ort ist immer da, auch wenn es stuermisch wird."),
    ],
    "Annaeherung": [
        ("Client", "Es gibt da eine Erinnerung, die mich immer wieder einholt."),
        ("Therapist", "Moechten Sie mir davon erzaehlen? Nur so weit, wie es sich sicher anfuehlt."),
        ("Client", "Es war nachts. Ich war allein. Ich hoerte Schritte und konnte mich nicht bewegen."),
        ("Therapist", "Danke, dass Sie mir das anvertrauen. Wie geht es Ihnen gerade, wenn Sie das sagen?"),
    ],
    "Affektbruecke": [
        ("Client", "Dieses Gefuehl... das kenne ich. Das ist wie damals, als ich klein war."),
        ("Therapist", "Es gibt also eine Bruecke zwischen dem Jetzt und dem Damals?"),
        ("Client", "Ja. Dieselbe Hilflosigkeit. Dieselbe Enge in der Brust."),
        ("Therapist", "Ihr Koerper erinnert sich. Aber Sie sind heute nicht mehr das kleine Kind. Sie sind hier, und Sie sind sicher."),
    ],
    "Reorientierung": [
        ("Client", "Stimmt. Ich bin jetzt hier. In diesem Raum. Bei Ihnen."),
        ("Therapist", "Genau. Schauen Sie sich um. Was sehen Sie?"),
        ("Client", "Die Pflanze am Fenster. Das Bild an der Wand. Ihren Stuhl."),
        ("Therapist", "Sehr gut. Sie sind im Hier und Jetzt. Das Damals ist vorbei."),
    ],
    "Ausloeser": [
        ("Client", "Es hat mit einem Kommentar meines Chefs angefangen. Da bin ich explodiert."),
        ("Therapist", "Was genau hat er gesagt, und was hat das in Ihnen ausgeloest?"),
        ("Client", "Er sagte, ich waere nicht belastbar genug. Das hat mich rasend gemacht."),
        ("Therapist", "Was an diesem Satz war so schmerzhaft?"),
    ],
    "Eskalationskette": [
        ("Client", "Erst war ich still, dann habe ich die Tuer zugeschlagen, dann habe ich geschrien."),
        ("Therapist", "Koennen Sie erkennen, wann der Punkt war, an dem es kippte?"),
        ("Client", "Als er den Kopf geschuettelt hat. Das war wie ein Schalter."),
        ("Therapist", "Dieses Kopfschuetteln scheint eine starke Bedeutung fuer Sie zu haben."),
    ],
    "Regulation": [
        ("Client", "Ich weiss nicht, wie ich mich beruhigen soll, wenn die Wut kommt."),
        ("Therapist", "Was haben Sie bisher versucht?"),
        ("Client", "Rausgehen, laufen. Aber manchmal hilft auch das nicht."),
        ("Therapist", "Lassen Sie uns gemeinsam schauen, was noch helfen koennte. Wie ist es mit bewusstem Atmen?"),
    ],
    "Beduerfnis_dahinter": [
        ("Client", "Eigentlich will ich nur, dass man mich respektiert."),
        ("Therapist", "Was bedeutet Respekt fuer Sie ganz konkret?"),
        ("Client", "Dass man mich anhoert. Dass meine Meinung zaehlt."),
        ("Therapist", "Hinter der Wut steckt also ein tiefes Beduerfnis nach Anerkennung und Gehoertwerden."),
    ],
    "Verlust_benennen": [
        ("Client", "Mein Vater ist vor drei Monaten gestorben. Ich... ich kann es immer noch nicht fassen."),
        ("Therapist", "Das tut mir leid. Moegen Sie mir erzaehlen, wie das fuer Sie ist?"),
        ("Client", "Es fuehlt sich unwirklich an. Als waere er nur verreist und kommt bald zurueck."),
        ("Therapist", "Das ist eine ganz normale Reaktion. Die Realitaet braucht Zeit, um anzukommen."),
    ],
    "Erinnerung": [
        ("Client", "Ich erinnere mich an seine Haende. Wie er mir als Kind Geschichten erzaehlt hat."),
        ("Therapist", "Was fuer Geschichten waren das?"),
        ("Client", "Von Abenteuern, die er sich ausgedacht hat. Nur fuer mich. Das war unsere Zeit."),
        ("Therapist", "Diese Erinnerungen gehoeren Ihnen. Niemand kann sie Ihnen nehmen."),
    ],
    "Sinnfrage": [
        ("Client", "Was bleibt, wenn jemand geht? Was hat das alles fuer einen Sinn?"),
        ("Therapist", "Das sind grosse Fragen. Was kommt Ihnen als Erstes in den Sinn?"),
        ("Client", "Vielleicht, dass ich so lebe, wie er es sich fuer mich gewuenscht haette."),
        ("Therapist", "Das klingt wie eine Art innerer Auftrag. Fuehlt sich das stimmig an?"),
    ],
    "Weiterleben": [
        ("Client", "Ich glaube, ich darf auch wieder lachen. Das waere okay."),
        ("Therapist", "Was glauben Sie, wuerde Ihr Vater dazu sagen?"),
        ("Client", "Er wuerde sagen: Natuerlich! Das Leben geht weiter, mein Schatz."),
        ("Therapist", "Da ist ein Laecheln. Trauer und Freude schliessen sich nicht aus."),
    ],
    "Ambivalenz": [
        ("Client", "Ein Teil von mir will aufhoeren. Aber ein anderer Teil will einfach nicht."),
        ("Therapist", "Beide Teile haben ihre Gruende. Was sagt der Teil, der nicht aufhoeren will?"),
        ("Client", "Dass es mir hilft. Dass ich sonst den Stress nicht aushalte."),
        ("Therapist", "Es gibt also eine Funktion dahinter. Das ist wichtig zu verstehen."),
    ],
    "Funktionsanalyse": [
        ("Client", "Wenn ich trinke, wird alles leiser. Der Druck, die Gedanken."),
        ("Therapist", "Was genau wird leiser?"),
        ("Client", "Die Stimme, die sagt, dass ich nicht genuege. Die Angst, zu versagen."),
        ("Therapist", "Der Alkohol uebernimmt also eine Funktion, die eigentlich andere Strategien braucht."),
    ],
    "Alternativen": [
        ("Client", "Was soll ich denn stattdessen machen, wenn alles zu viel wird?"),
        ("Therapist", "Lassen Sie uns gemeinsam schauen. Was hat Ihnen frueher geholfen?"),
        ("Client", "Sport vielleicht. Oder Musik hoeren. Das habe ich lange nicht mehr gemacht."),
        ("Therapist", "Das klingt nach Dingen, die Sie kennen und die funktioniert haben. Koennen wir damit anfangen?"),
    ],
    "Commitment": [
        ("Client", "Ich will es versuchen. Eine Woche ohne. Mal sehen, ob ich das schaffe."),
        ("Therapist", "Das ist ein konkreter Vorsatz. Was koennte Ihnen dabei helfen?"),
        ("Client", "Vielleicht ein Tagebuch. Aufschreiben, wann der Drang kommt und was ich stattdessen tue."),
        ("Therapist", "Ein sehr guter Plan. Wir schauen uns das naechste Woche zusammen an."),
    ],
    "Selbstbild": [
        ("Client", "Ich sehe mich immer als den Starken, der alles alleine schafft."),
        ("Therapist", "Woher kommt dieses Bild von sich?"),
        ("Client", "Ich musste immer funktionieren. Schwaeche war keine Option."),
        ("Therapist", "Was waere, wenn Staerke auch bedeuten koennte, sich Hilfe zu holen?"),
    ],
    "Fremdbild_Spannung": [
        ("Client", "Meine Freunde sagen, ich sei kalt. Aber innen drin fuehle ich so viel."),
        ("Therapist", "Wie erleben Sie diesen Widerspruch?"),
        ("Client", "Es macht mich traurig. Als waere ich unsichtbar."),
        ("Therapist", "Die Diskrepanz zwischen dem, was innen ist, und dem, was aussen ankommt, scheint schmerzhaft."),
    ],
    "Exploration": [
        ("Client", "Wer bin ich eigentlich, wenn ich nicht die Rolle spiele, die alle erwarten?"),
        ("Therapist", "Haben Sie eine Ahnung davon?"),
        ("Client", "Nein. Und das macht mir Angst. Was wenn da nichts ist?"),
        ("Therapist", "Die Tatsache, dass Sie diese Frage stellen, zeigt mir, dass da sehr wohl etwas ist."),
    ],
    "Authentizitaet": [
        ("Client", "Ich moechte mich trauen, so zu sein, wie ich wirklich bin."),
        ("Therapist", "Was waere ein erster Schritt dahin?"),
        ("Client", "Vielleicht meiner Schwester zu sagen, dass ich auch mal Hilfe brauche."),
        ("Therapist", "Das waere ein mutiger und authentischer Schritt. Was hindert Sie noch?"),
    ],
    "Admin": [
        ("Client", "Bevor wir anfangen... Ich muss naechste Woche unseren Termin verschieben."),
        ("Therapist", "Kein Problem, wir finden einen Ersatztermin. Gibt es sonst noch etwas Organisatorisches?"),
        ("Client", "Nein, das war alles. Danke."),
        ("Therapist", "Gut. Dann wuerde ich gerne etwas ansprechen, das mir letzte Sitzung aufgefallen ist."),
    ],
    "Beziehungsdynamik": [
        ("Client", "Manchmal habe ich das Gefuehl, dass Sie mich nicht wirklich verstehen."),
        ("Therapist", "Das ist wichtig, dass Sie das aussprechen. Was genau gibt Ihnen dieses Gefuehl?"),
        ("Client", "Sie nicken immer, aber ich weiss nicht, ob das echt ist."),
        ("Therapist", "Ich hoere, dass Sie sich nach echter Verbindung sehnen, auch hier in unserer Beziehung."),
    ],
    "Spiegelung": [
        ("Client", "Sie reagieren gerade genauso wie meine Mutter frueher."),
        ("Therapist", "Was genau erinnert Sie an Ihre Mutter?"),
        ("Client", "Diese ruhige Art. Ich weiss nie, was Sie wirklich denken."),
        ("Therapist", "Koennte es sein, dass Sie hier etwas wiederholen, was Sie von frueher kennen?"),
    ],
    "Deutung": [
        ("Client", "Sie meinen, ich suche hier das, was ich zuhause nie bekommen habe?"),
        ("Therapist", "Was denken Sie: Koennte da etwas dran sein?"),
        ("Client", "Ja... wahrscheinlich schon. Ich wuensche mir Bestaetigung, die ich nie gekriegt habe."),
        ("Therapist", "Und genau das koennen wir hier gemeinsam anschauen. Es ist ein sicherer Raum dafuer."),
    ],
    "Boundary": [
        ("Client", "Darf ich Sie eigentlich auch ausserhalb der Sitzung anrufen?"),
        ("Therapist", "Ich verstehe den Wunsch. Unsere gemeinsame Arbeit findet hier in den Sitzungen statt."),
        ("Client", "Das klingt hart. Aber ich verstehe es."),
        ("Therapist", "Der Rahmen schuetzt uns beide und macht diesen Raum ueberhaupt erst moeglich."),
    ],
}

# ---------------------------------------------------------------------------
# Semantic frame defaults per theme
# ---------------------------------------------------------------------------
THEME_SEMANTIC_FRAMES: dict[str, dict[str, Any]] = {
    "selbstwert": {
        "tone": "verletzlich",
        "themes": ["selbstwert", "scham", "identitaet"],
        "relational_dynamics": "Therapist spiegelt Wuerde",
        "intent": "self-exploration",
        "emotional_tenor": -0.1,
        "context_validity": 0.85,
        "offline_context_risk": 0.2,
    },
    "angst": {
        "tone": "aengstlich",
        "themes": ["angst", "vermeidung", "koerper"],
        "relational_dynamics": "Therapist reguliert Tempo",
        "intent": "fear-processing",
        "emotional_tenor": -0.3,
        "context_validity": 0.9,
        "offline_context_risk": 0.15,
    },
    "beziehung": {
        "tone": "konflikthaft",
        "themes": ["beziehung", "kommunikation", "muster"],
        "relational_dynamics": "Therapist fragt nach Mustern",
        "intent": "pattern-recognition",
        "emotional_tenor": -0.1,
        "context_validity": 0.85,
        "offline_context_risk": 0.2,
    },
    "familie": {
        "tone": "nachdenklich",
        "themes": ["familie", "bindung", "herkunft"],
        "relational_dynamics": "Therapist differenziert Bindung von Verstrickung",
        "intent": "family-exploration",
        "emotional_tenor": -0.05,
        "context_validity": 0.8,
        "offline_context_risk": 0.25,
    },
    "trauma": {
        "tone": "belastet",
        "themes": ["trauma", "sicherheit", "koerper"],
        "relational_dynamics": "Therapist haelt Sicherheitsrahmen",
        "intent": "trauma-processing",
        "emotional_tenor": -0.4,
        "context_validity": 0.9,
        "offline_context_risk": 0.1,
    },
    "wut": {
        "tone": "angespannt",
        "themes": ["wut", "kontrolle", "beduerfnisse"],
        "relational_dynamics": "Therapist normalisiert und lenkt auf Beduerfnisse",
        "intent": "anger-regulation",
        "emotional_tenor": -0.2,
        "context_validity": 0.85,
        "offline_context_risk": 0.2,
    },
    "trauer": {
        "tone": "traurig",
        "themes": ["verlust", "abschied", "erinnerung"],
        "relational_dynamics": "Therapist validiert Schmerz",
        "intent": "grief-processing",
        "emotional_tenor": -0.35,
        "context_validity": 0.9,
        "offline_context_risk": 0.15,
    },
    "sucht": {
        "tone": "ambivalent",
        "themes": ["sucht", "ambivalenz", "funktion"],
        "relational_dynamics": "Therapist exploriert Funktion ohne Moralisierung",
        "intent": "addiction-exploration",
        "emotional_tenor": -0.15,
        "context_validity": 0.8,
        "offline_context_risk": 0.3,
    },
    "identitaet": {
        "tone": "suchend",
        "themes": ["identitaet", "authentizitaet", "selbstbild"],
        "relational_dynamics": "Therapist foerdert Selbsterforschung",
        "intent": "identity-exploration",
        "emotional_tenor": 0.0,
        "context_validity": 0.8,
        "offline_context_risk": 0.25,
    },
    "uebertragung": {
        "tone": "geladen",
        "themes": ["uebertragung", "therapeutische_beziehung", "bindung"],
        "relational_dynamics": "Beziehungsdynamik wird zum Material",
        "intent": "transference-work",
        "emotional_tenor": -0.1,
        "context_validity": 0.85,
        "offline_context_risk": 0.2,
    },
}

# ---------------------------------------------------------------------------
# Therapy indices defaults per theme
# ---------------------------------------------------------------------------
THEME_THERAPY_INDICES: dict[str, dict[str, int]] = {
    "selbstwert": {"trust": 75, "conflict": 15, "deescalation": 80, "synchronization": 70, "semiotic_coherence": 65},
    "angst": {"trust": 80, "conflict": 10, "deescalation": 85, "synchronization": 75, "semiotic_coherence": 70},
    "beziehung": {"trust": 70, "conflict": 25, "deescalation": 70, "synchronization": 65, "semiotic_coherence": 60},
    "familie": {"trust": 75, "conflict": 20, "deescalation": 75, "synchronization": 70, "semiotic_coherence": 65},
    "trauma": {"trust": 85, "conflict": 10, "deescalation": 90, "synchronization": 80, "semiotic_coherence": 75},
    "wut": {"trust": 65, "conflict": 30, "deescalation": 65, "synchronization": 60, "semiotic_coherence": 55},
    "trauer": {"trust": 80, "conflict": 10, "deescalation": 80, "synchronization": 75, "semiotic_coherence": 70},
    "sucht": {"trust": 65, "conflict": 20, "deescalation": 70, "synchronization": 60, "semiotic_coherence": 55},
    "identitaet": {"trust": 70, "conflict": 15, "deescalation": 75, "synchronization": 65, "semiotic_coherence": 60},
    "uebertragung": {"trust": 70, "conflict": 25, "deescalation": 70, "synchronization": 65, "semiotic_coherence": 65},
}

# ---------------------------------------------------------------------------
# Semiotic sign templates per theme
# ---------------------------------------------------------------------------
THEME_SEMIOTIC_SIGNS: dict[str, list[dict[str, Any]]] = {
    "selbstwert": [
        {
            "id": "sign-fassade",
            "locus": "early session",
            "signifier": "Fassade",
            "signified": "protection against shame exposure",
            "type": "symbol",
            "denotation": "Mask or front presented to the world",
            "connotations": ["self-protection", "isolation", "shame"],
            "codes": ["psychodynamic"],
            "evidence": "Client describes hiding true feelings",
        }
    ],
    "angst": [
        {
            "id": "sign-enge",
            "locus": "mid session",
            "signifier": "Enge in der Brust",
            "signified": "somatic anxiety expression",
            "type": "index",
            "denotation": "Physical tightness as anxiety marker",
            "connotations": ["threat", "constriction", "fight-or-flight"],
            "codes": ["somatic"],
            "evidence": "Client reports chest tightness",
        }
    ],
    "beziehung": [
        {
            "id": "sign-muster",
            "locus": "mid session",
            "signifier": "Muster",
            "signified": "recurring relational pattern",
            "type": "symbol",
            "denotation": "Repeated behavioral cycle in relationships",
            "connotations": ["repetition", "compulsion", "awareness"],
            "codes": ["systemic"],
            "evidence": "Client recognizes repeating dynamic",
        }
    ],
    "familie": [
        {
            "id": "sign-verstrickung",
            "locus": "mid session",
            "signifier": "Verstrickung",
            "signified": "enmeshment with family of origin",
            "type": "symbol",
            "denotation": "Over-identification with parental role",
            "connotations": ["loyalty", "guilt", "burden"],
            "codes": ["systemic"],
            "evidence": "Client feels responsible for parent",
        }
    ],
    "trauma": [
        {
            "id": "sign-erstarrung",
            "locus": "mid session",
            "signifier": "Erstarrung",
            "signified": "freeze response during trauma recall",
            "type": "index",
            "denotation": "Immobilization as trauma response",
            "connotations": ["helplessness", "dissociation", "survival"],
            "codes": ["trauma-theory"],
            "evidence": "Client describes inability to move during memory",
        }
    ],
    "wut": [
        {
            "id": "sign-schalter",
            "locus": "mid session",
            "signifier": "Schalter",
            "signified": "tipping point in anger escalation",
            "type": "icon",
            "denotation": "Moment where control is lost",
            "connotations": ["trigger", "powerlessness", "explosion"],
            "codes": ["behavioral"],
            "evidence": "Client describes a moment where anger flips",
        }
    ],
    "trauer": [
        {
            "id": "sign-haende",
            "locus": "mid session",
            "signifier": "Haende des Vaters",
            "signified": "embodied memory of deceased",
            "type": "icon",
            "denotation": "Tactile memory as connection to the dead",
            "connotations": ["loss", "love", "permanence"],
            "codes": ["phenomenological"],
            "evidence": "Client recalls father's hands",
        }
    ],
    "sucht": [
        {
            "id": "sign-stille",
            "locus": "mid session",
            "signifier": "Stille im Kopf",
            "signified": "function of substance as silencer",
            "type": "symbol",
            "denotation": "Substance reduces inner noise",
            "connotations": ["relief", "avoidance", "self-medication"],
            "codes": ["functional-analysis"],
            "evidence": "Client describes silence when drinking",
        }
    ],
    "identitaet": [
        {
            "id": "sign-maske",
            "locus": "mid session",
            "signifier": "Rolle",
            "signified": "performed identity vs. authentic self",
            "type": "symbol",
            "denotation": "Social role as substitute for identity",
            "connotations": ["performance", "emptiness", "search"],
            "codes": ["existential"],
            "evidence": "Client questions who they are without their role",
        }
    ],
    "uebertragung": [
        {
            "id": "sign-mutterreaktion",
            "locus": "mid session",
            "signifier": "wie meine Mutter",
            "signified": "transference onto therapist",
            "type": "symbol",
            "denotation": "Therapist experienced as parental figure",
            "connotations": ["projection", "repetition", "attachment"],
            "codes": ["psychodynamic"],
            "evidence": "Client compares therapist to mother",
        }
    ],
}


# ---------------------------------------------------------------------------
# Helper: build the LLM prompt
# ---------------------------------------------------------------------------
def build_generation_prompt(theme: str, template: dict[str, Any]) -> str:
    """Build a prompt for LLM-based dialogue generation."""
    phases_str = " -> ".join(template["phases"])
    return f"""Generate a realistic German therapy dialogue for the theme "{theme}".

Description: {template["description"]}
Phase sequence: {phases_str}
VAD profile type: {template["vad_type"]}
Role dynamics: {template["role_dynamics"]}

Phase details:
- Containment: opening, establishing safety
- {template["phases"][1]}: {template["phases"][1].replace("_", " ")} phase
- {template["phases"][2]}: {template["phases"][2].replace("_", " ")} phase
- {template["phases"][3]}: {template["phases"][3].replace("_", " ")} phase
- {template["phases"][4]}: {template["phases"][4].replace("_", " ")} phase

Requirements:
1. Write 15-20 messages alternating between Client and Therapist
2. All text in German
3. Follow the phase sequence naturally
4. Include emotional shifts matching the VAD profile
5. Include subtle markers for pattern detection

Return JSON with:
- messages: array of {{role, text, start_time}}
- annotations: {{semantic_frame, semiotic_signs, vad_trajectory, expected_markers, therapy_indices, ambiguity_profile}}
"""


# ---------------------------------------------------------------------------
# Helper: parse LLM-generated dialogue into schema-compliant format
# ---------------------------------------------------------------------------
def parse_generated_dialogue(
    raw: dict[str, Any],
    dialog_id: str,
    theme: str,
) -> dict[str, Any]:
    """Parse raw LLM output into a schema-compliant dialogue document."""
    messages = raw.get("messages", [])
    total_chars = sum(len(m.get("text", "")) for m in messages)

    annotations = raw.get("annotations", {})
    # Ensure review_status and rater fields
    annotations.setdefault("review_status", "llm_generated")
    annotations.setdefault("rater_a", None)
    annotations.setdefault("rater_b", None)
    annotations.setdefault("inter_rater_agreement", None)

    return {
        "id": dialog_id,
        "source": "simulated",
        "language": "de",
        "theme": theme,
        "messages": messages,
        "metadata": {
            "generator": "template-replay-v1",
            "template_id": theme,
            "message_count": len(messages),
            "total_chars": total_chars,
            "duration_minutes": len(messages) * 2.0,
            "annotation_version": "v1.0",
            "anonymization": {
                "status": "synthetic",
                "method": None,
                "original_hash": None,
            },
        },
        "annotations": annotations,
    }


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def validate_against_schema(doc: dict[str, Any]) -> list[str]:
    """Validate a dialogue document against the JSON schema.

    Returns a list of error strings. Empty list means valid.
    Uses a lightweight check without requiring jsonschema library.
    """
    errors: list[str] = []

    # Required top-level fields
    required_top = ["id", "source", "language", "theme", "messages", "metadata", "annotations"]
    for field in required_top:
        if field not in doc:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # Can't check further without basic structure

    # Source enum
    if doc.get("source") not in ("real", "amod", "simulated"):
        errors.append(f"Invalid source: {doc.get('source')}")

    # Language enum
    if doc.get("language") not in ("de", "en"):
        errors.append(f"Invalid language: {doc.get('language')}")

    # Messages structure
    messages = doc.get("messages", [])
    if not isinstance(messages, list) or len(messages) == 0:
        errors.append("messages must be a non-empty array")
    else:
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                errors.append(f"messages[{i}] must be an object")
                continue
            for req in ("role", "text", "start_time"):
                if req not in msg:
                    errors.append(f"messages[{i}] missing required field: {req}")
            if msg.get("role") not in ("Client", "Therapist", "Other"):
                errors.append(f"messages[{i}] invalid role: {msg.get('role')}")
            if "start_time" in msg and (not isinstance(msg["start_time"], (int, float)) or msg["start_time"] < 0):
                errors.append(f"messages[{i}] start_time must be >= 0")

    # Metadata
    meta = doc.get("metadata", {})
    if not isinstance(meta, dict):
        errors.append("metadata must be an object")
    else:
        for req in ("message_count", "total_chars", "anonymization"):
            if req not in meta:
                errors.append(f"metadata missing required field: {req}")
        anon = meta.get("anonymization", {})
        if isinstance(anon, dict):
            if "status" not in anon:
                errors.append("metadata.anonymization missing required field: status")
            elif anon["status"] not in ("anonymized", "synthetic", "raw"):
                errors.append(f"Invalid anonymization status: {anon['status']}")

    # Annotations
    ann = doc.get("annotations", {})
    if not isinstance(ann, dict):
        errors.append("annotations must be an object")
    else:
        for req in ("semantic_frame", "semiotic_signs", "vad_trajectory"):
            if req not in ann:
                errors.append(f"annotations missing required field: {req}")

        # VAD trajectory items
        vad = ann.get("vad_trajectory", [])
        if isinstance(vad, list):
            for i, item in enumerate(vad):
                if not isinstance(item, dict):
                    continue
                for req in ("t", "valence", "arousal", "trigger", "trigger_sign_id"):
                    if req not in item:
                        errors.append(f"vad_trajectory[{i}] missing: {req}")

        # Semiotic signs items
        signs = ann.get("semiotic_signs", [])
        if isinstance(signs, list):
            for i, sign in enumerate(signs):
                if not isinstance(sign, dict):
                    continue
                for req in ("id", "locus", "signifier", "type", "denotation"):
                    if req not in sign:
                        errors.append(f"semiotic_signs[{i}] missing: {req}")

    return errors


# ---------------------------------------------------------------------------
# Offline dialogue generator (Path B — no LLM needed)
# ---------------------------------------------------------------------------
def generate_offline_dialogue(
    dialog_id: str,
    theme: str,
    template: dict[str, Any],
    markers: dict[str, dict[str, list[str]]],
    vad_anchors: list[dict[str, float]],
    variant: int = 0,
) -> dict[str, Any]:
    """Generate a structurally valid dialogue without an LLM.

    Args:
        dialog_id: Unique ID for the dialogue (e.g. GS-SIM-001)
        theme: Theme key (e.g. "trauer")
        template: Phase template with phases, vad_type, role_dynamics, description
        markers: Marker co-occurrence map for this theme (phase -> layer -> marker IDs)
        vad_anchors: VAD profile anchors for interpolation
        variant: Variant index (0-4) for slight dialogue variation
    """
    rng = random.Random(hash((dialog_id, theme, variant)))
    phases = template["phases"]

    # Build messages from phase dialogues
    messages: list[dict[str, Any]] = []
    time_cursor = 0.0
    total_duration = 50.0  # minutes

    time_per_phase = total_duration / len(phases)

    for phase_idx, phase in enumerate(phases):
        phase_lines = PHASE_DIALOGUES.get(phase, [])
        if not phase_lines:
            # Fallback for unknown phases
            phase_lines = [
                ("Client", f"Ich moechte ueber {phase.replace('_', ' ')} sprechen."),
                ("Therapist", f"Erzaehlen Sie mir mehr darueber."),
            ]

        # Select a subset or all lines; for variation, rotate or pick differently
        if variant > 0 and len(phase_lines) >= 4:
            # Rotate lines for variation
            rotation = (variant * 2) % len(phase_lines)
            # Ensure we always have an even number starting with the right role
            rotated = phase_lines[rotation:] + phase_lines[:rotation]
            # Fix: make sure we start with Client
            if rotated and rotated[0][0] == "Therapist":
                rotated = phase_lines  # Fall back to original order
            phase_lines = rotated

        for line_idx, (role, text) in enumerate(phase_lines):
            # Ensure alternating roles relative to the last message
            if messages and messages[-1]["role"] == role:
                # Skip to maintain alternation
                continue
            time_offset = rng.uniform(0.3, 0.8)
            messages.append({
                "role": role,
                "text": text,
                "start_time": round(time_cursor, 1),
            })
            time_cursor += time_offset + (time_per_phase / max(len(phase_lines), 1))

    # Ensure we have at least 10 messages
    while len(messages) < 10:
        filler_role = "Therapist" if messages[-1]["role"] == "Client" else "Client"
        filler_texts = {
            "Client": "Ja, das stimmt. Das beruehrt mich.",
            "Therapist": "Ich verstehe. Lassen Sie uns das weiter erkunden.",
        }
        messages.append({
            "role": filler_role,
            "text": filler_texts[filler_role],
            "start_time": round(time_cursor, 1),
        })
        time_cursor += rng.uniform(0.5, 1.0)

    total_chars = sum(len(m["text"]) for m in messages)

    # Build VAD trajectory from anchors
    vad_trajectory: list[dict[str, Any]] = []
    trigger_texts = ["session start", "topic introduction", "emotional deepening",
                     "crisis point", "regulation", "recovery", "closing"]
    for i, anchor in enumerate(vad_anchors):
        trigger = trigger_texts[i] if i < len(trigger_texts) else f"phase {i}"
        vad_trajectory.append({
            "t": anchor["t"],
            "valence": anchor["valence"],
            "arousal": anchor["arousal"],
            "trigger": trigger,
            "trigger_sign_id": "",
        })

    # Build expected markers from co-occurrence data
    expected_markers: dict[str, list[str]] = {"ATO": [], "SEM": [], "CLU": [], "MEMA": []}
    for _phase, phase_markers in markers.items():
        for layer, marker_ids in phase_markers.items():
            if layer in expected_markers:
                for mid in marker_ids:
                    if mid not in expected_markers[layer]:
                        expected_markers[layer].append(mid)

    # Get theme-specific data
    semantic_frame = THEME_SEMANTIC_FRAMES.get(theme, {
        "tone": "neutral",
        "themes": [theme],
        "relational_dynamics": "standard therapeutic relationship",
        "intent": "exploration",
        "emotional_tenor": 0.0,
        "context_validity": 0.8,
        "offline_context_risk": 0.2,
    })

    semiotic_signs = THEME_SEMIOTIC_SIGNS.get(theme, [
        {
            "id": f"sign-{theme}-generic",
            "locus": "mid session",
            "signifier": theme.replace("_", " ").title(),
            "signified": f"core theme of {theme}",
            "type": "symbol",
            "denotation": f"Symbolic representation of {theme}",
            "connotations": [theme],
            "codes": ["therapeutic"],
            "evidence": f"Client discusses {theme}",
        }
    ])

    therapy_indices = THEME_THERAPY_INDICES.get(theme, {
        "trust": 70,
        "conflict": 15,
        "deescalation": 75,
        "synchronization": 65,
        "semiotic_coherence": 60,
    })

    # Add slight variation to therapy indices
    if variant > 0:
        therapy_indices = {
            k: max(0, min(100, v + rng.randint(-5, 5)))
            for k, v in therapy_indices.items()
        }

    return {
        "id": dialog_id,
        "source": "simulated",
        "language": "de",
        "theme": theme,
        "messages": messages,
        "metadata": {
            "generator": "template-replay-v1",
            "template_id": theme,
            "message_count": len(messages),
            "total_chars": total_chars,
            "duration_minutes": round(time_cursor, 1),
            "annotation_version": "v1.0",
            "anonymization": {
                "status": "synthetic",
                "method": None,
                "original_hash": None,
            },
        },
        "annotations": {
            "semantic_frame": semantic_frame,
            "semiotic_signs": semiotic_signs,
            "expected_markers": expected_markers,
            "vad_trajectory": vad_trajectory,
            "therapy_indices": therapy_indices,
            "ambiguity_profile": {
                "kinds": [],
                "dominant_reading": theme,
                "competing_readings": [],
                "overall_risk": "low",
            },
            "review_status": "llm_generated",
            "rater_a": None,
            "rater_b": None,
            "inter_rater_agreement": None,
        },
    }


# ---------------------------------------------------------------------------
# LLM-based generation (Path A)
# ---------------------------------------------------------------------------
def _try_llm_generate(
    theme: str,
    template: dict[str, Any],
    dialog_id: str,
) -> dict[str, Any] | None:
    """Attempt LLM generation via Gemini. Returns None on failure."""
    api_key = os.environ.get("LEANDEEP_GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            os.environ.get("LEANDEEP_REASONING_MODEL", "gemini-1.5-flash")
        )

        prompt = build_generation_prompt(theme, template)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )

        raw = json.loads(response.text)
        return parse_generated_dialogue(raw, dialog_id, theme)
    except Exception as e:
        logger.warning("LLM generation failed for %s (%s): %s", dialog_id, theme, e)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 50 Template-Replay therapy dialogues for Gold Standard Corpus."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "build" / "eval" / "corpus" / "simulated",
        help="Output directory for generated dialogues",
    )
    parser.add_argument(
        "--force-offline",
        action="store_true",
        help="Force offline generation even if LLM API key is available",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load templates
    with open(_TEMPLATES_DIR / "phase_templates.json") as f:
        phase_templates: dict[str, Any] = json.load(f)

    with open(_TEMPLATES_DIR / "marker_cooccurrence.json") as f:
        marker_cooccurrence: dict[str, Any] = json.load(f)

    with open(_TEMPLATES_DIR / "vad_profiles.json") as f:
        vad_profiles: dict[str, Any] = json.load(f)

    random.seed(args.seed)

    # Create output directory
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    themes = list(phase_templates.keys())
    dialog_num = 1
    total_generated = 0
    total_errors = 0
    llm_count = 0
    offline_count = 0

    for theme in themes:
        template = phase_templates[theme]
        markers = marker_cooccurrence.get(theme, {})
        vad_type = template["vad_type"]
        vad_data = vad_profiles.get(vad_type, {})
        vad_anchors = vad_data.get("anchors", [
            {"t": 0.0, "valence": 0.3, "arousal": 0.4},
            {"t": 0.5, "valence": 0.3, "arousal": 0.4},
            {"t": 1.0, "valence": 0.3, "arousal": 0.4},
        ])

        for variant in range(5):
            dialog_id = f"GS-SIM-{dialog_num:03d}"
            logger.info("Generating %s (theme=%s, variant=%d)...", dialog_id, theme, variant)

            doc = None

            # Try LLM first (unless forced offline)
            if not args.force_offline:
                doc = _try_llm_generate(theme, template, dialog_id)
                if doc is not None:
                    llm_count += 1

            # Fallback to offline
            if doc is None:
                doc = generate_offline_dialogue(
                    dialog_id, theme, template, markers, vad_anchors, variant=variant
                )
                offline_count += 1

            # Validate
            errors = validate_against_schema(doc)
            if errors:
                logger.error("Validation errors for %s: %s", dialog_id, errors)
                total_errors += len(errors)

            # Write
            out_path = output_dir / f"{dialog_id}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)

            total_generated += 1
            dialog_num += 1

    logger.info(
        "Done. Generated %d dialogues (%d LLM, %d offline). Validation errors: %d.",
        total_generated,
        llm_count,
        offline_count,
        total_errors,
    )


if __name__ == "__main__":
    main()
