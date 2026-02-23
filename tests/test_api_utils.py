from apps.api.main import clamp_confidence, severity_score


def test_clamp_confidence_bounds() -> None:
    assert clamp_confidence(120) == 99
    assert clamp_confidence(-1) == 1
    assert clamp_confidence("42") == 42


def test_severity_score_detects_critical() -> None:
    text = "Security issue led to auth bypass in production"
    assert severity_score(text) == "critical"


def test_severity_score_detects_high() -> None:
    text = "Unhandled exception caused 500 error"
    assert severity_score(text) == "high"
