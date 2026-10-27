"""
ncode — DSA Storage Layer Tests
Tests for app/dsa/storage.py — solution persistence, solved status, progress tracking.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# Patch the DB path to a temp file so tests don't pollute real data
import app.dsa.storage as _storage_module
_tmp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db_file.close()
_storage_module.SOLUTIONS_DB = Path(_tmp_db_file.name)

from app.dsa.storage import (
    init_solutions_db, save_solution, get_solution,
    get_solved_ids, get_progress,
)


def setup():
    """Initialize test DB."""
    init_solutions_db()


def test_save_and_get_solution():
    """Save a solution and retrieve it."""
    save_solution(question_id=1, language="Python", code="print('hello')", solved=True)
    sol = get_solution(1)
    assert sol is not None, "Solution should exist after save"
    assert sol.question_id == 1
    assert sol.language == "Python"
    assert sol.code == "print('hello')"
    assert sol.solved is True
    print("✓ save and retrieve solution")


def test_get_nonexistent_solution():
    """Getting a non-existent solution returns None."""
    sol = get_solution(99999)
    assert sol is None, "Non-existent question should return None"
    print("✓ get non-existent solution returns None")


def test_overwrite_solution():
    """Saving again with new code overwrites the old solution."""
    save_solution(2, "C++", "// old code", solved=False)
    save_solution(2, "C++", "// new code", solved=True)
    sol = get_solution(2)
    assert sol is not None
    assert sol.code == "// new code"
    assert sol.solved is True
    print("✓ overwrite existing solution")


def test_solved_ids():
    """get_solved_ids returns only solved questions."""
    save_solution(10, "Go", "// go code", solved=True)
    save_solution(11, "Rust", "// rust code", solved=False)

    solved = get_solved_ids()
    assert 10 in solved, "Question 10 should be solved"
    assert 11 not in solved, "Question 11 (solved=False) should not be in solved set"
    print("✓ solved_ids correctness")


def test_progress():
    """get_progress returns a dict with total_solved."""
    progress = get_progress()
    assert "total_solved" in progress
    assert isinstance(progress["total_solved"], int)
    assert progress["total_solved"] >= 0
    print(f"✓ progress tracking (total_solved={progress['total_solved']})")


def test_language_and_timestamp():
    """Saved solution stores language and timestamp."""
    import re
    save_solution(20, "JavaScript", "console.log(1)", solved=True)
    sol = get_solution(20)
    assert sol is not None
    assert sol.language == "JavaScript"
    # saved_at should be an ISO datetime string
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", sol.saved_at), \
        f"saved_at format wrong: {sol.saved_at!r}"
    print("✓ language and timestamp stored correctly")


def test_different_languages_same_question():
    """Re-saving the same question with a different language updates it."""
    save_solution(30, "Python", "# python", solved=True)
    save_solution(30, "Java", "// java", solved=True)
    sol = get_solution(30)
    assert sol is not None
    assert sol.language == "Java", "Language should be updated to Java"
    assert sol.code == "// java"
    print("✓ re-saving with different language updates correctly")


if __name__ == "__main__":
    print("\n" + "=" * 54)
    print("  ncode — DSA Storage Tests")
    print("=" * 54 + "\n")

    setup()
    tests = [
        test_save_and_get_solution,
        test_get_nonexistent_solution,
        test_overwrite_solution,
        test_solved_ids,
        test_progress,
        test_language_and_timestamp,
        test_different_languages_same_question,
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

    # Cleanup temp DB
    Path(_tmp_db_file.name).unlink(missing_ok=True)

    print(f"\n{'='*54}")
    print(f"  {len(tests)-failed}/{len(tests)} tests passed")
    print(f"{'='*54}\n")
    sys.exit(0 if failed == 0 else 1)
