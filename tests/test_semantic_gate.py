"""Tests for the semantic gate in the detection engine."""


def test_semantic_gate_suppresses_wrong_intent():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="smalltalk", intent_confidence=0.9,
        register="informell", emotion_primary="neutral",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="unpersoenlich", beziehungsdynamik="neutral",
        pre_context=None, tension=0.1, source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_GATE", layer="ATO", confidence=0.8,
        description="test", matches=[], message_indices=[0],
    )

    eng.markers["TEST_GATE"] = MarkerDef(
        id="TEST_GATE", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={
            "intents": ["vorwurf", "drohung"],
            "intents_exclude": ["smalltalk"],
        },
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 0, "Should suppress marker when intent is excluded"


def test_semantic_gate_passes_matching_intent():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="vorwurf", intent_confidence=0.9,
        register="intim", emotion_primary="wut",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="selbst", beziehungsdynamik="distanzierung",
        pre_context="Wiederholter Konflikt", tension=0.8,
        source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_PASS", layer="ATO", confidence=0.8,
        description="test", matches=[], message_indices=[0],
    )

    eng.markers["TEST_PASS"] = MarkerDef(
        id="TEST_PASS", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={
            "intents": ["vorwurf", "drohung"],
            "ironie_suppress": True,
        },
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 1
    assert result[0].confidence == 0.8, "Should pass with full confidence"


def test_semantic_gate_suppresses_ironie():
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="feststellung", intent_confidence=0.8,
        register="informell", emotion_primary="verachtung",
        emotion_secondary=None, ironie=True, ironie_confidence=0.9,
        selbst_fremd="fremd", beziehungsdynamik="distanzierung",
        pre_context=None, tension=0.5, source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_IRONY", layer="ATO", confidence=0.9,
        description="test", matches=[], message_indices=[0],
    )

    eng.markers["TEST_IRONY"] = MarkerDef(
        id="TEST_IRONY", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity={"ironie_suppress": True},
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 0 or result[0].confidence < 0.2, "Should suppress when ironic"


def test_semantic_gate_passes_without_affinity():
    """Markers without semantic_affinity should always pass."""
    from api.engine import MarkerEngine, Detection, MarkerDef
    from api.semantic import SemanticProfile

    eng = MarkerEngine()
    eng.load()

    profile = SemanticProfile(
        intent="drohung", intent_confidence=0.9,
        register="intim", emotion_primary="wut",
        emotion_secondary=None, ironie=False, ironie_confidence=0.0,
        selbst_fremd="fremd", beziehungsdynamik="kontrolle",
        pre_context=None, tension=0.9, source="llm", text_span=(0, 10),
    )

    det = Detection(
        marker_id="TEST_NO_AFFINITY", layer="ATO", confidence=0.7,
        description="test", matches=[], message_indices=[0],
    )

    eng.markers["TEST_NO_AFFINITY"] = MarkerDef(
        id="TEST_NO_AFFINITY", layer="ATO", lang="de", description="test",
        frame={}, patterns=[], examples={}, tags=[], rating=1,
        semantic_affinity=None,
    )

    result = eng._apply_semantic_gate([det], profile)
    assert len(result) == 1
    assert result[0].confidence == 0.7
