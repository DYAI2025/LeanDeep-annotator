"""Tests for the anonymization validator."""

from tools.validate_anonymization import validate_dialogue, validate_corpus_dir


def test_rejects_raw_status():
    d = {"metadata": {"anonymization": {"status": "raw"}}, "messages": []}
    errors = validate_dialogue(d)
    assert any("raw" in e.lower() for e in errors)


def test_accepts_anonymized_clean():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "P1 sagte etwas zu P2."}]}
    assert validate_dialogue(d) == []


def test_accepts_synthetic():
    d = {"metadata": {"anonymization": {"status": "synthetic"}},
         "messages": [{"text": "Ein simulierter Dialog."}]}
    assert validate_dialogue(d) == []


def test_detects_common_german_names():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Anna hat gestern mit Thomas gesprochen."}]}
    errors = validate_dialogue(d)
    assert len(errors) > 0
    assert any("Anna" in e or "Thomas" in e for e in errors)


def test_detects_phone_pattern():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Erreichbar unter 0176-1234567."}]}
    errors = validate_dialogue(d)
    assert len(errors) > 0


def test_detects_email_pattern():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Mail an test@example.com."}]}
    errors = validate_dialogue(d)
    assert len(errors) > 0


def test_ignores_pseudonyms():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "P1 und P2 sprachen ueber Therapie."}]}
    assert validate_dialogue(d) == []


def test_ignores_therapeutic_terms():
    """Names that are also therapeutic terms should not trigger false positives."""
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Ego-State-Therapie und Borderline-Diagnostik."}]}
    assert validate_dialogue(d) == []


def test_missing_anonymization_field():
    d = {"metadata": {}, "messages": []}
    errors = validate_dialogue(d)
    assert len(errors) > 0
