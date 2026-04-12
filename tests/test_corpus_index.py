import json
from pathlib import Path
from tools.build_corpus_index import build_index_from_dialogues, scan_corpus_dir

def test_index_counts_sources():
    dialogues = [
        {"id": "GS-KAH-001", "source": "real", "language": "de", "theme": "ego_state",
         "metadata": {"message_count": 20, "total_chars": 5000},
         "annotations": {"review_status": "human_annotated"}},
        {"id": "GS-AMOD-001", "source": "amod", "language": "en", "theme": "angst",
         "metadata": {"message_count": 2, "total_chars": 500},
         "annotations": {"review_status": "llm_generated"}},
        {"id": "GS-SIM-001", "source": "simulated", "language": "de", "theme": "trauer",
         "metadata": {"message_count": 15, "total_chars": 3000},
         "annotations": {"review_status": "llm_generated"}},
    ]
    index = build_index_from_dialogues(dialogues)
    assert index["stats"]["total"] == 3
    assert index["stats"]["by_source"]["real"] == 1
    assert index["stats"]["by_source"]["amod"] == 1
    assert index["stats"]["by_source"]["simulated"] == 1
    assert index["stats"]["by_language"]["de"] == 2
    assert index["stats"]["by_language"]["en"] == 1

def test_index_counts_themes():
    dialogues = [
        {"id": f"GS-{i}", "source": "simulated", "language": "de", "theme": t,
         "metadata": {"message_count": 10, "total_chars": 1000},
         "annotations": {"review_status": "llm_generated"}}
        for i, t in enumerate(["angst", "angst", "trauer"])
    ]
    index = build_index_from_dialogues(dialogues)
    assert index["stats"]["by_theme"]["angst"] == 2
    assert index["stats"]["by_theme"]["trauer"] == 1

def test_index_lists_all_dialogues():
    dialogues = [
        {"id": f"GS-{i}", "source": "simulated", "language": "de", "theme": "x",
         "metadata": {"message_count": 5, "total_chars": 500},
         "annotations": {"review_status": "llm_generated"}}
        for i in range(5)
    ]
    index = build_index_from_dialogues(dialogues)
    assert len(index["dialogues"]) == 5
    assert all("id" in d and "path" in d for d in index["dialogues"])

def test_index_includes_review_status_stats():
    dialogues = [
        {"id": "a", "source": "real", "language": "de", "theme": "x",
         "metadata": {"message_count": 10, "total_chars": 1000},
         "annotations": {"review_status": "human_annotated"}},
        {"id": "b", "source": "simulated", "language": "de", "theme": "x",
         "metadata": {"message_count": 10, "total_chars": 1000},
         "annotations": {"review_status": "llm_generated"}},
    ]
    index = build_index_from_dialogues(dialogues)
    assert index["stats"]["by_review_status"]["human_annotated"] == 1
    assert index["stats"]["by_review_status"]["llm_generated"] == 1
