import json
from typing import Any


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def parse_repair_sections(text: str) -> tuple[str, str, list[str]]:
    patch = ""
    explanation = ""
    tests: list[str] = []

    marker_patch = "PATCH"
    marker_expl = "EXPLANATION"
    marker_tests = "TESTS"

    upper = text.upper()
    p = upper.find(marker_patch)
    e = upper.find(marker_expl)
    t = upper.find(marker_tests)

    if p >= 0 and e > p:
        patch = text[p + len(marker_patch) : e].strip(" :\n")
    if e >= 0 and t > e:
        explanation = text[e + len(marker_expl) : t].strip(" :\n")
    if t >= 0:
        test_blob = text[t + len(marker_tests) :].strip(" :\n")
        for line in test_blob.splitlines():
            line = line.strip().lstrip("-*").strip()
            if line:
                tests.append(line)

    if not patch:
        patch = text.strip()
    if not explanation:
        explanation = "Generated patch proposal based on supplied failure context."
    if not tests:
        tests = ["Add a regression test for the failing scenario"]

    return patch, explanation, tests
