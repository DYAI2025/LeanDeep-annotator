from api.models import AnalyzeResponse


def test_analyze_response_schema_builds_without_forward_ref_errors():
    # Regression test for CI failures on pydantic 2.5 where AnalyzeMeta was
    # referenced before declaration and could not be resolved during schema generation.
    schema = AnalyzeResponse.model_json_schema()
    assert "meta" in schema["properties"]
