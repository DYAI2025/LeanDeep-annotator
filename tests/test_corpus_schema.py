import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path("build/eval/schema/dialog_schema.json")


def test_schema_is_valid_json_schema():
    """The schema file itself must be a valid JSON Schema Draft 2020-12."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_requires_anonymization():
    schema = json.loads(SCHEMA_PATH.read_text())
    meta_required = schema["properties"]["metadata"]["required"]
    assert "anonymization" in meta_required


def test_minimal_valid_dialogue_passes():
    """A minimal valid dialogue should pass schema validation."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text())
    minimal = {
        "id": "GS-TEST-001",
        "source": "simulated",
        "language": "de",
        "theme": "test",
        "messages": [{"role": "Client", "text": "Hallo.", "start_time": 0}],
        "metadata": {
            "message_count": 1,
            "total_chars": 6,
            "anonymization": {"status": "synthetic"},
        },
        "annotations": {
            "semantic_frame": {"tone": "neutral"},
            "semiotic_signs": [],
            "vad_trajectory": [],
        },
    }
    jsonschema.validate(minimal, schema)


def test_raw_anonymization_status_is_allowed_by_schema():
    """Schema allows 'raw' (validation tool catches it, not schema)."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text())
    d = {
        "id": "GS-TEST-002",
        "source": "real",
        "language": "de",
        "theme": "test",
        "messages": [{"role": "Client", "text": "Test.", "start_time": 0}],
        "metadata": {
            "message_count": 1,
            "total_chars": 5,
            "anonymization": {"status": "raw"},
        },
        "annotations": {
            "semantic_frame": {},
            "semiotic_signs": [],
            "vad_trajectory": [],
        },
    }
    # Schema allows "raw" -- validation tool is the policy enforcer, not the schema
    jsonschema.validate(d, schema)
