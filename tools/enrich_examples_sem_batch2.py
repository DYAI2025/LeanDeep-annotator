#!/usr/bin/env python3
"""
Enrich SEM markers (batch 2 - second half alphabetically) with German examples.
Target: 50 positive + 25 negative per marker.
Only updates markers that exist as YAML files. Preserves all other fields.
"""

from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # prevent line wrapping
yaml.default_flow_style = False

BASE = Path("build/markers_rated")
DIRS = ["1_approved", "2_good", "3_needs_work"]
TARGET_POS = 50
TARGET_NEG = 25


# ──────────────────────────────────────────────────────────────────────
# Example data per marker
# ──────────────────────────────────────────────────────────────────────

EXAMPLES = {}

# ─── SEM_SELF_SUPPORT_STATEMENT ───
EXAMPLES["SEM_SELF_SUPPORT_STATEMENT"] = {
    "positive": [
        "Ich mache mir selbst Mut.",
        "Ich muntere mich selbst auf.",
        "Ich stehe mir selbst zur Seite.",
        "Ich sage mir: Du schaffst das.",
        "Ich stärke mich innerlich.",
        "Ich rede mir gut zu.",
        "Ich erinnere mich an meine Stärken.",
        "Ich halte zu mir.",
        "Ich beruhige mich selbst.",
        "Ich gebe mir Halt.",
        "Ich baue mich wieder auf.",
        "Ich bin freundlich zu mir.",
        "Ich bleibe zugewandt mit mir.",
        "Ich sporne mich an.",
        "Ich motiviere mich selbst.",
        "Ich sage mir immer wieder: Du bist stark genug.",
        "Ich stehe morgens auf und rede mir Mut zu.",
        "Ich hab mir vorgenommen, heute nett zu mir zu sein.",
        "Ich feiere meine kleinen Erfolge bewusst.",
        "Ich gebe mir die Erlaubnis, Fehler zu machen.",
        "Ich erlaube mir, langsam zu sein.",
        "Ich sage mir: Es ist okay, nicht perfekt zu sein.",
        "Ich klopfe mir innerlich auf die Schulter.",
        "Ich spreche liebevoll mit mir selbst.",
        "Ich nehme mich selbst in den Arm, so mental halt.",
        "Ich atme durch und sage mir: Es wird besser.",
        "Ich gönne mir Pausen ohne schlechtes Gewissen.",
        "Ich stärke mich mit positiven Gedanken.",
        "Ich sage mir, dass ich das Recht habe, traurig zu sein.",
        "Ich bin mein eigener bester Freund gerade.",
        "Ich mache mir bewusst, was ich alles geschafft habe.",
        "Ich halte mich an meinen eigenen Worten fest.",
        "Ich ermutige mich selbst, weiterzumachen.",
        "Ich sage mir: Du hast schon Schlimmeres überstanden.",
        "Ich versuche, mir selbst eine gute Beraterin zu sein.",
        "Ich tröste mich damit, dass morgen ein neuer Tag ist.",
        "Ich nehme mir vor, gut auf mich aufzupassen.",
        "Ich höre auf meine innere Stimme, die sagt: Das packst du.",
        "Ich behandle mich so, wie ich eine Freundin behandeln würde.",
        "Ich bin geduldig mit mir, auch wenn es schwer fällt.",
        "Ich lobe mich für das, was ich heute geschafft hab.",
        "Ich halte mir vor Augen, dass ich wertvoll bin.",
        "Ich rede mir ein: Schritt für Schritt.",
        "Ich gebe mir den Raum, den ich brauche.",
        "Ich sage mir: Du darfst auch mal schwach sein.",
        "Ich stehe hinter mir, egal was die anderen sagen.",
        "Ich vertraue darauf, dass ich das hinkriege.",
        "Ich unterstütze mich selbst in dieser Phase.",
        "Ich achte auf meine Bedürfnisse und nehme sie ernst.",
        "Ich bin stolz auf mich, auch wenn es nur Kleinigkeiten sind.",
    ],
    "negative": [
        "Kannst du mir das Salz reichen?",
        "Der Termin ist um 14 Uhr.",
        "Ich war gestern einkaufen.",
        "Das Wetter soll morgen besser werden.",
        "Hast du die E-Mail gelesen?",
        "Ich muss noch tanken.",
        "Die Besprechung ist im Konferenzraum.",
        "Ich habe den Zug verpasst.",
        "Der Film war echt langweilig.",
        "Hast du schon gegessen?",
        "Morgen kommt meine Schwester zu Besuch.",
        "Ich hab vergessen, Milch zu kaufen.",
        "Die Waschmaschine ist kaputt.",
        "Er hat mir gesagt, ich solle stärker sein.",
        "Mein Chef hat mich heute gelobt.",
        "Die Kinder waren heute brav.",
        "Ich habe die Rechnung bezahlt.",
        "Das Meeting wurde verschoben.",
        "Wann hast du Feierabend?",
        "Ich brauche neue Schuhe.",
        "Der Supermarkt schließt um 20 Uhr.",
        "Du solltest mal einen Therapeuten aufsuchen.",
        "Mein Kollege hat mir geholfen.",
        "Wir haben morgen frei.",
        "Ich schaue heute Abend Netflix.",
    ],
}

# ─── SEM_SHARED_HUMOR ───
EXAMPLES["SEM_SHARED_HUMOR"] = {
    "positive": [
        "Hahah Danke.",
        "Boah haha fahren jetzt endlich heim",
        "Haha er ist sehr labil",
        "Ja haha deine Jacke hat mich Mega gerettet",
        "Haha naja",
        "aye.. haha..",
        "Hahaha ja genau!",
        "Haha stimmt, das war witzig",
        "LOL ja das kenn ich",
        "Haha ok das ist gut",
        "Haha du bist so verrückt, ich lieb's!",
        "Omg haha das erinnert mich an damals bei der Party",
        "Hahaha wir sind echt die schlimmsten",
        "Haha geil, du checkst es immer sofort",
        "Lol weißt du noch als wir das gemacht haben?",
        "Haha ja Mann, das war episch",
        "Hahaha ich kann nicht mehr, du bist so dumm 😂",
        "Haha klassiker von dir",
        "Omg haha die gleiche Energie wie letztes Mal",
        "Hahaha ok das ist echt unser Ding",
        "Haha war klar dass du das sagst",
        "Lol ja wir sind halt so",
        "Haha das erinnert mich an unseren Insider",
        "Hahaha ich sterbe gerade, danke dafür",
        "Haha du hast mich zum Lachen gebracht, danke Schatz",
        "Lol wir zwei sind unmöglich zusammen",
        "Haha ok ich geb's zu, das war lustig",
        "Hahaha same, ich dachte genau das gleiche",
        "Haha ja voll, das ist so typisch für uns",
        "Lol weißt du was das lustigste daran war?",
        "Haha ich liebe unsere Gespräche",
        "Hahaha der war gut, den merk ich mir",
        "Haha du bringst mich immer zum Grinsen",
        "Lol ja stimmt, wir haben den gleichen Humor",
        "Haha boah erinnerst du dich an den Kellner?",
        "Hahaha ich hab fast mein Getränk ausgespuckt",
        "Haha ok wir müssen aufhören, mir tut der Bauch weh",
        "Lol das erzähl ich morgen auf der Arbeit",
        "Haha genau so wars, du beschreibst das perfekt",
        "Hahaha niemand versteht unseren Humor",
        "Haha alter, du bist die Beste",
        "Lol ich musste so lachen als du das geschickt hast",
        "Haha ok das war unerwartet lustig",
        "Hahaha wir hätten Comedians werden sollen",
        "Haha weißt du was, du machst meinen Tag besser",
        "Lol ja das ist unser running gag",
        "Haha ich konnte gar nicht aufhören zu lachen",
        "Hahaha ok ok, Punkt für dich",
        "Haha genau das hab ich mir auch gedacht, wir ticken gleich",
        "Lol haha boah ey, ich kann grad nicht",
    ],
    "negative": [
        "Das finde ich gar nicht lustig.",
        "Ich verstehe nicht was daran witzig sein soll.",
        "Hör auf darüber zu lachen.",
        "Das ist ernst gemeint.",
        "Ich mache keine Witze.",
        "Kannst du bitte mal ernst bleiben?",
        "Das Thema ist mir wichtig, bitte keine Witze.",
        "Ich lache gerade nicht, ich bin sauer.",
        "Dein Humor nervt mich manchmal echt.",
        "Ich finde es respektlos, dass du darüber lachst.",
        "Lach nicht, ich meine das so.",
        "Das ist kein Spaß für mich.",
        "Ich will jetzt nicht lachen, mir geht's schlecht.",
        "Hör auf, alles ins Lächerliche zu ziehen.",
        "Der Witz ist mir zu viel gerade.",
        "Ich bin nicht in Stimmung für sowas.",
        "Bitte nimm das ernst.",
        "Ich verstehe deinen Humor einfach nicht.",
        "Das verletzt mich, auch wenn du es lustig meinst.",
        "Können wir mal sachlich bleiben?",
        "Dein Sarkasmus hilft gerade nicht.",
        "Ich fühle mich nicht wohl damit.",
        "Das geht mir zu weit mit dem Spaß.",
        "Ich möchte ernsthaft darüber reden.",
        "Witze sind gerade fehl am Platz.",
    ],
}

# ─── SEM_UNTRACEABLE_PAYMENT_METHOD ───
EXAMPLES["SEM_UNTRACEABLE_PAYMENT_METHOD"] = {
    "positive": [
        "Am einfachsten wäre es, wenn du mir ein paar Amazon-Geschenkkarten kaufst und die Codes fotografierst.",
        "Eine Überweisung dauert zu lange, per Western Union ist das Geld sofort da.",
        "Kryptowährungen wie Bitcoin sind der sicherste und anonymste Weg, mir zu helfen.",
        "Bitte sende das Geld nicht auf mein Konto, sondern an meinen Agenten über MoneyGram.",
        "Du kannst das Geld auf eine Prepaid-Kreditkarte laden und mir die Daten schicken.",
        "Kaufe bitte Steam-Gutscheine im Wert von 500 Euro und schick mir die Nummern.",
        "Google Play Karten gehen am schnellsten, die kann ich hier sofort einlösen.",
        "Schick mir das Geld bitte über Wise an diese Adresse, aber nicht auf ein Bankkonto.",
        "iTunes-Karten sind die einfachste Lösung, die gibt es an jeder Tankstelle.",
        "Wir machen das über Hawala, das ist hier in meiner Region üblich.",
        "Bitte kein PayPal, das geht hier nicht. Nimm lieber Western Union.",
        "Ich kann kein normales Bankkonto nutzen, schick es bitte per Bargeldtransfer.",
        "Am besten du kaufst mir eine Paysafecard und schickst den Code.",
        "Bitcoin ist am sichersten für uns beide, hier ist meine Wallet-Adresse.",
        "Ethereum geht auch, Hauptsache kein Bankkonto — das wird hier überwacht.",
        "MoneyGram ist die einzige Option, die hier funktioniert.",
        "Kauf einfach Gutscheine und schick mir Fotos von den Codes.",
        "Per Bargeldumschlag wäre auch eine Option, ich gebe dir die Adresse.",
        "Neosurf-Gutscheine kann ich hier sofort einlösen, das ist am einfachsten.",
        "Bitte über TransferGo, aber als Bargeldabholung, nicht als Banküberweisung.",
        "Prepaid Visa Karten sind perfekt, die kann ich überall nutzen.",
        "Du könntest mir auch über Crypto.com was schicken, das ist diskreter.",
        "Mein Bankkonto ist gesperrt, bitte schick das Geld über einen Transfer-Service.",
        "Am besten kaufst du mir Zalando-Gutscheine, die kann ich hier verkaufen.",
        "Ria Money Transfer geht am schnellsten, bar zur Abholung bitte.",
        "Revolut funktioniert bei mir nicht, nimm bitte Western Union.",
        "Cashapp oder Venmo gehen hier leider nicht, nur Gutscheincodes.",
        "Kauf mir bitte eine Mastercard Geschenkkarte und schick die Daten.",
        "Das Geld muss bar sein, per Überweisung geht das nicht wegen der Behörden.",
        "Tether USDT ist am besten, das schwankt nicht so wie Bitcoin.",
        "Schick es bitte über WorldRemit, Bargeldabholung in meiner Stadt.",
        "Eine CashtoCode-Zahlung wäre die sicherste Methode für uns.",
        "Monero ist komplett anonym, das wäre die ideale Lösung.",
        "Bitte lade Geld auf eine virtuelle Karte und schick mir die Nummer.",
        "Über eine App wie Remitly kannst du mir Bargeld schicken, das geht schnell.",
        "Guthabenkarten vom Supermarkt sind am unkompliziertesten.",
        "Kein Banktransfer bitte, das dauert Wochen und wird kontrolliert.",
        "Dash oder Litecoin gehen auch, Hauptsache dezentral.",
        "Schick mir die Apple-Geschenkkarte einfach per Foto, den Rest mache ich.",
        "Über Xoom kannst du mir Bargeld zur Abholung senden.",
        "Ich brauche die Geschenkkartennummer und den PIN, dann ist alles erledigt.",
        "Per Hawala-Broker geht das in 24 Stunden, ganz ohne Bank.",
        "Bitte kauf mir Flexepin-Codes, die kann ich hier direkt einlösen.",
        "Hier gibt es keinen PayPal-Zugang, aber Western Union hat eine Filiale.",
        "Nimm bitte Ria oder MoneyGram, bar zur Abholung.",
        "Eine anonyme Krypto-Wallet ist das Sicherste für dich und mich.",
        "Ich kann nur Gutscheincodes annehmen, alles andere wird blockiert.",
        "Bitte schick es über den informellen Kanal, den ich dir erklärt habe.",
        "Goldkauf und Versand wäre auch eine Möglichkeit, wenn du magst.",
        "Per Telegram kann ich dir eine Bitcoin-Adresse schicken, das ist einfacher.",
    ],
    "negative": [
        "Ich finde, wir sollten das in Ruhe besprechen.",
        "Das ist ein guter Punkt, den du da machst.",
        "Ich verstehe deine Perspektive.",
        "Lass uns gemeinsam eine Lösung finden.",
        "Mir ist aufgefallen, dass wir unterschiedlich denken.",
        "Ich möchte verstehen, was du meinst.",
        "Das klingt nach einem wichtigen Thema für dich.",
        "Kannst du mir deine IBAN schicken? Dann überweise ich dir das.",
        "Ich zahle dir das per normaler Banküberweisung zurück.",
        "Soll ich dir das Geld per PayPal schicken?",
        "Meine Bankverbindung findest du auf der Rechnung.",
        "Hast du ein Konto bei der Sparkasse? Dann geht's am schnellsten.",
        "Ich überweise dir morgen die 50 Euro zurück.",
        "Das Geld ist schon auf deinem Konto, dauert einen Werktag.",
        "Soll ich per Lastschrift oder Überweisung zahlen?",
        "Ich habe das online per Kreditkarte bezahlt.",
        "Die Rechnung kannst du per SEPA-Überweisung begleichen.",
        "Ich schicke dir das Geld per PayPal Friends, ok?",
        "Die Miete überweise ich wie immer am Ersten.",
        "Hast du die Erstattung von Amazon schon bekommen?",
        "Soll ich das Ticket per Karte bezahlen?",
        "Ich hab dir das Geld gerade überwiesen.",
        "Per Klarna kann man das auch in Raten zahlen.",
        "Ich bezahle das heute Abend online.",
        "Die Kaution überweise ich morgen mit Betreff 'Wohnung XY'.",
    ],
}

# ─── SEM_WEBCAM_EXCUSE ───
EXAMPLES["SEM_WEBCAM_EXCUSE"] = {
    "positive": [
        "Ich würde ja gerne, aber ich bin auf einer Militärbasis und Kameras sind hier streng verboten.",
        "Mein Laptop ist alt und die Webcam hat schon vor Jahren den Geist aufgegeben.",
        "Die Internetverbindung auf dieser Ölplattform ist zu schlecht für ein Videotelefonat.",
        "Ich sehe heute schrecklich aus, habe kaum geschlafen. Lass uns das auf morgen verschieben.",
        "Ich bin zu schüchtern für die Kamera. Ich mag es lieber, wenn wir schreiben.",
        "Mein Glaube erlaubt mir keine Videoanrufe.",
        "Ich bin gerade bei meiner Familie, hier kann ich nicht ungestört per Video telefonieren.",
        "Der Treiber für meine Kamera muss aktualisiert werden, das dauert ewig.",
        "Lass uns erst eine tiefere Verbindung aufbauen, bevor wir uns per Video sehen.",
        "Ich habe gerade eine schlimme Erkältung, ich will nicht, dass du mich so siehst.",
        "Die Sicherheitssoftware meiner Firma blockiert alle Video-Ports.",
        "Ich bin nicht der Typ, der sich gerne selbst auf dem Bildschirm sieht.",
        "Meine Haare sind eine Katastrophe!",
        "Es ist schon dunkel hier, das Licht ist zu schlecht.",
        "Ich habe nur mein Handy und die Frontkamera ist gesprungen.",
        "Vielleicht ein andermal, ich fühle mich gerade nicht danach.",
        "Ich finde, unsere Stimmen am Telefon zu hören, ist viel intimer.",
        "Ich bin in einem öffentlichen WLAN, das ist zu unsicher für Video.",
        "Meine Religion verbietet die Abbildung von Personen.",
        "Lass uns das geheimnisvoll halten. Die Vorfreude ist doch das Schönste.",
        "Gerade ist mein Bildschirm schwarz, keine Ahnung warum.",
        "Oh nein, Zoom funktioniert bei mir einfach nie!",
        "Das Mikro ist okay, aber das Bild geht schon wieder nicht.",
        "Ich habe eine Panikattacke, wenn ich mich selbst auf Video sehe.",
        "Sorry, das Licht ist so schlecht, du würdest eh nichts erkennen.",
        "Mein Handy hat keinen Speicher mehr, da stürzt die Kamera-App immer ab.",
        "Ich bin auf Dienstreise in einem Hotel ohne stabiles WLAN.",
        "Meine Kamera wird gerade von einem anderen Programm blockiert.",
        "Die Kinder schlafen nebenan, ich kann kein Video machen.",
        "Mein Gesicht ist geschwollen von einer Behandlung, das möchte ich dir nicht zumuten.",
        "Ich habe gerade einen Sonnenbrand und sehe furchtbar aus.",
        "Auf dem Schiff hier gibt es nur Satelliteninternet, Video unmöglich.",
        "Ich bin im Krankenhaus, die erlauben hier keine Videoanrufe.",
        "Mein Arbeitgeber verbietet private Videocalls auf dem Diensthandy.",
        "Die Webcam meines PCs ist abgeklebt wegen Datenschutz, geht gerade nicht ab.",
        "Ich bin zu müde für Video, sehe aus wie ein Zombie.",
        "FaceTime spinnt mal wieder, das geht einfach nicht.",
        "Ich sitze gerade im Zug, Video geht bei dem Empfang nicht.",
        "Ich mag keine Videocalls, das macht mich nervös.",
        "Mein Akku ist fast leer und Video frisst zu viel Strom.",
        "Ich bin auf einer Baustelle, da wäre ein Videocall zu laut.",
        "Meine Kamera hat einen Grünstich, das sieht total komisch aus.",
        "Ich habe kein Datenvolumen mehr, Video geht nur über WLAN.",
        "Ich bin in einer Zone ohne Netzabdeckung, kaum Internet hier.",
        "Mein Gesicht hat gerade eine allergische Reaktion, ich möchte nicht vor die Kamera.",
        "Die App will ein Update, und ich habe gerade keine Zeit dafür.",
        "Ich telefoniere lieber, Video ist mir zu aufwändig.",
        "Mein Bildschirm flackert, ich muss den erst reparieren lassen.",
        "In meinem Land ist FaceTime gesperrt wegen Regulierung.",
        "Ich habe eine Augenverletzung und muss Augenpflaster tragen, geht nicht.",
    ],
    "negative": [
        "Ich sehe heute schwierig aus, habe kaum geschlafen. Lass uns das auf morgen verschieben.",
        "Ich sehe das anders, aber ich respektiere deine Sicht.",
        "Ich möchte ehrlich mit dir sein, auch wenn es schwer ist.",
        "Du hast recht, das war mein Fehler. Es tut mir leid.",
        "Lass uns beide unsere Seite erklären.",
        "Ich fühle mich unwohl dabei und möchte darüber reden.",
        "Ich verstehe, warum du das so siehst.",
        "Klar, lass uns jetzt videotelefonieren! Einen Moment, ich schalte die Kamera ein.",
        "Ja super, FaceTime klingt gut, ich bin bereit!",
        "Ich ruf dich gleich per Video an, freue mich dich zu sehen.",
        "Hey, Kamera läuft, kannst du mich sehen?",
        "Na endlich, ich wollte schon lange mal videochatten mit dir!",
        "Zoom oder Teams? Sag an, ich bin für beides bereit.",
        "Lass uns morgen Abend einen Videocall machen, da hab ich Zeit.",
        "Ich freu mich total auf den Videocall!",
        "Meine neue Webcam ist super, die Qualität ist echt gut.",
        "Ich hab das Video extra für dich aufgenommen, guck mal.",
        "Wir können auch Google Meet nehmen, das funktioniert immer.",
        "Ich zeig dir per Video meine neue Wohnung!",
        "Hey, ich schick dir erstmal ein Video von mir.",
        "Klar können wir skypen, wann passt es dir?",
        "Ich hab mir extra eine Ring-Lampe gekauft für unsere Calls.",
        "Der Videocall gestern war so schön, lass das öfter machen.",
        "Ich hab gerade Discord offen, willst du kurz reinkommen?",
        "Video geht klar, ich bin in 5 Minuten ready.",
    ],
}

# ─── SEM_EMOTIONAL_AWARENESS ───
EXAMPLES["SEM_EMOTIONAL_AWARENESS"] = {
    "positive": [
        "Ich achte auf meine Gefühle und fühle mich ruhiger.",
        "Mir war klar, dass ich ängstlich wurde.",
        "Ich merke, dass ich mich unsicher fühle.",
        "Ich achte darauf, wenn ich traurig bin.",
        "Ich bin mir bewusst, dass ich nervös bin.",
        "Ich spüre, wie die Freude kommt.",
        "Ich bemerke meine Anspannung.",
        "Mir ist bewusst, dass ich wütend bin.",
        "Ich registriere mein Unbehagen.",
        "Ich nehme wahr, dass ich erleichtert bin.",
        "Ich achte auf meinen Ärger.",
        "Ich bin mir meiner Trauer bewusst.",
        "Ich erkenne meine Angst.",
        "Ich spüre die Nervosität.",
        "Mir wird klar, wenn es kippt.",
        "Ich merke gerade, dass ich total aufgeregt bin.",
        "Ich nehme wahr, dass mich das traurig macht.",
        "Mir fällt auf, dass ich bei dem Thema immer gereizt reagiere.",
        "Ich spüre, dass ich mich innerlich zurückziehe.",
        "Ich bemerke eine leise Wut in mir.",
        "Mir ist bewusst, dass ich gerade überfordert bin.",
        "Ich achte darauf, wie sich mein Bauch anfühlt — da ist Angst.",
        "Ich erkenne, dass ich eifersüchtig bin, und das ist okay.",
        "Ich nehme meine Enttäuschung wahr, bevor ich reagiere.",
        "Mir wird bewusst, dass ich mich gerade schäme.",
        "Ich spüre, dass Freude aufkommt, wenn du das sagst.",
        "Ich bemerke, dass ich mich nach Nähe sehne.",
        "Ich achte auf die Traurigkeit, die gerade hochkommt.",
        "Mir fällt auf, dass ich Angst habe, dich zu verlieren.",
        "Ich registriere, dass ich gerade genervt bin.",
        "Ich merke, dass mich das berührt.",
        "Ich bin mir bewusst, dass ich mich gerade schuldig fühle.",
        "Ich spüre eine Mischung aus Freude und Trauer.",
        "Mir wird klar, dass ich Sehnsucht habe.",
        "Ich nehme wahr, dass ich erleichtert und gleichzeitig unsicher bin.",
        "Ich bemerke, wie sich meine Stimmung verändert.",
        "Ich achte auf mein inneres Ungleichgewicht.",
        "Ich erkenne, dass ich gerade abwehrend bin.",
        "Mir fällt auf, dass ich innerlich angespannt bin.",
        "Ich spüre, dass mich das mehr mitnimmt als ich dachte.",
        "Ich merke, dass ich gerade neidisch bin, und versuche es zu verstehen.",
        "Ich bin mir bewusst, dass mich das verletzt hat.",
        "Ich nehme wahr, dass ich mich vor dem Gespräch fürchte.",
        "Mir wird bewusst, wie erschöpft ich emotional bin.",
        "Ich achte darauf, was dieses Gefühl mir sagen will.",
        "Ich bemerke, dass ich mich gerade ganz klein fühle.",
        "Ich registriere eine tiefe Dankbarkeit.",
        "Ich erkenne, dass ich wütend bin, weil ich mich nicht gehört fühle.",
        "Mir fällt auf, dass ich mich in der Situation hilflos fühle.",
        "Ich spüre genau, wie die Enttäuschung kommt.",
    ],
    "negative": [
        "Ich finde, wir sollten das in Ruhe besprechen.",
        "Das ist ein guter Punkt, den du da machst.",
        "Ich verstehe deine Perspektive.",
        "Lass uns gemeinsam eine Lösung finden.",
        "Mir ist aufgefallen, dass wir unterschiedlich denken.",
        "Ich möchte verstehen, was du meinst.",
        "Das klingt nach einem wichtigen Thema für dich.",
        "Ich bin traurig.",
        "Mir geht's schlecht.",
        "Ich bin wütend auf dich.",
        "Ich habe Angst.",
        "Ich bin so glücklich gerade.",
        "Das macht mich fertig.",
        "Ich fühl mich einsam.",
        "Das nervt mich total.",
        "Ich hab keinen Bock mehr.",
        "Ich bin enttäuscht von dir.",
        "Das regt mich auf.",
        "Ich fühle mich unwohl.",
        "Morgen wird bestimmt besser.",
        "Hast du die Nachrichten gesehen?",
        "Ich muss noch einkaufen gehen.",
        "Der Arzttermin ist übermorgen.",
        "Ich habe letzte Woche Sport gemacht.",
        "Wir sollten mal wieder was zusammen unternehmen.",
    ],
}


def find_yaml(marker_id: str) -> Path | None:
    """Find YAML file for marker across all rating dirs."""
    for d in DIRS:
        for ext in [".yaml", ".yml"]:
            p = BASE / d / "SEM" / (marker_id + ext)
            if p.exists():
                return p
    return None


def get_example_keys(data: dict) -> tuple[str, str]:
    """Determine the correct positive/negative key names."""
    ex = data.get("examples", {})
    if isinstance(ex, dict):
        pos_key = "positive_de" if "positive_de" in ex else "positive"
        neg_key = "negative_de" if "negative_de" in ex else "negative"
    else:
        pos_key = "positive"
        neg_key = "negative"
    return pos_key, neg_key


def main():
    updated = 0
    skipped_nofile = 0
    skipped_target = 0
    errors = 0

    for marker_id, new_examples in EXAMPLES.items():
        path = find_yaml(marker_id)
        if path is None:
            print(f"SKIP (no file): {marker_id}")
            skipped_nofile += 1
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.load(f)

            pos_key, neg_key = get_example_keys(data)

            # Ensure examples dict exists
            if "examples" not in data or not isinstance(data.get("examples"), dict):
                from ruamel.yaml.comments import CommentedMap
                data["examples"] = CommentedMap()

            existing_pos = data["examples"].get(pos_key, []) or []
            existing_neg = data["examples"].get(neg_key, []) or []

            current_pos = len(existing_pos)
            current_neg = len(existing_neg)

            if current_pos >= TARGET_POS and current_neg >= TARGET_NEG:
                print(f"SKIP (at target): {marker_id} ({current_pos}p/{current_neg}n)")
                skipped_target += 1
                continue

            # Replace with full set
            data["examples"][pos_key] = new_examples["positive"][:TARGET_POS]
            data["examples"][neg_key] = new_examples["negative"][:TARGET_NEG]

            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)

            final_pos = len(data["examples"][pos_key])
            final_neg = len(data["examples"][neg_key])
            print(f"UPDATED: {marker_id} ({current_pos}->{final_pos}p, {current_neg}->{final_neg}n) @ {path}")
            updated += 1

        except Exception as e:
            print(f"ERROR: {marker_id} — {e}")
            errors += 1

    print(f"\n{'='*60}")
    print(f"Summary: {updated} updated, {skipped_nofile} no file, {skipped_target} at target, {errors} errors")


if __name__ == "__main__":
    main()
