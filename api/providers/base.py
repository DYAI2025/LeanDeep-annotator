"""Base prompt template shared by all LLM providers."""

SYSTEM_PROMPT = """Du bist ein psycholinguistischer Analyst. Analysiere jeden Textabschnitt und gib ein strukturiertes semantisches Profil zurueck. Antworte ausschliesslich in JSON (Array)."""

def build_user_prompt(units_text: list[tuple[int, str]], language: str) -> str:
    """Build the user prompt with numbered text units."""
    lines = [f'[{idx}] "{text}"' for idx, text in units_text]
    texts_block = "\n".join(lines)

    return f"""Analysiere folgende Texteinheiten (Sprache: {language}):

{texts_block}

Gib pro Einheit ein JSON-Objekt zurueck mit genau diesen Feldern:
- index: int (die Nummer der Texteinheit)
- intent: "vorwurf"|"bitte"|"rechtfertigung"|"frage"|"feststellung"|"drohung"|"reparatur"|"smalltalk"|"neutral"
- register: "intim"|"informell"|"formal"|"technisch"|"therapeutisch"
- emotion_primary: "wut"|"trauer"|"angst"|"freude"|"verachtung"|"ueberraschung"|"ekel"|"neutral"
- emotion_secondary: gleiche Liste oder null
- ironie: boolean
- ironie_confidence: 0.0-1.0
- selbst_fremd: "selbst"|"fremd"|"unpersoenlich"
- beziehungsdynamik: "naehe_suche"|"distanzierung"|"kontrolle"|"unterwerfung"|"kooperation"|"neutral"
- pre_context: kurze kausale Hypothese (1 Satz, was vorher passiert sein muss) oder null
- tension: 0.0-1.0 (grundunabhaengige Spannungsintensitaet)

Antworte NUR mit dem JSON-Array, kein Markdown, kein Text drumherum."""
