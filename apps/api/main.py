import os
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from apps.api.parsing import extract_json_object, parse_repair_sections

load_dotenv()


def parse_origins(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def severity_score(error_text: str) -> str:
    txt = error_text.lower()
    if any(k in txt for k in ["segmentation fault", "data loss", "security", "auth bypass"]):
        return "critical"
    if any(k in txt for k in ["exception", "timeout", "500", "failed"]):
        return "high"
    if any(k in txt for k in ["warning", "deprecated", "minor"]):
        return "low"
    return "medium"


app = FastAPI(title="DraftForge Repair Agent API", version="1.1.0")
origins = parse_origins(os.getenv("ALLOW_ORIGINS", "*"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Language = Literal["python", "javascript", "typescript", "go", "java", "other"]


class AnalyzeRequest(BaseModel):
    code: str = Field(min_length=10, max_length=20000)
    error_log: str = Field(min_length=3, max_length=12000)
    language: Language = "python"


class RepairRequest(BaseModel):
    code: str = Field(min_length=10, max_length=20000)
    error_log: str = Field(min_length=3, max_length=12000)
    language: Language = "python"
    strategy: Literal["minimal_patch", "safe_refactor", "performance_fix"] = "minimal_patch"


class AnalyzeResponse(BaseModel):
    severity: str
    root_cause: str
    confidence: int
    provider: str


class RepairResponse(BaseModel):
    patch: str
    explanation: str
    tests_to_add: list[str]
    provider: str


def clamp_confidence(value: int | float | str | None) -> int:
    try:
        val = int(float(value if value is not None else 75))
    except (TypeError, ValueError):
        val = 75
    return max(1, min(99, val))


def local_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    root = (
        "Likely null/None handling gap or unchecked assumption near failing path. "
        "Add input guards and explicit error handling around boundary conditions."
    )
    return AnalyzeResponse(
        severity=severity_score(req.error_log),
        root_cause=root,
        confidence=71,
        provider="fallback",
    )


def local_patch(req: RepairRequest) -> RepairResponse:
    patch = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@\n"
        "-result = process(data)\n"
        "+if data is None:\n"
        "+    raise ValueError(\"data cannot be None\")\n"
        "+result = process(data)\n"
    )
    explanation = (
        "Adds an explicit input guard before the failing call path. "
        "This prevents runtime crashes from null input and surfaces a clear error message."
    )
    tests = [
        "Add unit test for None/null input path",
        "Add regression test covering the reported stack trace scenario",
        "Add happy-path test ensuring behavior is unchanged",
    ]
    return RepairResponse(patch=patch, explanation=explanation, tests_to_add=tests, provider="fallback")


async def call_provider(messages: list[dict[str, str]]) -> str:
    base = os.getenv("AKASH_BASE_URL", "").strip()
    key = os.getenv("AKASH_API_KEY", "").strip()
    model = os.getenv("AKASH_MODEL", "").strip()
    timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    if not base or not key or not model:
        raise RuntimeError("provider_not_configured")

    url = f"{base.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.2}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    system = "You are a senior debugging engineer. Return strict JSON with keys severity, root_cause, confidence."
    user = (
        f"Language: {req.language}\n"
        f"Error:\n{req.error_log}\n\n"
        f"Code:\n{req.code}\n"
    )

    try:
        text = await call_provider([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
    except RuntimeError:
        return local_analyze(req)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider analyze failed: {exc}") from exc

    parsed = extract_json_object(text)
    if not parsed:
        return AnalyzeResponse(
            severity=severity_score(req.error_log),
            root_cause=text.strip(),
            confidence=82,
            provider="akashml",
        )

    return AnalyzeResponse(
        severity=str(parsed.get("severity") or severity_score(req.error_log)).lower(),
        root_cause=str(parsed.get("root_cause") or "No root cause returned by provider."),
        confidence=clamp_confidence(parsed.get("confidence")),
        provider="akashml",
    )


@app.post("/api/v1/repair", response_model=RepairResponse)
async def repair(req: RepairRequest) -> RepairResponse:
    system = "You are a code repair agent. Produce sections PATCH, EXPLANATION, TESTS."
    user = (
        f"Language: {req.language}\n"
        f"Strategy: {req.strategy}\n"
        f"Error:\n{req.error_log}\n\n"
        f"Code:\n{req.code}\n"
    )

    try:
        text = await call_provider([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
    except RuntimeError:
        return local_patch(req)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider repair failed: {exc}") from exc

    patch, explanation, tests = parse_repair_sections(text)
    return RepairResponse(
        patch=patch,
        explanation=explanation,
        tests_to_add=tests,
        provider="akashml",
    )
