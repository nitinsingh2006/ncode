"""
Nitin Editor - ai_transpiler.py
AI-powered code transpiler using Groq API (llama-3.3-70b-versatile).
Converts code from one programming language to another while preserving logic and output.
No extra pip packages needed — uses stdlib urllib only.
"""
from __future__ import annotations

import threading
import urllib.request
import urllib.error
import json
from typing import Callable


# ── Groq API settings ────────────────────────────────────────────────────────

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "qwen/qwen3.8-27b"   # available on this account, great for code

# Languages that support transpilation (exclude markup/query langs)
TRANSPILABLE_LANGUAGES = {"Python", "C", "C++", "Java", "JavaScript"}


# ── Prompt builder ───────────────────────────────────────────────────────────

def _build_prompt(code: str, from_lang: str, to_lang: str) -> str:
    return (
        f"You are a precise code transpiler. Convert the following {from_lang} code "
        f"to {to_lang}.\n\n"
        "STRICT RULES:\n"
        "1. Preserve the EXACT same logic and output — the program must produce "
        "identical results in the target language.\n"
        "2. Use idiomatic, clean syntax of the target language.\n"
        "3. Return ONLY the raw source code — NO explanation, NO markdown, "
        "NO triple-backtick fences.\n"
        "4. Adapt comments to the target language's comment style.\n\n"
        f"=== {from_lang} SOURCE ===\n"
        f"{code}\n"
        f"=== END SOURCE ===\n\n"
        f"Output the {to_lang} code only:"
    )


# ── Groq API caller ──────────────────────────────────────────────────────────

def _call_groq_api(api_key: str, prompt: str) -> str:
    """
    Synchronously call the Groq Chat Completions API.
    Returns the generated text or raises an exception.
    """
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert code transpiler. "
                    "You output only raw source code, never markdown or explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            # Cloudflare on Groq blocks Python-urllib user-agent; spoof a browser
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    text = result["choices"][0]["message"]["content"].strip()

    # Strip accidental code fences
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    return text


# ── Public API ───────────────────────────────────────────────────────────────

def can_transpile(from_lang: str, to_lang: str) -> bool:
    """Return True if both languages are supported for transpilation."""
    return from_lang in TRANSPILABLE_LANGUAGES and to_lang in TRANSPILABLE_LANGUAGES


def transpile_async(
    code: str,
    from_lang: str,
    to_lang: str,
    api_key: str,
    on_success: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    """
    Start a background thread to transpile code via Groq API.
    Calls on_success(converted_code) or on_error(error_message) on completion.
    Callbacks are invoked from a worker thread — use Qt signals to update UI.
    """

    def _worker() -> None:
        try:
            if not code.strip():
                on_error("Editor is empty — nothing to transpile.")
                return
            prompt = _build_prompt(code, from_lang, to_lang)
            converted = _call_groq_api(api_key, prompt)
            if converted:
                on_success(converted)
            else:
                on_error("Groq returned an empty response.")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code in (401, 403):
                on_error(
                    "Groq API key invalid or unauthorised.\n"
                    "Go to Settings → AI Transpiler → enter a valid key."
                )
            elif e.code == 429:
                on_error("Groq rate limit hit. Please wait a moment and try again.")
            else:
                on_error(f"Groq HTTP error {e.code}: {body[:200]}")
        except urllib.error.URLError as e:
            on_error(
                f"Network error — could not reach Groq API.\n"
                f"Check your internet connection.\n({e.reason})"
            )
        except TimeoutError:
            on_error("Groq API timed out (>15 s). Try again.")
        except Exception as e:  # noqa: BLE001
            on_error(f"Transpiler error: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
