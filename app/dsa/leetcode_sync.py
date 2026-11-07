"""
ncode — LeetCode Sync Helper
Maps DSA question titles to LeetCode slugs and provides URL/browser utilities.
No external dependencies — uses stdlib webbrowser module.
"""
from __future__ import annotations

import webbrowser

# Maps lowercased title keywords → LeetCode slug
# Covers common questions from Striver's SDE Sheet and NeetCode 150
TITLE_TO_SLUG: dict[str, str] = {
    # Arrays / Hashing
    "two sum": "two-sum",
    "best time to buy and sell stock": "best-time-to-buy-and-sell-stock",
    "contains duplicate": "contains-duplicate",
    "product of array except self": "product-of-array-except-self",
    "maximum subarray": "maximum-subarray",
    "maximum product subarray": "maximum-product-subarray",
    "find minimum in rotated sorted array": "find-minimum-in-rotated-sorted-array",
    "search in rotated sorted array": "search-in-rotated-sorted-array",
    "3sum": "3sum",
    "container with most water": "container-with-most-water",
    "valid anagram": "valid-anagram",
    "group anagrams": "group-anagrams",
    "top k frequent elements": "top-k-frequent-elements",
    "encode and decode strings": "encode-and-decode-strings",
    "longest consecutive sequence": "longest-consecutive-sequence",
    "sort colors": "sort-colors",
    "set matrix zeroes": "set-matrix-zeroes",
    "spiral matrix": "spiral-matrix",
    "rotate image": "rotate-image",
    "word search": "word-search",
    # Binary Search
    "binary search": "binary-search",
    "search a 2d matrix": "search-a-2d-matrix",
    "koko eating bananas": "koko-eating-bananas",
    "find the duplicate number": "find-the-duplicate-number",
    "median of two sorted arrays": "median-of-two-sorted-arrays",
    "time based key value store": "time-based-key-value-store",
    # Linked List
    "reverse linked list": "reverse-linked-list",
    "merge two sorted lists": "merge-two-sorted-lists",
    "linked list cycle": "linked-list-cycle",
    "reorder list": "reorder-list",
    "remove nth node from end of list": "remove-nth-node-from-end-of-list",
    "copy list with random pointer": "copy-list-with-random-pointer",
    "add two numbers": "add-two-numbers",
    "lru cache": "lru-cache",
    "merge k sorted lists": "merge-k-sorted-lists",
    "reverse nodes in k group": "reverse-nodes-in-k-group",
    "find the starting point of the loop in a linked list": "linked-list-cycle-ii",
    "linked list cycle ii": "linked-list-cycle-ii",
    "middle of the linked list": "middle-of-the-linked-list",
    "palindrome linked list": "palindrome-linked-list",
    "intersection of two linked lists": "intersection-of-two-linked-lists",
    # Trees
    "invert binary tree": "invert-binary-tree",
    "maximum depth of binary tree": "maximum-depth-of-binary-tree",
    "diameter of binary tree": "diameter-of-binary-tree",
    "balanced binary tree": "balanced-binary-tree",
    "same tree": "same-tree",
    "subtree of another tree": "subtree-of-another-tree",
    "lowest common ancestor of a binary search tree": "lowest-common-ancestor-of-a-binary-search-tree",
    "binary tree level order traversal": "binary-tree-level-order-traversal",
    "binary tree right side view": "binary-tree-right-side-view",
    "count good nodes in binary tree": "count-good-nodes-in-binary-tree",
    "validate binary search tree": "validate-binary-search-tree",
    "kth smallest element in a bst": "kth-smallest-element-in-a-bst",
    "construct binary tree from preorder and inorder traversal": "construct-binary-tree-from-preorder-and-inorder-traversal",
    "binary tree maximum path sum": "binary-tree-maximum-path-sum",
    "serialize and deserialize binary tree": "serialize-and-deserialize-binary-tree",
    "word ladder": "word-ladder",
    # Graphs
    "number of islands": "number-of-islands",
    "clone graph": "clone-graph",
    "max area of island": "max-area-of-island",
    "pacific atlantic water flow": "pacific-atlantic-water-flow",
    "surrounded regions": "surrounded-regions",
    "rotting oranges": "rotting-oranges",
    "walls and gates": "walls-and-gates",
    "course schedule": "course-schedule",
    "course schedule ii": "course-schedule-ii",
    "redundant connection": "redundant-connection",
    "number of connected components in an undirected graph": "number-of-connected-components-in-an-undirected-graph",
    "graph valid tree": "graph-valid-tree",
    "minimum height trees": "minimum-height-trees",
    "alien dictionary": "alien-dictionary",
    # Dynamic Programming
    "climbing stairs": "climbing-stairs",
    "min cost climbing stairs": "min-cost-climbing-stairs",
    "house robber": "house-robber",
    "house robber ii": "house-robber-ii",
    "longest palindromic substring": "longest-palindromic-substring",
    "palindromic substrings": "palindromic-substrings",
    "decode ways": "decode-ways",
    "coin change": "coin-change",
    "maximum product subarray": "maximum-product-subarray",
    "word break": "word-break",
    "longest increasing subsequence": "longest-increasing-subsequence",
    "partition equal subset sum": "partition-equal-subset-sum",
    "target sum": "target-sum",
    "interleaving string": "interleaving-string",
    "edit distance": "edit-distance",
    "unique paths": "unique-paths",
    "jump game": "jump-game",
    "jump game ii": "jump-game-ii",
    # Intervals
    "insert interval": "insert-interval",
    "merge intervals": "merge-intervals",
    "non overlapping intervals": "non-overlapping-intervals",
    "meeting rooms": "meeting-rooms",
    "meeting rooms ii": "meeting-rooms-ii",
    "minimum interval to include each query": "minimum-interval-to-include-each-query",
    # Stack
    "valid parentheses": "valid-parentheses",
    "min stack": "min-stack",
    "evaluate reverse polish notation": "evaluate-reverse-polish-notation",
    "generate parentheses": "generate-parentheses",
    "daily temperatures": "daily-temperatures",
    "car fleet": "car-fleet",
    "largest rectangle in histogram": "largest-rectangle-in-histogram",
    # Sliding Window
    "best time to buy and sell stock ii": "best-time-to-buy-and-sell-stock-ii",
    "longest substring without repeating characters": "longest-substring-without-repeating-characters",
    "longest repeating character replacement": "longest-repeating-character-replacement",
    "permutation in string": "permutation-in-string",
    "minimum window substring": "minimum-window-substring",
    "sliding window maximum": "sliding-window-maximum",
    # Backtracking
    "permutations": "permutations",
    "subsets": "subsets",
    "combination sum": "combination-sum",
    "combination sum ii": "combination-sum-ii",
    "subsets ii": "subsets-ii",
    "letter combinations of a phone number": "letter-combinations-of-a-phone-number",
    "n queens": "n-queens",
    "palindrome partitioning": "palindrome-partitioning",
    # Heap / Priority Queue
    "kth largest element in a stream": "kth-largest-element-in-a-stream",
    "last stone weight": "last-stone-weight",
    "k closest points to origin": "k-closest-points-to-origin",
    "kth largest element in an array": "kth-largest-element-in-an-array",
    "task scheduler": "task-scheduler",
    "design twitter": "design-twitter",
    "find median from data stream": "find-median-from-data-stream",
    # Trie
    "implement trie prefix tree": "implement-trie-prefix-tree",
    "design add and search words data structure": "design-add-and-search-words-data-structure",
    "word search ii": "word-search-ii",
    # Bit Manipulation
    "number of 1 bits": "number-of-1-bits",
    "counting bits": "counting-bits",
    "reverse bits": "reverse-bits",
    "missing number": "missing-number",
    "sum of two integers": "sum-of-two-integers",
    "single number": "single-number",
    "reverse integer": "reverse-integer",
    # Math
    "rotate array": "rotate-array",
    "pow(x, n)": "powx-n",
    "sqrt(x)": "sqrtx",
    "plus one": "plus-one",
    "happy number": "happy-number",
}

_LEETCODE_BASE = "https://leetcode.com/problems/"


def _normalize(title: str) -> str:
    """Lowercase and strip punctuation for fuzzy matching."""
    return title.lower().strip()


def get_leetcode_slug(question_title: str) -> str | None:
    """Return LeetCode slug for a question title, or None if unknown."""
    normalized = _normalize(question_title)
    # Exact match
    if normalized in TITLE_TO_SLUG:
        return TITLE_TO_SLUG[normalized]
    # Partial / substring match
    for key, slug in TITLE_TO_SLUG.items():
        if key in normalized or normalized in key:
            return slug
    return None


def get_leetcode_url(question_title: str) -> str | None:
    """Return full LeetCode URL for a question title, or None if unknown."""
    slug = get_leetcode_slug(question_title)
    if slug:
        return f"{_LEETCODE_BASE}{slug}/"
    return None


def open_leetcode(question_title: str) -> bool:
    """Open LeetCode URL in default browser. Returns True if URL found."""
    url = get_leetcode_url(question_title)
    if url:
        webbrowser.open(url)
        return True
    return False
