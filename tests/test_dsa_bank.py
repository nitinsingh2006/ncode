"""ncode — DSA Question Bank Validation Tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dsa.bank import get_all_questions, init_db
from app.dsa.seed_questions import seed

VALID_SOURCES = {"Striver", "NeetCode", "Both"}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
VALID_TOPICS = {
    "Arrays", "Backtracking", "Binary Search", "Bit Manipulation",
    "Dynamic Programming", "Graphs", "Greedy", "Hashing", "Heap",
    "Intervals", "Linked List", "Math", "Matrix", "Sliding Window",
    "Sorting", "Stack", "Strings", "Trees", "Tries", "Two Pointers",
    "Design",
}


def setup_module():
    init_db()
    seed()


def test_questions_exist():
    questions = get_all_questions()
    assert len(questions) >= 61, f"Expected >= 61 questions, got {len(questions)}"


def test_unique_ids():
    questions = get_all_questions()
    ids = [q.id for q in questions]
    assert len(ids) == len(set(ids)), "Duplicate question IDs found"


def test_unique_titles():
    questions = get_all_questions()
    titles = [q.title for q in questions]
    assert len(titles) == len(set(titles)), "Duplicate titles found"


def test_all_required_fields_present():
    for q in get_all_questions():
        assert q.title.strip(), f"Question {q.id} has empty title"
        assert q.source.strip(), f"Question {q.id} ({q.title}) has empty source"
        assert q.topic.strip(), f"Question {q.id} ({q.title}) has empty topic"
        assert q.difficulty.strip(), f"Question {q.id} ({q.title}) has empty difficulty"
        assert q.problem_statement.strip(), f"Question {q.id} ({q.title}) has empty problem_statement"
        assert q.time_complexity.strip(), f"Question {q.id} ({q.title}) has empty time_complexity"
        assert q.space_complexity.strip(), f"Question {q.id} ({q.title}) has empty space_complexity"


def test_valid_source_values():
    for q in get_all_questions():
        assert q.source in VALID_SOURCES, f"Question {q.id} ({q.title}) has invalid source: {q.source}"


def test_valid_difficulty_values():
    for q in get_all_questions():
        assert q.difficulty in VALID_DIFFICULTIES, f"Question {q.id} ({q.title}) has invalid difficulty: {q.difficulty}"


def test_valid_topic_values():
    for q in get_all_questions():
        assert q.topic in VALID_TOPICS, f"Question {q.id} ({q.title}) has invalid topic: {q.topic}"


def test_lc_number_is_non_negative():
    for q in get_all_questions():
        assert q.lc_number >= 0, f"Question {q.id} ({q.title}) has negative lc_number"
