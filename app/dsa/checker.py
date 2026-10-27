"""
ncode — DSA AI Checker
Sends problem + user code to Groq and returns a structured verdict.
Reuses the same urllib-only pattern as ai_transpiler.py.
"""
from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

# Reuse API config from the transpiler
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "qwen/qwen3.8-27b"   # fast + accurate for code review


@dataclass
class CheckResult:
    verdict: str           # "correct" | "incorrect" | "error"
    message: str           # human-readable summary
    issues: list[str]      # list of specific issues (empty if correct)
    edge_cases: list[str]  # edge cases that fail (empty if correct)
    complexity_ok: bool    # True if time/space is acceptable
    complexity_note: str   # details on complexity
    raw: str               # raw Groq response (for debugging)
    hint: str = ""         # hint for incorrect solutions


def _build_check_prompt(
    title: str,
    problem: str,
    constraints: str,
    req_time: str,
    req_space: str,
    language: str,
    code: str,
) -> str:
    return f"""You are an expert competitive programming judge.

PROBLEM: {title}
---
{problem}
---
CONSTRAINTS: {constraints}
REQUIRED TIME COMPLEXITY: {req_time}
REQUIRED SPACE COMPLEXITY: {req_space}

USER'S {language.upper()} SOLUTION:
```{language.lower()}
{code}
```

Evaluate the solution strictly. Respond with ONLY a valid JSON object (no markdown, no explanation outside JSON):

{{
  "verdict": "correct" | "incorrect",
  "message": "one-line summary of the result",
  "issues": ["issue 1", "issue 2"],
  "edge_cases": ["edge case that fails"],
  "complexity_ok": true | false,
  "complexity_note": "actual complexity of the solution and whether it meets requirements",
  "hint": "if incorrect, a conceptual hint (NOT the full solution)"
}}

Rules:
- verdict is "correct" only if logic is provably correct for ALL valid inputs.
- issues is [] if correct.
- edge_cases is [] if correct.
- hint is "" if correct.
- Do NOT output the full solution under any circumstances.
"""


def _parse_response(raw: str) -> CheckResult:
    """Parse Groq JSON response into CheckResult. Handles malformed output."""
    # Strip <think> tags (Qwen/DeepSeek reasoning models)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Extract JSON object from response
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        return CheckResult(
            verdict="error",
            message="Could not parse AI response. Please try again.",
            issues=[],
            edge_cases=[],
            complexity_ok=False,
            complexity_note="",
            raw=raw,
            hint="",
        )
    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return CheckResult(
            verdict="error",
            message=f"AI returned invalid JSON: {e}",
            issues=[],
            edge_cases=[],
            complexity_ok=False,
            complexity_note="",
            raw=raw,
            hint="",
        )

    verdict = str(data.get("verdict", "error")).lower()
    if verdict not in ("correct", "incorrect"):
        verdict = "incorrect"

    return CheckResult(
        verdict=verdict,
        message=str(data.get("message", "")),
        issues=list(data.get("issues", [])),
        edge_cases=list(data.get("edge_cases", [])),
        complexity_ok=bool(data.get("complexity_ok", False)),
        complexity_note=str(data.get("complexity_note", "")),
        hint=str(data.get("hint", "")),
        raw=raw,
    )


def _call_groq(api_key: str, prompt: str) -> str:
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict competitive programming judge. "
                    "Respond ONLY with valid JSON as instructed. "
                    "Never include markdown code fences around the JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()


def check_solution_async(
    question_title: str,
    problem_statement: str,
    constraints: str,
    req_time: str,
    req_space: str,
    language: str,
    code: str,
    api_key: str,
    on_success: Callable[[CheckResult], None],
    on_error: Callable[[str], None],
) -> None:
    """
    Run the AI check in a background thread.
    Calls on_success(CheckResult) or on_error(str) when done.
    Callbacks fire from a worker thread — use Qt signals to update UI.
    """

    def _worker() -> None:
        try:
            if not code.strip():
                on_error("Editor is empty — nothing to check.")
                return
            prompt = _build_check_prompt(
                question_title, problem_statement, constraints,
                req_time, req_space, language, code,
            )
            raw = _call_groq(api_key, prompt)
            result = _parse_response(raw)
            on_success(result)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code in (401, 403):
                on_error(
                    "Groq API key invalid or unauthorised.\n"
                    "Go to Settings → Preferences and enter a valid Groq key."
                )
            elif e.code == 429:
                on_error("Groq rate limit hit. Please wait a moment and try again.")
            else:
                on_error(f"Groq HTTP {e.code}: {body[:200]}")
        except urllib.error.URLError as e:
            on_error(
                f"Network error — cannot reach Groq API.\n"
                f"Check your internet connection.\n({e.reason})"
            )
        except TimeoutError:
            on_error("Groq API timed out (>30 s). Try again.")
        except Exception as e:  # noqa: BLE001
            on_error(f"Checker error: {e}")

    threading.Thread(target=_worker, daemon=True).start()
