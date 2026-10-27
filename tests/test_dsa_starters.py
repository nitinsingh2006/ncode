"""ncode — DSA Starter Code and Comment Block Tests."""
import sys
import ast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dsa.bank import Question
from app.dsa.starters import (
    SUPPORTED_LANGS, make_comment_block, make_full_editor_content,
    make_starter_code,
)
from app.dsa.seed_questions import seed
from app.dsa.bank import get_all_questions

SAMPLE_Q = Question(
    id=999, title="Test Problem", source="Both", topic="Arrays",
    difficulty="Medium", problem_statement="Given an array, do something.",
    examples="Input: [1,2,3]\nOutput: 6", constraints="1 <= n <= 10^5",
    time_complexity="O(n)", space_complexity="O(1)", lc_number=1, tags="test",
)


def test_supported_langs_set():
    assert {"Python", "C++", "Java", "JavaScript"} <= SUPPORTED_LANGS
    assert len(SUPPORTED_LANGS) >= 11


def test_comment_blocks_for_all_supported_languages():
    for language in SUPPORTED_LANGS:
        block = make_comment_block(SAMPLE_Q, language)
        assert block.startswith("# " if language == "Python" else "// ")
        assert "Test Problem" in block


def test_comment_block_contains_all_sections():
    block = make_comment_block(SAMPLE_Q, "Python")
    for section in ("PROBLEM:", "EXAMPLES:", "CONSTRAINTS:", "REQUIRED COMPLEXITY:", "Source", "Difficulty"):
        assert section in block
    assert "O(n)" in block and "O(1)" in block


def test_starter_code_python():
    code = make_starter_code(SAMPLE_Q, "Python")
    assert "class Solution" in code and "def test_problem" in code and "pass" in code


def test_starter_code_cpp():
    code = make_starter_code(SAMPLE_Q, "C++")
    assert "class Solution" in code and "int main()" in code


def test_starter_code_java():
    code = make_starter_code(SAMPLE_Q, "Java")
    assert "class Solution" in code and "public static void main" in code


def test_starter_code_javascript():
    code = make_starter_code(SAMPLE_Q, "JavaScript")
    assert "function" in code or "var" in code


def test_starter_code_all_supported_langs():
    for language in SUPPORTED_LANGS:
        assert len(make_starter_code(SAMPLE_Q, language)) > 10


def test_full_editor_content_without_saved():
    content = make_full_editor_content(SAMPLE_Q, "Python")
    assert "Test Problem" in content and "class Solution" in content


def test_full_editor_content_with_saved():
    content = make_full_editor_content(SAMPLE_Q, "Python", saved_code="def my_solution(): return 42")
    assert "Test Problem" in content and "def my_solution(): return 42" in content
    assert "class Solution" not in content


def test_unsupported_lang_fallback():
    assert len(make_starter_code(SAMPLE_Q, "Lua")) > 5


def test_python_starters_parse_for_every_bank_question():
    seed()
    for question in get_all_questions():
        ast.parse(make_starter_code(question, "Python"))
