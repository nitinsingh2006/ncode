"""
ncode — DSA AI Checker Response Parser Tests
Tests for app/dsa/checker.py — structured Groq JSON response parsing.
Does NOT make real API calls; tests the parser against sample responses.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dsa.checker import _parse_response, CheckResult


def test_correct_verdict():
    raw = """
    {
      "verdict": "correct",
      "message": "The solution handles all cases correctly.",
      "issues": [],
      "edge_cases": [],
      "complexity_ok": true,
      "complexity_note": "O(n) time, O(1) space — meets requirements.",
      "hint": ""
    }
    """
    result = _parse_response(raw)
    assert result.verdict == "correct"
    assert result.complexity_ok is True
    assert result.issues == []
    assert result.edge_cases == []
    assert "O(n)" in result.complexity_note
    print("✓ correct verdict parsed")


def test_incorrect_verdict():
    raw = """
    {
      "verdict": "incorrect",
      "message": "Fails on negative numbers.",
      "issues": ["Does not handle negative input", "Missing edge case for empty array"],
      "edge_cases": ["nums = [-1, -2]", "nums = []"],
      "complexity_ok": false,
      "complexity_note": "O(n²) but O(n) required.",
      "hint": "Try using a hash map to track complements."
    }
    """
    result = _parse_response(raw)
    assert result.verdict == "incorrect"
    assert len(result.issues) == 2
    assert len(result.edge_cases) == 2
    assert result.complexity_ok is False
    assert "hash map" in result.raw
    print("✓ incorrect verdict parsed")


def test_think_tag_stripping():
    """Reasoning model <think> tags should be stripped before parsing."""
    raw = """<think>
    Let me evaluate this solution carefully...
    The user used a nested loop which is O(n²)...
    </think>
    {
      "verdict": "incorrect",
      "message": "Too slow.",
      "issues": ["O(n²) complexity"],
      "edge_cases": [],
      "complexity_ok": false,
      "complexity_note": "Needs O(n).",
      "hint": "Use a hash map."
    }
    """
    result = _parse_response(raw)
    assert result.verdict == "incorrect"
    assert "<think>" not in result.raw
    print("✓ <think> tags stripped correctly")


def test_markdown_fence_json():
    """JSON wrapped in markdown code fences is still parsed."""
    raw = """```json
    {
      "verdict": "correct",
      "message": "Perfect.",
      "issues": [],
      "edge_cases": [],
      "complexity_ok": true,
      "complexity_note": "O(n)",
      "hint": ""
    }
    ```"""
    result = _parse_response(raw)
    assert result.verdict == "correct"
    print("✓ markdown-fenced JSON parsed")


def test_malformed_json():
    """Malformed JSON returns error verdict gracefully."""
    result = _parse_response("This is not JSON at all.")
    assert result.verdict == "error"
    assert "parse" in result.message.lower() or "json" in result.message.lower()
    print("✓ malformed JSON handled gracefully")


def test_empty_response():
    """Empty string returns error verdict."""
    result = _parse_response("")
    assert result.verdict == "error"
    print("✓ empty response handled")


def test_extra_fields_ignored():
    """Extra fields in JSON don't cause crashes."""
    raw = """
    {
      "verdict": "correct",
      "message": "OK",
      "issues": [],
      "edge_cases": [],
      "complexity_ok": true,
      "complexity_note": "Fine.",
      "hint": "",
      "extra_field_that_does_not_exist": "should be ignored"
    }
    """
    result = _parse_response(raw)
    assert result.verdict == "correct"
    print("✓ extra JSON fields ignored safely")


def test_verdict_normalisation():
    """Unknown verdict values fall back to 'incorrect'."""
    raw = '{"verdict": "UNKNOWN_VALUE", "message": "", "issues": [], "edge_cases": [], "complexity_ok": false, "complexity_note": "", "hint": ""}'
    result = _parse_response(raw)
    assert result.verdict == "incorrect"
    print("✓ unknown verdict normalised to 'incorrect'")


if __name__ == "__main__":
    print("\n" + "=" * 54)
    print("  ncode — DSA Checker Parser Tests")
    print("=" * 54 + "\n")

    tests = [
        test_correct_verdict,
        test_incorrect_verdict,
        test_think_tag_stripping,
        test_markdown_fence_json,
        test_malformed_json,
        test_empty_response,
        test_extra_fields_ignored,
        test_verdict_normalisation,
    ]

    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"✗ FAIL {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*54}")
    print(f"  {len(tests)-failed}/{len(tests)} tests passed")
    print(f"{'='*54}\n")
    sys.exit(0 if failed == 0 else 1)
