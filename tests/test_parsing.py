from apps.api.parsing import extract_json_object, parse_repair_sections


def test_extract_json_object_from_plain_json() -> None:
    text = '{"severity":"high","root_cause":"null deref","confidence":88}'
    parsed = extract_json_object(text)
    assert parsed is not None
    assert parsed["severity"] == "high"


def test_extract_json_object_from_wrapped_response() -> None:
    text = "model output\n{\"severity\":\"medium\",\"confidence\":66}\nthanks"
    parsed = extract_json_object(text)
    assert parsed is not None
    assert parsed["confidence"] == 66


def test_parse_repair_sections() -> None:
    src = "PATCH:\n--- a/a.py\n+++ b/a.py\n\nEXPLANATION:\nAdded guard\n\nTESTS:\n- unit test\n- regression"
    patch, explanation, tests = parse_repair_sections(src)
    assert "--- a/a.py" in patch
    assert "Added guard" in explanation
    assert len(tests) == 2
