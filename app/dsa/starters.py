"""
ncode — DSA Starter Code Templates
Generates language-specific comment blocks and function starters for DSA problems.
"""
from __future__ import annotations

from app.dsa.bank import Question


# Languages that get full DSA support (comment + starter)
SUPPORTED_LANGS = {
    "Python", "C", "C++", "Java", "JavaScript", "TypeScript",
    "Go", "Rust", "C#", "Kotlin", "Swift",
}


def make_comment_block(question: Question, language: str) -> str:
    """Return the problem statement formatted as a comment in the target language."""
    lines = [
        f"{'='*68}",
        f"  {question.title}",
        f"{'='*68}",
        f"  Source     : {question.source} DSA Sheet",
        f"  Topic      : {question.topic}",
        f"  Difficulty : {question.difficulty}",
        f"  LeetCode   : {'#' + str(question.lc_number) if question.lc_number else 'N/A'}",
        "",
        "  PROBLEM:",
        *[f"  {line}" for line in question.problem_statement.splitlines()],
        "",
    ]

    if question.examples:
        lines.append("  EXAMPLES:")
        for line in question.examples.splitlines():
            lines.append(f"  {line}")
        lines.append("")

    if question.constraints:
        lines.append("  CONSTRAINTS:")
        for line in question.constraints.splitlines():
            lines.append(f"  {line}")
        lines.append("")

    lines += [
        "  REQUIRED COMPLEXITY:",
        f"  Time  : {question.time_complexity}",
        f"  Space : {question.space_complexity}",
        f"{'='*68}",
    ]

    if language in ("C", "C++", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C#", "Kotlin", "Swift"):
        prefix = "// "
        block = "\n".join(f"{prefix}{line}".rstrip() for line in lines)
    else:
        # Python and fallback: # comment lines
        prefix = "# "
        block = "\n".join(f"{prefix}{line}".rstrip() for line in lines)

    return block


def make_starter_code(question: Question, language: str) -> str:
    """Return a minimal function starter for the given question and language."""
    # Generic starters keyed by (topic, language)
    # We generate a clean named function based on the problem title
    fn_name = _to_snake(question.title)
    class_name = _to_pascal(question.title)

    starters: dict[str, str] = {
        "Python": _py_starter(fn_name, question),
        "C++": _cpp_starter(fn_name, question),
        "Java": _java_starter(class_name, question),
        "JavaScript": _js_starter(fn_name, question),
        "TypeScript": _ts_starter(fn_name, question),
        "C": _c_starter(fn_name, question),
        "Go": _go_starter(fn_name, question),
        "Rust": _rust_starter(fn_name, question),
        "C#": _csharp_starter(class_name, question),
        "Kotlin": _kotlin_starter(fn_name, question),
        "Swift": _swift_starter(fn_name, question),
    }
    return starters.get(language, _generic_starter(language, fn_name))


def make_full_editor_content(question: Question, language: str, saved_code: str = "") -> str:
    """
    Build the complete editor content for a question tab.
    = comment block + starter code (or saved solution if available).
    """
    comment = make_comment_block(question, language)
    if saved_code.strip():
        # Reopen with saved solution — strip any old comment block prefix
        return comment + "\n\n" + saved_code.strip() + "\n"

    starter = make_starter_code(question, language)
    return comment + "\n\n" + starter + "\n"


# ── Language-specific starters ──────────────────────────────────────────────

def _py_starter(fn: str, q: Question) -> str:
    topic_hints = {
        "Arrays": "nums: list[int]",
        "Strings": "s: str",
        "Linked List": "head: Optional[ListNode]",
        "Trees": "root: Optional[TreeNode]",
        "Graphs": "graph: list[list[int]]",
        "Dynamic Programming": "nums: list[int]",
        "Backtracking": "nums: list[int]",
        "Binary Search": "nums: list[int], target: int",
        "Stack": "nums: list[int]",
        "Queue": "nums: list[int]",
        "Heap": "nums: list[int]",
        "Sliding Window": "nums: list[int], k: int",
        "Two Pointers": "nums: list[int]",
        "Hashing": "nums: list[int]",
        "Sorting": "nums: list[int]",
        "Math": "n: int",
        "Bit Manipulation": "n: int",
        "Recursion": "n: int",
        "Greedy": "nums: list[int]",
    }
    params = topic_hints.get(q.topic, "*args")
    return (
        f"from typing import Optional, List\n\n\n"
        f"class Solution:\n"
        f"    def {fn}(self, {params}):\n"
        f"        # Write your solution here\n"
        f"        pass\n\n\n"
        f"# ── Test your solution ──\n"
        f"if __name__ == '__main__':\n"
        f"    sol = Solution()\n"
        f"    # Example: sol.{fn}(...)\n"
    )


def _cpp_starter(fn: str, q: Question) -> str:
    return (
        f"#include <bits/stdc++.h>\n"
        f"using namespace std;\n\n\n"
        f"class Solution {{\n"
        f"public:\n"
        f"    // TODO: replace return type and parameters\n"
        f"    int {fn}(vector<int>& nums) {{\n"
        f"        // Write your solution here\n"
        f"        return 0;\n"
        f"    }}\n"
        f"}};\n\n\n"
        f"int main() {{\n"
        f"    Solution sol;\n"
        f"    // Test: sol.{fn}(...);\n"
        f"    return 0;\n"
        f"}}\n"
    )


def _java_starter(cls: str, q: Question) -> str:
    return (
        f"import java.util.*;\n\n\n"
        f"class Solution {{\n"
        f"    // TODO: adjust return type and parameters\n"
        f"    public int {_to_camel(q.title)}(int[] nums) {{\n"
        f"        // Write your solution here\n"
        f"        return 0;\n"
        f"    }}\n\n"
        f"    public static void main(String[] args) {{\n"
        f"        Solution sol = new Solution();\n"
        f"        // Test: sol.{_to_camel(q.title)}(...);\n"
        f"    }}\n"
        f"}}\n"
    )


def _js_starter(fn: str, q: Question) -> str:
    return (
        f"/**\n"
        f" * @param {{number[]}} nums\n"
        f" * @return {{number}}\n"
        f" */\n"
        f"var {_to_camel(q.title)} = function(nums) {{\n"
        f"    // Write your solution here\n"
        f"}};\n\n\n"
        f"// Test\n"
        f"console.log({_to_camel(q.title)}([]));\n"
    )


def _ts_starter(fn: str, q: Question) -> str:
    return (
        f"function {_to_camel(q.title)}(nums: number[]): number {{\n"
        f"    // Write your solution here\n"
        f"    return 0;\n"
        f"}};\n\n\n"
        f"// Test\n"
        f"console.log({_to_camel(q.title)}([]));\n"
    )


def _c_starter(fn: str, q: Question) -> str:
    return (
        f"#include <stdio.h>\n"
        f"#include <stdlib.h>\n\n\n"
        f"/* TODO: adjust return type and parameters */\n"
        f"int {fn}(int* nums, int numsSize) {{\n"
        f"    /* Write your solution here */\n"
        f"    return 0;\n"
        f"}}\n\n\n"
        f"int main(void) {{\n"
        f"    /* Test */\n"
        f"    return 0;\n"
        f"}}\n"
    )


def _go_starter(fn: str, q: Question) -> str:
    return (
        f"package main\n\n"
        f"import \"fmt\"\n\n\n"
        f"// TODO: adjust parameters and return type\n"
        f"func {_to_pascal(q.title)}(nums []int) int {{\n"
        f"    // Write your solution here\n"
        f"    return 0\n"
        f"}}\n\n\n"
        f"func main() {{\n"
        f"    fmt.Println({_to_pascal(q.title)}([]int{{}}))\n"
        f"}}\n"
    )


def _rust_starter(fn: str, q: Question) -> str:
    return (
        f"fn {fn}(nums: Vec<i32>) -> i32 {{\n"
        f"    // Write your solution here\n"
        f"    0\n"
        f"}}\n\n\n"
        f"fn main() {{\n"
        f"    println!(\"{{}}\", {fn}(vec![]));\n"
        f"}}\n"
    )


def _csharp_starter(cls: str, q: Question) -> str:
    return (
        f"using System;\n"
        f"using System.Collections.Generic;\n\n\n"
        f"public class Solution {{\n"
        f"    // TODO: adjust return type and parameters\n"
        f"    public int {_to_pascal(q.title)}(int[] nums) {{\n"
        f"        // Write your solution here\n"
        f"        return 0;\n"
        f"    }}\n\n"
        f"    static void Main() {{\n"
        f"        var sol = new Solution();\n"
        f"        // Test: sol.{_to_pascal(q.title)}(...);\n"
        f"    }}\n"
        f"}}\n"
    )


def _kotlin_starter(fn: str, q: Question) -> str:
    return (
        f"fun {_to_camel(q.title)}(nums: IntArray): Int {{\n"
        f"    // Write your solution here\n"
        f"    return 0\n"
        f"}}\n\n\n"
        f"fun main() {{\n"
        f"    println({_to_camel(q.title)}(intArrayOf()))\n"
        f"}}\n"
    )


def _swift_starter(fn: str, q: Question) -> str:
    return (
        f"func {_to_camel(q.title)}(_ nums: [Int]) -> Int {{\n"
        f"    // Write your solution here\n"
        f"    return 0\n"
        f"}}\n\n\n"
        f"print({_to_camel(q.title)}([]))\n"
    )


def _generic_starter(language: str, fn: str) -> str:
    return f"# {language} — write your solution for {fn} here\n"


# ── Name helpers ────────────────────────────────────────────────────────────

def _to_snake(title: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9 ]", "", title)
    name = "_".join(w.lower() for w in s.split()) or "solve"
    return f"solve_{name}" if name[0].isdigit() else name


def _to_pascal(title: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9 ]", "", title)
    name = "".join(w.capitalize() for w in s.split()) or "Solve"
    return f"Solve{name}" if name[0].isdigit() else name


def _to_camel(title: str) -> str:
    p = _to_pascal(title)
    return p[0].lower() + p[1:] if p else "solve"
