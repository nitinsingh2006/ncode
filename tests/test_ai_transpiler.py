import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
from app.ai_transpiler import can_transpile, _build_prompt, _call_groq_api, transpile_async

def test_can_transpile():
    assert can_transpile("C++", "Python") is True
    assert can_transpile("Python", "JavaScript") is True
    assert can_transpile("HTML", "Python") is True
    assert can_transpile("SQL", "C++") is True
    assert can_transpile("Rust", "Go") is True
    assert can_transpile("Python", "Python") is False  # same language does not transpile

def test_build_prompt():
    prompt = _build_prompt("cout << 123;", "C++", "Python")
    assert "C++" in prompt
    assert "Python" in prompt
    assert "cout << 123;" in prompt

@patch("urllib.request.urlopen")
def test_call_groq_api_strips_fences(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"choices":[{"message":{"content":"```python\\nprint(123)\\n```"}}]}'
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    res = _call_groq_api("dummy_key", "prompt")
    assert res == "print(123)"
