#!/usr/bin/env python3
"""
Enrich ATO markers with German-language examples (50 positive, 25 negative).
Batch 2: Second half alphabetically of 132 ATO markers.

Only processes markers that:
1. Have a YAML file in build/markers_rated/
2. Are below target (50 positive / 25 negative)

Uses ruamel.yaml to preserve formatting.
"""

from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # prevent line wrapping

BASE = Path("build/markers_rated")
DIRS = ["1_approved", "2_good", "3_needs_work"]
TARGET_POS = 50
TARGET_NEG = 25


def build_id_map():
    """Build mapping of marker ID -> file path."""
    id_map = {}
    for d in DIRS:
        ato_dir = BASE / d / "ATO"
        if not ato_dir.exists():
            continue
        for f in ato_dir.glob("*.yaml"):
            try:
                data = yaml.load(f.read_text())
                if data and "id" in data:
                    id_map[data["id"]] = f
            except Exception as e:
                print(f"  WARN: Could not parse {f}: {e}")
    return id_map


# ============================================================
# Example data for each marker
# ============================================================

EXAMPLES = {
    "ATO_FEELING_CONNECTION": {
        "positive": [
            "Ich fühle mich dir so nah wie noch nie.",
            "Es gibt eine tiefe Verbindung zwischen uns.",
            "Wir sind auf einer Wellenlänge, das spüre ich.",
            "Wenn ich bei dir bin, fühle ich mich komplett.",
            "Zwischen uns stimmt einfach alles.",
            "Ich habe das Gefühl, dass uns etwas ganz Besonderes verbindet.",
            "Du bist der Mensch, bei dem ich mich am meisten zuhause fühle.",
            "Wenn wir zusammen sind, fühlt sich alles richtig an.",
            "Diese Verbindung zu dir ist etwas, das ich noch nie erlebt habe.",
            "Ich fühle mich dir verbunden, auch wenn wir weit weg sind.",
            "Wir sind eng verbunden, das merke ich immer wieder.",
            "Mit dir fühle ich mich ganz und vollständig.",
            "Uns verbindet etwas, das über Worte hinausgeht.",
            "Ich spüre eine Verbindung zu dir, die ich nicht erklären kann.",
            "Bei dir bin ich angekommen, das weiß ich einfach.",
            "Es fühlt sich so vertraut an mit dir, als würden wir uns ewig kennen.",
            "Die Chemie zwischen uns stimmt einfach perfekt.",
            "Das verbindet uns auf eine Art, die ich sonst nirgends erlebe.",
            "Wenn du da bist, fühle ich mich zugehörig.",
            "Unsere Verbindung ist das Wertvollste in meinem Leben.",
            "Ich spüre eine tiefe emotionale Nähe zu dir.",
            "Mit dir zusammen fühle ich mich nicht allein auf der Welt.",
            "Wir verstehen uns ohne Worte, das ist Verbundenheit.",
            "Ich fühle mich dir auch über die Entfernung verbunden.",
            "Du gibst mir das Gefühl von Zugehörigkeit.",
            "Zusammen fühlt sich alles vertraut und sicher an.",
            "Unsere Verbindung wächst mit jedem Tag.",
            "Ich habe bei dir das Gefühl, dass ich dazugehöre.",
            "Du bist für mich wie ein Anker, der mich verbindet.",
            "Dieses Gefühl der Nähe zu dir ist unbeschreiblich.",
            "Wir sind seelenverwandt, da bin ich mir sicher.",
            "Bei dir fühle ich mich aufgehoben und verbunden.",
            "Es gibt eine unsichtbare Verbindung zwischen uns.",
            "Zusammen sein mit dir fühlt sich an wie nach Hause kommen.",
            "Ich spüre, dass wir auf einer tiefen Ebene verbunden sind.",
            "Du bist der Mensch, der mich am besten versteht, und das verbindet uns.",
        ],
        "negative": [
            "Wir sollten mal wieder telefonieren.",
            "Ich habe heute Pizza bestellt.",
            "Kannst du mir die Adresse schicken?",
            "Das Meeting ist um drei.",
            "Ich gehe jetzt einkaufen.",
            "Morgen wird es regnen.",
            "Hast du den Schlüssel dabei?",
            "Ich war heute beim Arzt.",
            "Der Zug hatte Verspätung.",
            "Ich trinke gerade Kaffee.",
            "Wir kennen uns schon lange.",
            "Ich finde deinen Vorschlag interessant.",
            "Das war ein netter Abend gestern.",
            "Du bist mir sympathisch.",
            "Ich mag deine Art zu reden.",
            "Nette Kollegin, die neue.",
            "Der Film war ganz gut.",
            "Ich habe das Buch fertig gelesen.",
        ],
    },
    "ATO_LL_RECEIVING_GIFTS": {
        "positive": [
            "Ich habe dir was Kleines mitgebracht, weil ich an dich gedacht habe.",
            "Schau mal, diese kleine Aufmerksamkeit hat mich an dich erinnert.",
            "Ich habe dir eine Überraschung gekauft, einfach so.",
            "Das Mitbringsel ist zwar klein, aber es kommt von Herzen.",
            "Ich habe dir ein Erinnerungsstück von unserer Reise aufgehoben.",
            "Hier, ein Geschenk für dich, ohne besonderen Anlass.",
            "Die Geste zählt, nicht der Preis.",
            "Ich habe dir Blumen mitgebracht, weil du sie so liebst.",
            "Diese kleine Aufmerksamkeit soll dich aufmuntern.",
            "Ich wollte dir etwas schenken, das dich an uns erinnert.",
            "Schau, ich habe dir deine Lieblingsschokolade besorgt.",
            "Die Überraschung war mir wichtig, weil du es verdienst.",
            "Ein kleines Mitbringsel aus dem Urlaub für dich.",
            "Ich habe dir ein Buch geschenkt, weil es mich an dich erinnert hat.",
            "Diese Kette ist ein Geschenk, damit du weißt, dass ich an dich denke.",
            "Ich habe dir Karten für das Konzert besorgt, einfach weil.",
            "Hier, eine kleine Aufmerksamkeit zum Feierabend.",
            "Das Erinnerungsstück von unserem ersten Treffen habe ich aufgehoben.",
            "Ich habe dir dein Lieblingseis mitgebracht.",
            "Das Geschenk ist selbstgemacht, weil es persönlicher ist.",
            "Für dich habe ich etwas ganz Besonderes ausgesucht.",
            "Ich schenke dir diese Kerze, weil du sie letztens so schön fandest.",
            "Hier ist eine Überraschung, die ich für dich aufgehoben habe.",
            "Ein kleines Geschenk als Dankeschön für alles.",
            "Ich habe dir dieses Parfüm mitgebracht, weil du es im Laden gemocht hast.",
            "Dieses Mitbringsel habe ich extra für dich ausgesucht.",
            "Ich wollte dir eine Freude machen und habe dir was Schönes geholt.",
            "Wichtig ist die Geste dahinter, nicht der materielle Wert.",
            "Schau mal, ich habe dir einen Talisman gebastelt.",
            "Dieses kleine Geschenk soll dir sagen, dass du wichtig bist.",
            "Ich habe dir aus dem Urlaub etwas mitgebracht.",
            "Hier, eine kleine Aufmerksamkeit für meinen Lieblingsmenschen.",
            "Ich schenke dir dieses Bild, weil es mich an unseren Moment erinnert.",
            "Für dich habe ich einen Gutschein für dein Lieblingsrestaurant besorgt.",
            "Ich habe diese Postkarte aufgehoben als Erinnerungsstück an uns.",
            "Hier, ein Geschenk, ich wollte dir einfach zeigen, dass ich dich liebe.",
            "Ich bringe dir immer gern etwas mit, wenn ich verreise.",
            "Schau, eine kleine Überraschung auf deinem Schreibtisch.",
            "Das Mitbringsel ist von mir, ich weiß, du magst sowas.",
            "Ich habe dir dein Lieblingsbrot mitgebracht, weil ich beim Bäcker war.",
        ],
        "negative": [
            "Ich muss noch Weihnachtsgeschenke kaufen.",
            "Hast du die Rechnung bezahlt?",
            "Der Laden hat um 20 Uhr zu.",
            "Ich brauche neue Schuhe.",
            "Was kostet das denn?",
            "Das war zu teuer.",
            "Ich finde, wir sollten das in Ruhe besprechen.",
            "Mir ist aufgefallen, dass wir unterschiedlich denken.",
            "Ich möchte verstehen, was du meinst.",
            "Das ist ein guter Punkt.",
            "Wir müssen noch einkaufen gehen.",
            "Ich habe den Kassenbon verloren.",
            "Der Versand dauert drei Tage.",
            "Hast du den Gutschein eingelöst?",
            "Die Retoure wurde bearbeitet.",
            "Ich bestelle das online.",
            "Hast du dir das selbst gekauft?",
            "Das Paket kommt morgen.",
        ],
    },
    "ATO_MINIMIZATION": {
        "positive": [
            "Ach, war nur ein bisschen unangenehm.",
            "Das ist doch nicht so schlimm, mach dir keine Sorgen.",
            "Halb so wild, passiert halt.",
            "Eigentlich war es okay, kein großes Ding.",
            "War ja nichts Ernstes.",
            "Das ist doch kein Drama.",
            "Mach dir keinen Kopf, war nur ein bisschen stressig.",
            "Ist ja halb so wild, echt jetzt.",
            "So schlimm war es gar nicht, glaub mir.",
            "War nur ein kleiner Streit, nichts Weltbewegendes.",
            "Ach, das war nur ein bisschen ärgerlich.",
            "Eigentlich okay, man gewöhnt sich dran.",
            "Nicht so schlimm wie es klingt.",
            "War halb so wild, ehrlich gesagt.",
            "Nur ein bisschen müde, sonst alles gut.",
            "Das ist echt nicht so schlimm, vertrau mir.",
            "Eigentlich okay, ich mache kein Drama daraus.",
            "Ach, halb so wild, das regelt sich.",
            "Ist ja nur ein bisschen Stress, geht vorbei.",
            "War nicht so schlimm, hab ich schon vergessen.",
            "Nur ein bisschen traurig, aber geht schon.",
            "Eigentlich okay, ist nicht der Rede wert.",
            "Halb so wild, ich übertreibe sicher.",
            "So schlimm ist das doch nicht, oder?",
            "War nur ein kleines Missverständnis, halb so wild.",
            "Naja, nur ein bisschen enttäuscht, nicht so schlimm.",
            "Ist eigentlich okay, andere haben es schlimmer.",
            "War ja nur ein bisschen peinlich.",
            "Nicht so schlimm, ich habe Schlimmeres erlebt.",
            "Ach, halb so wild, ich komme drüber weg.",
            "War nur ein bisschen kalt draußen.",
            "Eigentlich okay, war ja nur eine Kleinigkeit.",
            "So schlimm war das wirklich nicht.",
            "Halb so wild, das kennt doch jeder.",
            "Nur ein bisschen angespannt, geht gleich wieder.",
            "Ist ja nicht so schlimm, lass gut sein.",
            "War eigentlich okay, ein bisschen komisch vielleicht.",
            "Ach, halb so wild, ich bin da nicht nachtragend.",
            "Nur ein bisschen nervös, aber nicht so schlimm.",
            "Das war doch gar nicht so schlimm.",
            "War halb so wild, ich hab das überstanden.",
            "Eigentlich okay, war ja nur kurz.",
            "Nicht so schlimm, geht mir schon besser.",
            "Ach, war nur ein bisschen ungemütlich.",
            "Halb so wild, das passiert jedem mal.",
        ],
        "negative": [
            "Das hat mich tief getroffen und ich bin wirklich verletzt.",
            "Das war eine schwierige Situation und ich bin noch nicht darüber hinweg.",
            "Ich nehme das sehr ernst und brauche Zeit.",
            "Das ist mir wirklich wichtig, bitte hör zu.",
            "Ich fühle mich damit nicht wohl und will ehrlich sein.",
            "Das war schlimm für mich, das gebe ich offen zu.",
            "Mich hat das wirklich beschäftigt.",
            "Ich bin total kaputt nach dem Tag.",
            "Das war echt hart für mich.",
            "Ich bin frustriert und enttäuscht.",
            "Mir geht es nicht gut damit.",
            "Das hat mich total aufgewühlt.",
            "Ich bin wütend und traurig zugleich.",
            "Das war eine echte Belastung.",
            "Ich brauche Hilfe bei dem Thema.",
            "Mir fehlen die Worte, so schlimm war das.",
            "Das hat mich richtig fertig gemacht.",
            "Ich bin noch ganz aufgelöst deswegen.",
        ],
    },
    "ATO_NEGATION": {
        "positive": [
            "Nein, das will ich nicht.",
            "Das stimmt so nicht.",
            "Keinesfalls, auf gar keinen Fall.",
            "Auf keinen Fall mache ich das.",
            "Nicht mit mir, das geht nicht.",
            "Nein, da bin ich anderer Meinung.",
            "Das ist nicht richtig.",
            "Nein, absolut nicht.",
            "Auf keinen Fall kommt das in Frage.",
            "Keinesfalls werde ich das akzeptieren.",
            "Nein, das stimmt einfach nicht.",
            "Das sehe ich nicht so, überhaupt nicht.",
            "Nicht in Ordnung, nein.",
            "Nein danke, das möchte ich nicht.",
            "Keinesfalls werde ich das so hinnehmen.",
            "Das habe ich nicht gesagt.",
            "Auf keinen Fall fahre ich da hin.",
            "Nein, das passt mir nicht.",
            "Stimmt nicht, das ist falsch.",
            "Nicht jetzt, nein.",
            "Auf keinen Fall stimme ich zu.",
            "Nein, das ist mir zu viel.",
            "Das will ich nicht, nein.",
            "Keinesfalls war das meine Schuld.",
            "Nein nein nein, so nicht.",
            "Das geht nicht, auf keinen Fall.",
            "Nicht wahr, das hast du dir ausgedacht.",
            "Nein, nie im Leben.",
            "Stimmt nicht, so war das nicht.",
            "Das kommt nicht in Frage.",
            "Auf keinen Fall lasse ich das durchgehen.",
            "Nein, ich lehne ab.",
            "Keinesfalls akzeptabel.",
            "Nicht unter diesen Bedingungen.",
            "Auf keinen Fall, das sage ich klar.",
            "Nein, definitiv nicht.",
            "Nicht in meinem Haus.",
            "Das stimmt nicht, und das weißt du.",
            "Keinesfalls, das kommt überhaupt nicht in Frage.",
            "Nein, fertig, Ende der Diskussion.",
            "Nicht so, das muss anders gehen.",
            "Auf keinen Fall gehe ich da mit.",
            "Nein, kein Stück, gar nicht.",
            "Das hat nicht gestimmt, was du gesagt hast.",
        ],
        "negative": [
            "Ja, das finde ich auch.",
            "Okay, einverstanden.",
            "Stimmt, da hast du recht.",
            "Gerne, kein Problem.",
            "Klar, mach ich.",
            "Das ist eine gute Idee.",
            "Ja natürlich, gerne doch.",
            "Ich bin dabei.",
            "Das klingt gut.",
            "Meinetwegen, warum nicht?",
            "Geht klar, machen wir.",
            "Super, das passt.",
            "Von mir aus, einverstanden.",
            "Ja sicher, kein Thema.",
            "Finde ich gut, lass uns das machen.",
            "Genau so sehe ich das auch.",
            "Richtig, das stimmt.",
            "Alles klar, bin dabei.",
        ],
    },
    "ATO_ORGANIZATION_ENTITY": {
        "positive": [
            "Ich arbeite seit drei Jahren bei Bosch.",
            "Die Caritas hat uns damals sehr geholfen.",
            "Bei der Deutschen Bahn gibt es immer Verspätungen.",
            "Meine Schwester macht ein Praktikum bei der Telekom.",
            "Der ADAC hat uns abgeschleppt.",
            "Die AOK hat die Kosten übernommen.",
            "Er ist Mitglied beim TÜV Süd.",
            "Die Diakonie bietet Beratung an.",
            "Mein Mann arbeitet bei Volkswagen.",
            "Die Sparkasse hat die Zinsen erhöht.",
            "Der Fußballverein FC Bayern hat gewonnen.",
            "Ich habe mich bei der Agentur für Arbeit gemeldet.",
            "Die Stiftung Warentest hat den Test veröffentlicht.",
            "Die Allianz hat die Versicherung genehmigt.",
            "Wir haben bei IKEA neue Möbel bestellt.",
            "Die Polizeigewerkschaft hat protestiert.",
            "Das Jugendamt wurde eingeschaltet.",
            "Mein Sohn studiert an der TU München.",
            "Die Gewerkschaft ver.di hat zum Streik aufgerufen.",
            "Ich habe ein Angebot von Lufthansa bekommen.",
            "Die DHL hat das Paket verloren.",
            "Die Barmer übernimmt die Kur.",
            "Wir waren beim Familiengericht.",
            "Das Arbeitsamt hat mir eine Stelle vermittelt.",
            "Die Kirche hat eine Spendensammlung organisiert.",
            "Der Elternbeirat hat sich beschwert.",
            "Die Hausverwaltung reagiert nicht.",
            "Mein Chef hat mit der IHK gesprochen.",
            "Das Sozialamt hat den Antrag abgelehnt.",
            "Die Commerzbank hat die Überziehung gestrichen.",
            "Ich warte auf einen Termin bei der Rentenversicherung.",
            "Die Tafel verteilt Lebensmittel an Bedürftige.",
            "Mein Verein hat das Sportfest organisiert.",
            "Die Techniker Krankenkasse hat den Brief geschickt.",
        ],
        "negative": [
            "Ich war heute arbeiten.",
            "Die Besprechung war um 14 Uhr.",
            "Er hat einen neuen Job angefangen.",
            "Meine Chefin ist nett.",
            "Ich habe morgen frei.",
            "Das Büro ist im dritten Stock.",
            "Ich muss Überstunden machen.",
            "Die Kollegen sind freundlich.",
            "Ich finde, wir sollten das in Ruhe besprechen.",
            "Das ist ein guter Punkt, den du da machst.",
            "Ich verstehe deine Perspektive.",
            "Wir gehen morgen Abend essen.",
            "Das Wetter war heute schön.",
            "Ich habe den Rasen gemäht.",
            "Die Kinder spielen draußen.",
            "Ich koche heute Abend.",
            "Wir fahren am Wochenende weg.",
            "Morgen habe ich einen Termin.",
        ],
    },
    "ATO_OVERLAP_INTERRUPT": {
        "positive": [
            "A: Ich wollte sagen— B: (überlappt) Warte, das ist wichtig!",
            "A: Also ich denke— B: (rein) Nein, hör mal!",
            "A: Wenn wir das— B: (überlappt) Stopp, ich war noch nicht fertig!",
            "A: Es geht darum— B: (rein) Das ist doch Quatsch!",
            "A: Ich meine— B: (überlappt) Genau das!",
            "A: Wir könnten— B: (rein) Ich wollte gerade—",
            "A: Und dann hat er— B: (überlappt) Moment, lass mich ausreden!",
            "A: Das Problem ist— B: (rein) Nein nein, das—",
            "A: Gestern war— B: (überlappt) Ja, ich weiß!",
            "A: Aber ich— B: (rein) Warte, warte, warte.",
            "A: Meine Meinung ist— B: (überlappt) Das stimmt nicht!",
            "A: Also wir haben— B: (rein) Darf ich kurz?",
            "A: Ich finde— B: (überlappt) Sorry, aber—",
            "A: Letzte Woche— B: (rein) Ach, davon rede ich ja!",
            "A: Und wenn— B: (überlappt) Aber genau das meine ich!",
            "A: Ich hab— B: (rein) Ich auch!",
            "A: Es ist so— B: (überlappt) Du unterbrichst mich dauernd!",
            "A: Na ja— B: (rein) Moment mal eben.",
            "A: Ich sage— B: (überlappt) Lass mich bitte!",
            "A: Egal was— B: (rein) Stopp! Ich erst.",
            "A: Also ich— B: (überlappt) Ja aber—",
            "A: Wie gesagt— B: (rein) Kann ich was sagen?",
            "A: Das heißt— B: (überlappt) Nein, andersrum!",
            "A: Mein Plan— B: (rein) Dein Plan? Haha!",
            "A: Warte ich— B: (überlappt) Nee, ich zuerst.",
            "A: Also wenn du— B: (rein) Ich hatte grade—",
            "A: Das finde ich— B: (überlappt) Falsch!",
            "A: Hör zu— B: (rein) Nein, DU hör zu!",
            "A: Können wir— B: (überlappt) Kurze Frage!",
            "A: Es war— B: (rein) Ja genau, und—",
            "A: Meiner Meinung— B: (überlappt) Deine Meinung?",
            "A: Ich weiß dass— B: (rein) Weißt du was?",
            "A: Wir sollten— B: (überlappt) Sollten wir nicht!",
            "A: Außerdem— B: (rein) Außerdem was?",
            "A: Das einzige— B: (überlappt) Das stimmt so nicht!",
            "A: Bitte— B: (rein) Ich muss kurz—",
            "A: Morgen— B: (überlappt) Morgen geht nicht!",
            "A: Wichtig ist— B: (rein) Wichtiger ist—",
            "A: Ich denke— B: (überlappt) Du denkst immer—",
            "A: Vielleicht— B: (rein) Definitiv!",
            "A: Also— B: (überlappt) Also nein.",
            "A: Mein Punkt— B: (rein) Was für ein Punkt?",
        ],
        "negative": [
            "A: Was denkst du? B: Ich denke, das ist eine gute Idee.",
            "A: Und dann? B: Dann sind wir nach Hause gefahren.",
            "Ich habe aufmerksam zugehört und stimme dir zu.",
            "Lass mich kurz nachdenken, bevor ich antworte.",
            "Du hast recht, ich warte bis du fertig bist.",
            "Entschuldige, rede bitte weiter.",
            "Ich höre dir zu, erzähl weiter.",
            "Bitte sprich ruhig zu Ende.",
            "Ich warte, bis du fertig bist.",
            "Erzähl mir mehr davon.",
            "Ich bin ganz Ohr.",
            "Nimm dir die Zeit, die du brauchst.",
            "Was wolltest du noch sagen?",
            "Ich wollte nicht unterbrechen.",
            "Bitte fahr fort.",
            "Ich lass dich ausreden.",
            "Rede ruhig weiter, ich höre zu.",
            "Du bist dran, ich bin still.",
        ],
    },
    "ATO_SARCASM_CUES": {
        "positive": [
            "Ja genau, als ob das jemals funktioniert hat.",
            "Na klar, das ist ja total einfach.",
            "Ganz bestimmt, und morgen flieg ich zum Mond.",
            "Super logisch, echt genial dein Plan.",
            "Na klar doch, wir haben ja alle unbegrenzt Zeit.",
            "Ja, genau, du bist natürlich der Experte hier.",
            "Ganz bestimmt hat das niemand vorher probiert /s",
            "Super, na klar funktioniert das einfach so.",
            "Ja genau, so wie beim letzten Mal.",
            "Na klar, weil das bei dir ja immer so gut klappt.",
            "Ganz bestimmt wird das diesmal anders.",
            "Na klar doch, einfach mal machen, was soll schon schiefgehen.",
            "Super, logisch, warum bin ich da nicht drauf gekommen.",
            "Ja, genau, läuft bei dir.",
            "Ganz bestimmt eine tolle Idee /s",
            "Na klar, du hast ja auch nie Fehler gemacht.",
            "Ja genau, das hilft bestimmt total.",
            "Super na klar, sag ich doch.",
            "Na klar doch, wer braucht schon Schlaf.",
            "Ganz bestimmt die beste Entscheidung deines Lebens.",
            "Ja, genau, das hat ja schon drei Mal nicht geklappt.",
            "Na klar, weil Geld ja auf Bäumen wächst.",
            "Ganz bestimmt ist das die Lösung aller Probleme.",
            "Super logisch, warum macht das nicht jeder so?",
            "Ja genau, das wird total gut ausgehen /s",
            "Na klar doch, das glaube ich dir sofort.",
            "Ganz bestimmt hast du recht, wie immer.",
            "Ja, genau, weil das Leben ja so fair ist.",
            "Na klar, als hätte ich nichts Besseres zu tun.",
            "Super, na klar, kein Problem, easy.",
            "Ja genau, du bist der Einzige mit Problemen.",
            "Ganz bestimmt wird das ein voller Erfolg.",
            "Na klar doch, das war ja absehbar.",
            "Ja, genau, als ob mich das überrascht.",
            "Super logisch, da kommt man von alleine drauf.",
            "Na klar, weil du ja immer alles besser weißt.",
            "Ganz bestimmt, das wird sich von alleine lösen.",
            "Ja genau, noch so eine brillante Idee von dir.",
            "Na klar doch, läuft ja hervorragend /s",
            "Super, na klar, als ob das realistisch wäre.",
            "Ja, genau, das macht total Sinn.",
            "Ganz bestimmt habe ich darauf gewartet.",
            "Na klar, weil das so einfach ist, ne?",
            "Ja genau, herzlichen Glückwunsch zu der Erkenntnis.",
            "Super logisch, und die Erde ist eine Scheibe.",
        ],
        "negative": [
            "Ja, genau so machen wir das, guter Plan!",
            "Na klar, das schaffen wir gemeinsam.",
            "Ganz bestimmt wird es morgen besser.",
            "Super, ich freue mich darüber.",
            "Klar, verstanden, ich bin dabei.",
            "Das ist wirklich eine gute Idee, finde ich.",
            "Ja, stimmt, da hast du völlig recht.",
            "Natürlich, das mache ich gerne für dich.",
            "Logisch, das ergibt Sinn.",
            "Ich bin aufrichtig begeistert von deinem Vorschlag.",
            "Danke, das ist echt nett von dir.",
            "Na klar helfe ich dir, kein Problem.",
            "Ganz bestimmt komme ich zu deiner Feier.",
            "Super Idee, lass uns das umsetzen!",
            "Ja, genau das wollte ich auch vorschlagen.",
            "Klar doch, gerne mache ich das.",
            "Das ist wirklich toll, danke dir!",
            "Logisch, das ist der richtige Weg.",
        ],
    },
    "ATO_SECOND_PERSON_ABSOLUTE_2P_TRAIT": {
        "positive": [
            "Du bist einfach arrogant, das war schon immer so.",
            "Ihr seid doch alle unsicher, deshalb macht ihr das.",
            "Du bist so dermaßen egoistisch.",
            "Du bist faul, das ist der Kern des Problems.",
            "Ihr seid unfähig, das zu begreifen.",
            "Du bist arrogant und merkst es nicht mal.",
            "Ihr seid unsicher, deshalb greift ihr mich an.",
            "Du bist egoistisch bis auf die Knochen.",
            "Du bist so faul, das ist nicht auszuhalten.",
            "Ihr seid unfähig, eine einfache Aufgabe zu erledigen.",
            "Du bist arrogant, punkt.",
            "Du bist unfähig, zuzuhören.",
            "Ihr seid arrogant und herablassend.",
            "Du bist unsicher, das sieht man dir an.",
            "Du bist egoistisch, dich interessiert nur du selbst.",
            "Ihr seid faul, immer muss ich alles machen.",
            "Du bist arrogant, wie dein Vater.",
            "Du bist unfähig, Kritik anzunehmen.",
            "Ihr seid so unsicher, das ist peinlich.",
            "Du bist egoistisch, du denkst nur an dich.",
            "Du bist faul und bequem.",
            "Ihr seid unfähig, euch zu organisieren.",
            "Du bist arrogant, deshalb hast du keine Freunde.",
            "Du bist unsicher und neidisch.",
            "Ihr seid egoistisch, keiner denkt an andere.",
            "Du bist faul, steh endlich auf.",
            "Du bist unfähig, dich zu entschuldigen.",
            "Ihr seid arrogant, ohne Grund.",
            "Du bist unsicher, deshalb kontrollierst du alles.",
            "Du bist egoistisch, das ist dein Problem.",
            "Ihr seid faul, das sieht man am Ergebnis.",
            "Du bist arrogant und überheblich.",
            "Du bist unfähig, dich zu ändern.",
            "Du bist egoistisch und rücksichtslos.",
            "Ihr seid unsicher und projiziert das auf mich.",
            "Du bist faul, du könntest so viel mehr.",
            "Du bist unfähig, auch nur eine Sache richtig zu machen.",
            "Du bist arrogant und selbstgerecht.",
            "Ihr seid egoistisch und denkt nie an die Konsequenzen.",
            "Du bist faul, das ist keine Überraschung.",
            "Du bist unfähig, einen Kompromiss einzugehen.",
            "Du bist arrogant und eingebildet.",
        ],
        "negative": [
            "Ich finde, du hast manchmal eine andere Perspektive als ich.",
            "Mir fällt auf, dass wir unterschiedlich an Dinge herangehen.",
            "Ich wünsche mir, dass du mehr zuhörst.",
            "Ich fühle mich manchmal nicht gehört.",
            "Ich empfinde das als schwierig.",
            "Mir wäre es lieber, wenn wir das anders machen.",
            "Ich möchte ehrlich mit dir sein, auch wenn es schwer ist.",
            "Du hast recht, das war mein Fehler.",
            "Ich verstehe, warum du das so siehst.",
            "Lass uns beide unsere Seite erklären.",
            "Ich fühle mich unwohl und möchte darüber reden.",
            "Danke, dass du mir das sagst, ich denke darüber nach.",
            "Du wirkst heute müde, ist alles okay?",
            "Ich sehe, dass du dich Mühe gibst.",
            "Du bist heute so ruhig, alles gut?",
            "Du hast viel geschafft heute.",
            "Ich finde, du machst das richtig gut.",
            "Du wirkst nachdenklich, was beschäftigt dich?",
        ],
    },
}


def enrich_marker(marker_id, filepath, examples_data):
    """Add examples to a marker YAML file up to target counts."""
    data = yaml.load(filepath.read_text())

    if "examples" not in data:
        data["examples"] = {}

    ex = data["examples"]

    # Detect existing key names
    pos_key = "positive_de" if "positive_de" in ex else "positive"
    neg_key = "negative_de" if "negative_de" in ex else "negative"

    # Get existing examples
    existing_pos = list(ex.get(pos_key, []) or [])
    existing_neg = list(ex.get(neg_key, []) or [])

    # Calculate how many to add
    need_pos = TARGET_POS - len(existing_pos)
    need_neg = TARGET_NEG - len(existing_neg)

    if need_pos <= 0 and need_neg <= 0:
        print(f"  SKIP {marker_id}: already at target ({len(existing_pos)}/{len(existing_neg)})")
        return False

    new_pos = examples_data.get("positive", [])
    new_neg = examples_data.get("negative", [])

    # Filter out duplicates
    existing_pos_set = set(str(e).strip() for e in existing_pos)
    existing_neg_set = set(str(e).strip() for e in existing_neg)

    new_pos_unique = [e for e in new_pos if str(e).strip() not in existing_pos_set]
    new_neg_unique = [e for e in new_neg if str(e).strip() not in existing_neg_set]

    # Add up to needed count
    final_pos = existing_pos + new_pos_unique[:need_pos]
    final_neg = existing_neg + new_neg_unique[:need_neg]

    ex[pos_key] = final_pos
    ex[neg_key] = final_neg

    # Write back
    with open(filepath, "w") as f:
        yaml.dump(data, f)

    print(f"  OK   {marker_id}: {len(existing_pos)}->{len(final_pos)} pos, {len(existing_neg)}->{len(final_neg)} neg")
    return True


def main():
    print("Building marker ID -> filepath map...")
    id_map = build_id_map()
    print(f"Found {len(id_map)} ATO markers total\n")

    # Target markers from the batch
    targets = list(EXAMPLES.keys())

    updated = 0
    skipped = 0
    not_found = 0

    for marker_id in targets:
        if marker_id not in id_map:
            print(f"  MISS {marker_id}: no YAML file found")
            not_found += 1
            continue

        filepath = id_map[marker_id]
        examples_data = EXAMPLES[marker_id]

        if enrich_marker(marker_id, filepath, examples_data):
            updated += 1
        else:
            skipped += 1

    print(f"\nDone: {updated} updated, {skipped} skipped, {not_found} not found")


if __name__ == "__main__":
    main()
