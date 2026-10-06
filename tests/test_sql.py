"""
Nitin Editor — Unit tests for SQL execution and formatting (app/sql)
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.sql.executor import SQLExecutor, SQLResult
from app.sql.formatter import format_table, format_rowcount


def test_statement_splitter():
    executor = SQLExecutor()
    sql = """
    -- Comment line
    CREATE TABLE t (id INT);
    INSERT INTO t VALUES (1); -- inline comment
    SELECT * FROM t;
    """
    stmts = executor._split_statements(sql)
    assert len(stmts) == 3, f"Expected 3 statements, got {len(stmts)}: {stmts}"
    print("✓ SQL statement splitter")


def test_sql_create_insert_select():
    executor = SQLExecutor()
    sql = """
    CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, marks INTEGER);
    INSERT INTO students VALUES (1, 'Amit', 85), (2, 'Rahul', 92);
    SELECT * FROM students;
    """
    res = executor.execute(sql)
    assert res.success, f"Error: {res.error}"
    assert "Amit" in res.output
    assert "Rahul" in res.output
    assert "+----+-------+-------+" in res.output
    print("✓ SQL CREATE, INSERT, SELECT execution")


def test_sql_update_delete_join():
    executor = SQLExecutor()
    sql = """
    CREATE TABLE dept (id INT, dname TEXT);
    CREATE TABLE emp (id INT, ename TEXT, dept_id INT);
    INSERT INTO dept VALUES (1, 'IT'), (2, 'HR');
    INSERT INTO emp VALUES (101, 'Alice', 1), (102, 'Bob', 2);
    UPDATE emp SET ename = 'Alice Smith' WHERE id = 101;
    DELETE FROM emp WHERE id = 102;
    SELECT e.id, e.ename, d.dname FROM emp e JOIN dept d ON e.dept_id = d.id;
    """
    res = executor.execute(sql)
    assert res.success, f"Error: {res.error}"
    assert "Alice Smith" in res.output
    assert "IT" in res.output
    print("✓ SQL UPDATE, DELETE, JOIN execution")


def test_sql_invalid():
    executor = SQLExecutor()
    sql = "SELEC * FROM non_existent_table;"
    res = executor.execute(sql)
    assert not res.success
    assert "SQL Error" in res.output or "syntax error" in res.output.lower()
    print("✓ SQL syntax error handling")


def test_sql_empty():
    executor = SQLExecutor()
    res = executor.execute("  \n -- only comments\n ")
    assert not res.success
    assert "No SQL" in res.output
    print("✓ SQL empty query handling")


def test_sql_result_formatting():
    headers = ["id", "name", "marks"]
    rows = [(1, "Amit", 85), (2, "Rahul", 92)]
    formatted = format_table(headers, rows)
    assert "+----+-------+-------+" in formatted
    assert "| 1  | Amit  | 85    |" in formatted
    assert "| 2  | Rahul | 92    |" in formatted
    assert "2 row(s) returned." in formatted
    print("✓ SQL ASCII result table formatting")


def test_sql_temp_db_cleanup():
    executor = SQLExecutor()
    sql = "CREATE TABLE temp_t (x INT); INSERT INTO temp_t VALUES (10);"
    res = executor.execute(sql)
    assert res.success
    assert executor._temp_db_path is None  # Should be cleaned up after execution
    print("✓ SQL temp database cleanup")


def test_sql_opened_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_file = Path(f.name)

    try:
        # Write table into opened DB directly first
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE t (x INT);")
        conn.execute("INSERT INTO t VALUES (42);")
        conn.commit()
        conn.close()

        # Run via SQLExecutor targeting file
        executor = SQLExecutor()
        res = executor.execute("SELECT * FROM t;", db_path=db_file)
        assert res.success
        assert "42" in res.output
    finally:
        if db_file.exists():
            db_file.unlink()
    print("✓ SQL opened .db database file mode")


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — SQL Tests")
    print("======================================================\n")

    tests = [
        test_statement_splitter,
        test_sql_create_insert_select,
        test_sql_update_delete_join,
        test_sql_invalid,
        test_sql_empty,
        test_sql_result_formatting,
        test_sql_temp_db_cleanup,
        test_sql_opened_db,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*54}")
    print(f"  {len(tests)-failed}/{len(tests)} tests passed")
    print(f"{'='*54}\n")

    sys.exit(0 if failed == 0 else 1)
