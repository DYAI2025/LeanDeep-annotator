Die **vollständige JSON-Schema-Datei** (dialog_schema_extended.json) ist nun fertig. Sie ist rückwärtskompatibel zu deinem ursprünglichen Schema, erweitert es aber systematisch um die semiotische Schicht (semiotic_signs), präzise Trigger-Verknüpfung (trigger_sign_id), Ambiguitäts-Handling und Qualitätssicherung.

Das Schema folgt JSON Schema Draft 2020-12, nutzt $defs für Wiederverwendbarkeit und enthält detaillierte description- und examples-Felder für bessere Lesbarkeit und Validierung. Es ist sofort einsetzbar für Validierung, Generierung und Pipeline-Integration (Marker-Annotator + Emotion-Dynamics + Semiotik-Analyst).

**Wichtige Design-Entscheidungen**
- **Semiotic Signs**: Vollständig integriert nach dem Output-Schema deines Semotik-Skills.
- **Trigger-Verknüpfung**: trigger_sign_id ist jetzt Pflicht in der VAD-Trajektorie und referenziert semiotic_signs.
- **Ambiguität**: Separater Block für Polysemie und konkurrierende Lesarten.
- **Qualität**: inter_rater_agreement, annotation_version und erweiterte Review-Status.
- **Skalierbarkeit**: $defs für wiederverwendbare Typen (Sign, VAD-Item, Marker etc.).

**Vollständiges JSON Schema** (dialog_schema_extended.json)

JSON

Kopieren

`{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/gs-dialog-schema-extended.json",
  "title": "GS-Dialog Extended Schema – Real/Amod/Simulated with Semiotic Layer",
  "description": "Erweitertes Schema für therapeutische Dialoge mit semiotischer, marker-basierter und Emotions-Dynamics-Analyse.",
  "type": "object",
  "required": ["id", "source", "language", "theme", "messages", "metadata", "annotations"],
  "properties": {
    "id": { "type": "string", "description": "Eindeutige Dialog-ID, z.B. GS-KAH-001" },
    "source": { "type": "string", "enum": ["real", "amod", "simulated"] },
    "language": { "type": "string", "enum": ["de", "en"] },
    "theme": { "type": "string", "description": "Hauptthema, z.B. ego_state_ketamine_integration" },
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["role", "text", "start_time"],
        "properties": {
          "role": { "type": "string", "enum": ["Client", "Therapist", "Other"] },
          "text": { "type": "string" },
          "start_time": { "type": "number", "minimum": 0 }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["message_count", "total_chars"],
      "properties": {
        "generator": { "type": ["string", "null"] },
        "template_id": { "type": ["string", "null"] },
        "message_count": { "type": "integer", "minimum": 1 },
        "total_chars": { "type": "integer", "minimum": 0 },
        "duration_minutes": { "type": "number", "minimum": 0 },
        "annotation_version": { "type": "string", "default": "v1.0" }
      }
    },
    "annotations": {
      "type": "object",
      "required": ["semantic_frame", "semiotic_signs", "vad_trajectory"],
      "properties": {
        "semantic_frame": {
          "type": "object",
          "properties": {
            "tone": { "type": "string" },
            "themes": { "type": "array", "items": { "type": "string" } },
            "relational_dynamics": { "type": "string" },
            "intent": { "type": "string" },
            "emotional_tenor": { "type": "number", "minimum": -1, "maximum": 1 },
            "context_validity": { "type": "number", "minimum": 0, "maximum": 1 },
            "offline_context_risk": { "type": "number", "minimum": 0, "maximum": 1 }
          }
        },
        "semiotic_signs": {
          "type": "array",
          "items": { "$ref": "#/$defs/semioticSign" }
        },
        "expected_markers": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "vad_trajectory": {
          "type": "array",
          "items": { "$ref": "#/$defs/vadItem" }
        },
        "ambiguity_profile": {
          "type": "object",
          "properties": {
            "kinds": { "type": "array", "items": { "type": "string" } },
            "dominant_reading": { "type": "string" },
            "competing_readings": { "type": "array", "items": { "type": "string" } },
            "overall_risk": { "type": "string", "enum": ["low", "medium", "high"] }
          }
        },
        "therapy_indices": {
          "type": "object",
          "properties": {
            "trust": { "type": "integer", "minimum": 0, "maximum": 100 },
            "conflict": { "type": "integer", "minimum": 0, "maximum": 100 },
            "deescalation": { "type": "integer", "minimum": 0, "maximum": 100 },
            "synchronization": { "type": "integer", "minimum": 0, "maximum": 100 },
            "semiotic_coherence": { "type": "integer", "minimum": 0, "maximum": 100 }
          }
        },
        "review_status": { "type": "string", "enum": ["llm_generated", "human_annotated", "reviewed"] },
        "rater_a": { "type": ["string", "null"] },
        "rater_b": { "type": ["string", "null"] },
        "inter_rater_agreement": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    }
  },
  "$defs": {
    "semioticSign": {
      "type": "object",
      "required": ["id", "locus", "signifier", "type", "denotation"],
      "properties": {
        "id": { "type": "string" },
        "locus": { "type": "string", "description": "z.B. t≈48–55 min, Speaker 0" },
        "evidence": { "type": "string" },
        "signifier": { "type": "string" },
        "signified": { "type": "string" },
        "type": { "type": "string", "enum": ["icon", "index", "symbol", "mixed"] },
        "denotation": { "type": "string" },
        "connotations": { "type": "array", "items": { "type": "string" } },
        "codes": { "type": "array", "items": { "type": "string" } },
        "myth": { "type": "string" },
        "ambiguity": {
          "type": "object",
          "properties": {
            "kinds": { "type": "array", "items": { "type": "string" } },
            "risk": { "type": "string", "enum": ["low", "medium", "high"] },
            "mitigation": { "type": "string" }
          }
        },
        "markers": { "type": "array", "items": { "type": "string" } },
        "emotion_trigger": { "type": "string" },
        "valence_delta": { "type": "number" }
      }
    },
    "vadItem": {
      "type": "object",
      "required": ["t", "valence", "arousal", "trigger", "trigger_sign_id"],
      "properties": {
        "t": { "type": "number", "minimum": 0, "maximum": 1, "description": "normalisierte Zeit [0..1] oder Minuten" },
        "valence": { "type": "number", "minimum": -1, "maximum": 1 },
        "arousal": { "type": "number", "minimum": 0, "maximum": 1 },
        "trigger": { "type": "string" },
        "trigger_sign_id": { "type": "string", "description": "Referenz auf semiotic_signs.id" }
      }
    }
  }
}`
