"""Tests for the anonymization tool."""

from tools.anonymize_dialogue import anonymize_text, anonymize_dialogue, detect_pii


def test_replaces_known_names():
    text = "Dirk hat gesagt, dass Oli kommen soll."
    result = anonymize_text(text, names={"Dirk": "P1", "Oli": "P2"})
    assert "Dirk" not in result
    assert "Oli" not in result
    assert "P1" in result
    assert "P2" in result


def test_replaces_place_names():
    text = "Sie fliegt nach Wien und dann nach Israel."
    result = anonymize_text(text, places={"Wien": "[Ort_A]", "Israel": "[Ort_B]"})
    assert "Wien" not in result
    assert "[Ort_A]" in result


def test_removes_phone_numbers():
    text = "Ruf mich an: 0176-12345678 oder +49 30 1234567."
    result = anonymize_text(text)
    assert "0176" not in result
    assert "1234567" not in result


def test_removes_email():
    text = "Schreib mir an anna.mueller@klinik.de bitte."
    result = anonymize_text(text)
    assert "@" not in result


def test_preserves_therapeutic_terms():
    text = "Ego-State-Therapie, Ketamin und Borderline bleiben erhalten."
    result = anonymize_text(text)
    assert "Ego-State" in result
    assert "Ketamin" in result
    assert "Borderline" in result


def test_replaces_age_patterns():
    text = "Die Patientin ist 39 Jahre alt und seit 5 Jahren in Behandlung."
    result = anonymize_text(text)
    assert "39 Jahre" not in result
    assert "[Alter]" in result


def test_anonymize_dialogue_sets_metadata():
    dialogue = {
        "id": "GS-KAH-001",
        "source": "real",
        "messages": [{"role": "Client", "text": "Dirk sagte etwas.", "start_time": 0}],
        "metadata": {"message_count": 1, "total_chars": 18},
    }
    result = anonymize_dialogue(dialogue, names={"Dirk": "P1"})
    assert result["metadata"]["anonymization"]["status"] == "anonymized"
    assert result["metadata"]["anonymization"]["method"] == "name_replacement"
    assert "original_hash" in result["metadata"]["anonymization"]
    assert "Dirk" not in result["messages"][0]["text"]
    assert "P1" in result["messages"][0]["text"]


def test_anonymize_dialogue_preserves_structure():
    dialogue = {
        "id": "GS-KAH-001",
        "source": "real",
        "language": "de",
        "theme": "test",
        "messages": [
            {"role": "Client", "text": "Hallo.", "start_time": 0},
            {"role": "Therapist", "text": "Wie geht es Ihnen?", "start_time": 5},
        ],
        "metadata": {"message_count": 2, "total_chars": 25},
    }
    result = anonymize_dialogue(dialogue)
    assert result["id"] == "GS-KAH-001"
    assert result["source"] == "real"
    assert len(result["messages"]) == 2
    assert result["messages"][0]["start_time"] == 0
    assert result["messages"][1]["role"] == "Therapist"


def test_detect_pii_finds_patterns():
    findings = detect_pii("Anna rief 0176-1234567 an und schrieb test@mail.de")
    assert len(findings) >= 2  # phone + email at minimum
