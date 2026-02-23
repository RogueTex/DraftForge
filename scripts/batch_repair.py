#!/usr/bin/env python3
"""Batch process code repair jobs from JSONL through the DraftForge API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch code-repair jobs against DraftForge API")
    parser.add_argument("--api-url", default="http://localhost:8010", help="DraftForge API base URL")
    parser.add_argument("--input", required=True, help="Input JSONL path")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout seconds")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    data = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text(f"{data}\n" if data else "", encoding="utf-8")


def run_job(client: httpx.Client, api_url: str, job: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "language": job.get("language", "python"),
        "error_log": job["error_log"],
        "code": job["code"],
        "strategy": job.get("strategy", "minimal_patch"),
    }
    response = client.post(f"{api_url.rstrip('/')}/api/v1/repair", json=payload)
    response.raise_for_status()
    body = response.json()
    return {
        "id": job.get("id"),
        "language": payload["language"],
        "strategy": payload["strategy"],
        "provider": body.get("provider"),
        "patch": body.get("patch"),
        "explanation": body.get("explanation"),
        "tests_to_add": body.get("tests_to_add", []),
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    jobs = load_jsonl(input_path)

    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=args.timeout) as client:
        for job in jobs:
            try:
                results.append(run_job(client, args.api_url, job))
            except Exception as exc:  # noqa: BLE001
                results.append({
                    "id": job.get("id"),
                    "error": str(exc),
                    "status": "failed",
                })

    write_jsonl(output_path, results)
    print(f"Processed {len(jobs)} jobs -> {output_path}")


if __name__ == "__main__":
    main()
