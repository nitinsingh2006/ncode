"""
ncode — DSA Question Bank Seeder
Seeds the SQLite question bank with Striver's SDE Sheet and NeetCode 150 questions.
Run once: python -m app.dsa.seed_questions
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Make the project root importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.dsa.bank import DB_PATH, init_db


# ── Question definitions ─────────────────────────────────────────────────────
# Format: (title, source, topic, difficulty, lc_number, problem_statement, examples, constraints, time_complexity, space_complexity, tags)

QUESTIONS = [
    # ── Arrays ──
    (
        "Two Sum", "Both", "Arrays", "Easy", 1,
        "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: nums[0] + nums[1] == 9\n\nInput: nums = [3,2,4], target = 6\nOutput: [1,2]",
        "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nOnly one valid answer exists.",
        "O(n)", "O(n)",
        "hash map,complement"
    ),
    (
        "Best Time to Buy and Sell Stock", "Both", "Arrays", "Easy", 121,
        "You are given an array prices where prices[i] is the price of a given stock on the ith day.\nYou want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.\nReturn the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return 0.",
        "Input: prices = [7,1,5,3,6,4]\nOutput: 5\nExplanation: Buy on day 2 (price=1) and sell on day 5 (price=6), profit = 6-1 = 5.\n\nInput: prices = [7,6,4,3,1]\nOutput: 0",
        "1 <= prices.length <= 10^5\n0 <= prices[i] <= 10^4",
        "O(n)", "O(1)",
        "greedy,sliding window"
    ),
    (
        "Contains Duplicate", "NeetCode", "Arrays", "Easy", 217,
        "Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
        "Input: nums = [1,2,3,1]\nOutput: true\n\nInput: nums = [1,2,3,4]\nOutput: false",
        "1 <= nums.length <= 10^5\n-10^9 <= nums[i] <= 10^9",
        "O(n)", "O(n)",
        "hash set"
    ),
    (
        "Maximum Subarray", "Both", "Arrays", "Medium", 53,
        "Given an integer array nums, find the subarray with the largest sum, and return its sum.\n(Kadane's Algorithm)",
        "Input: nums = [-2,1,-3,4,-1,2,1,-5,4]\nOutput: 6\nExplanation: The subarray [4,-1,2,1] has the largest sum 6.\n\nInput: nums = [1]\nOutput: 1",
        "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
        "O(n)", "O(1)",
        "kadane,dp,greedy"
    ),
    (
        "Product of Array Except Self", "Both", "Arrays", "Medium", 238,
        "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].\nThe product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer.\nYou must write an algorithm that runs in O(n) time and without using the division operation.",
        "Input: nums = [1,2,3,4]\nOutput: [24,12,8,6]\n\nInput: nums = [-1,1,0,-3,3]\nOutput: [0,0,9,0,0]",
        "2 <= nums.length <= 10^5\n-30 <= nums[i] <= 30\nThe product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer.",
        "O(n)", "O(1) (excluding output array)",
        "prefix,suffix,product"
    ),
    (
        "Maximum Product Subarray", "Striver", "Arrays", "Medium", 152,
        "Given an integer array nums, find a subarray that has the largest product, and return the product.\nThe test cases are generated so that the answer will fit in a 32-bit integer.",
        "Input: nums = [2,3,-2,4]\nOutput: 6\nExplanation: [2,3] has the largest product 6.\n\nInput: nums = [-2,0,-1]\nOutput: 0",
        "1 <= nums.length <= 2 * 10^4\n-10 <= nums[i] <= 10\nThe product of any subarray of nums is guaranteed to fit in a 32-bit integer.",
        "O(n)", "O(1)",
        "dp,greedy,prefix"
    ),
    (
        "Find Minimum in Rotated Sorted Array", "Both", "Arrays", "Medium", 153,
        "Suppose an array of length n sorted in ascending order is rotated between 1 and n times.\nGiven the sorted rotated array nums of unique elements, return the minimum element of this array.\nYou must write an algorithm that runs in O(log n) time.",
        "Input: nums = [3,4,5,1,2]\nOutput: 1\n\nInput: nums = [4,5,6,7,0,1,2]\nOutput: 0",
        "n == nums.length\n1 <= n <= 5000\n-5000 <= nums[i] <= 5000\nAll the integers of nums are unique.",
        "O(log n)", "O(1)",
        "binary search,rotation"
    ),
    (
        "Search in Rotated Sorted Array", "Both", "Arrays", "Medium", 33,
        "There is an integer array nums sorted in ascending order (with distinct values). Given the array nums after the possible rotation and an integer target, return the index of target if it is in nums, or -1 if it is not in nums.\nYou must write an algorithm with O(log n) runtime complexity.",
        "Input: nums = [4,5,6,7,0,1,2], target = 0\nOutput: 4\n\nInput: nums = [4,5,6,7,0,1,2], target = 3\nOutput: -1",
        "1 <= nums.length <= 5000\n-10^4 <= nums[i] <= 10^4\nAll values of nums are unique.",
        "O(log n)", "O(1)",
        "binary search,rotation"
    ),
    (
        "3Sum", "Both", "Arrays", "Medium", 15,
        "Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.\nNotice that the solution set must not contain duplicate triplets.",
        "Input: nums = [-1,0,1,2,-1,-4]\nOutput: [[-1,-1,2],[-1,0,1]]\n\nInput: nums = [0,1,1]\nOutput: []",
        "3 <= nums.length <= 3000\n-10^5 <= nums[i] <= 10^5",
        "O(n²)", "O(n) (for output)",
        "two pointers,sorting"
    ),
    (
        "Container With Most Water", "Both", "Arrays", "Medium", 11,
        "You are given an integer array height of length n. There are n vertical lines drawn such that the two endpoints of the ith line are (i, 0) and (i, height[i]).\nFind two lines that together with the x-axis form a container, such that the container contains the most water.\nReturn the maximum amount of water a container can store.",
        "Input: height = [1,8,6,2,5,4,8,3,7]\nOutput: 49\n\nInput: height = [1,1]\nOutput: 1",
        "n == height.length\n2 <= n <= 10^5\n0 <= height[i] <= 10^4",
        "O(n)", "O(1)",
        "two pointers,greedy"
    ),
    # ── Linked List ──
    (
        "Reverse Linked List", "Both", "Linked List", "Easy", 206,
        "Given the head of a singly linked list, reverse the list, and return the reversed list.",
        "Input: head = [1,2,3,4,5]\nOutput: [5,4,3,2,1]\n\nInput: head = [1,2]\nOutput: [2,1]",
        "The number of nodes in the list is in the range [0, 5000].\n-5000 <= Node.val <= 5000",
        "O(n)", "O(1)",
        "iteration,recursion"
    ),
    (
        "Linked List Cycle", "Both", "Linked List", "Easy", 141,
        "Given head, the head of a linked list, determine if the linked list has a cycle in it.\nReturn true if there is a cycle in the linked list. Otherwise, return false.",
        "Input: head = [3,2,0,-4], pos = 1\nOutput: true\n\nInput: head = [1,2], pos = 0\nOutput: true\n\nInput: head = [1], pos = -1\nOutput: false",
        "The number of the nodes in the list is in the range [0, 10^4].\n-10^5 <= Node.val <= 10^5\npos is -1 or a valid index in the linked-list.",
        "O(n)", "O(1)",
        "floyd's cycle detection,tortoise and hare"
    ),
    (
        "Merge Two Sorted Lists", "Both", "Linked List", "Easy", 21,
        "You are given the heads of two sorted linked lists list1 and list2.\nMerge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists.\nReturn the head of the merged linked list.",
        "Input: list1 = [1,2,4], list2 = [1,3,4]\nOutput: [1,1,2,3,4,4]\n\nInput: list1 = [], list2 = []\nOutput: []",
        "The number of nodes in both lists is in the range [0, 50].\n-100 <= Node.val <= 100\nBoth list1 and list2 are sorted in non-decreasing order.",
        "O(n + m)", "O(1)",
        "merge,recursion"
    ),
    (
        "Remove Nth Node From End of List", "Striver", "Linked List", "Medium", 19,
        "Given the head of a linked list, remove the nth node from the end of the list and return its head.",
        "Input: head = [1,2,3,4,5], n = 2\nOutput: [1,2,3,5]\n\nInput: head = [1], n = 1\nOutput: []\n\nInput: head = [1,2], n = 1\nOutput: [1]",
        "The number of nodes in the list is sz.\n1 <= sz <= 30\n0 <= Node.val <= 100\n1 <= n <= sz",
        "O(n)", "O(1)",
        "two pointers,fast slow"
    ),
    (
        "Merge K Sorted Lists", "Both", "Linked List", "Hard", 23,
        "You are given an array of k linked-lists lists, each linked-list is sorted in ascending order.\nMerge all the linked-lists into one sorted linked-list and return it.",
        "Input: lists = [[1,4,5],[1,3,4],[2,6]]\nOutput: [1,1,2,3,4,4,5,6]\n\nInput: lists = []\nOutput: []",
        "k == lists.length\n0 <= k <= 10^4\n0 <= lists[i].length <= 500\n-10^4 <= lists[i][j] <= 10^4\nlists[i] is sorted in ascending order.",
        "O(n log k)", "O(k)",
        "heap,divide and conquer,merge"
    ),
    # ── Trees ──
    (
        "Invert Binary Tree", "NeetCode", "Trees", "Easy", 226,
        "Given the root of a binary tree, invert the tree, and return its root.",
        "Input: root = [4,2,7,1,3,6,9]\nOutput: [4,7,2,9,6,3,1]\n\nInput: root = [2,1,3]\nOutput: [2,3,1]",
        "The number of nodes in the tree is in the range [0, 100].\n-100 <= Node.val <= 100",
        "O(n)", "O(h) where h = tree height",
        "dfs,bfs,recursion"
    ),
    (
        "Maximum Depth of Binary Tree", "Both", "Trees", "Easy", 104,
        "Given the root of a binary tree, return its maximum depth.\nA binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.",
        "Input: root = [3,9,20,null,null,15,7]\nOutput: 3\n\nInput: root = [1,null,2]\nOutput: 2",
        "The number of nodes in the tree is in the range [0, 10^4].\n-100 <= Node.val <= 100",
        "O(n)", "O(h)",
        "dfs,bfs,recursion"
    ),
    (
        "Diameter of Binary Tree", "Striver", "Trees", "Easy", 543,
        "Given the root of a binary tree, return the length of the diameter of the tree.\nThe diameter of a binary tree is the length of the longest path between any two nodes in a tree. This path may or may not pass through the root.",
        "Input: root = [1,2,3,4,5]\nOutput: 3\nExplanation: 3 is the length of the path [4,2,1,3] or [5,2,1,3].\n\nInput: root = [1,2]\nOutput: 1",
        "The number of nodes in the tree is in the range [1, 10^4].\n-100 <= Node.val <= 100",
        "O(n)", "O(h)",
        "dfs,recursion"
    ),
    (
        "Balanced Binary Tree", "Striver", "Trees", "Easy", 110,
        "Given a binary tree, determine if it is height-balanced.\nA height-balanced binary tree is a binary tree in which the depth of the two subtrees of every node never differs by more than one.",
        "Input: root = [3,9,20,null,null,15,7]\nOutput: true\n\nInput: root = [1,2,2,3,3,null,null,4,4]\nOutput: false",
        "The number of nodes in the tree is in the range [0, 5000].\n-10^4 <= Node.val <= 10^4",
        "O(n)", "O(h)",
        "dfs,recursion"
    ),
    (
        "Binary Tree Level Order Traversal", "Both", "Trees", "Medium", 102,
        "Given the root of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).",
        "Input: root = [3,9,20,null,null,15,7]\nOutput: [[3],[9,20],[15,7]]\n\nInput: root = [1]\nOutput: [[1]]",
        "The number of nodes in the tree is in the range [0, 2000].\n-1000 <= Node.val <= 1000",
        "O(n)", "O(n)",
        "bfs,queue"
    ),
    (
        "Lowest Common Ancestor of a BST", "Both", "Trees", "Medium", 235,
        "Given a binary search tree (BST), find the lowest common ancestor (LCA) node of two given nodes in the BST.\nThe LCA is defined as the lowest node in T that has both p and q as descendants (a node can be a descendant of itself).",
        "Input: root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8\nOutput: 6\n\nInput: root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4\nOutput: 2",
        "The number of nodes in the tree is in the range [2, 10^5].\n-10^9 <= Node.val <= 10^9\nAll Node.val are unique.",
        "O(h)", "O(1)",
        "bst,recursion,dfs"
    ),
    (
        "Binary Tree Right Side View", "NeetCode", "Trees", "Medium", 199,
        "Given the root of a binary tree, imagine yourself standing on the right side of it, return the values of the nodes you can see ordered from top to bottom.",
        "Input: root = [1,2,3,null,5,null,4]\nOutput: [1,3,4]\n\nInput: root = [1,null,3]\nOutput: [1,3]",
        "The number of nodes in the tree is in the range [0, 100].\n-100 <= Node.val <= 100",
        "O(n)", "O(n)",
        "bfs,dfs,level order"
    ),
    (
        "Validate Binary Search Tree", "Both", "Trees", "Medium", 98,
        "Given the root of a binary tree, determine if it is a valid binary search tree (BST).\nA valid BST is defined as follows:\n- The left subtree of a node contains only nodes with keys less than the node's key.\n- The right subtree of a node contains only nodes with keys greater than the node's key.\n- Both the left and right subtrees must also be binary search trees.",
        "Input: root = [2,1,3]\nOutput: true\n\nInput: root = [5,1,4,null,null,3,6]\nOutput: false",
        "The number of nodes in the tree is in the range [1, 10^4].\n-2^31 <= Node.val <= 2^31 - 1",
        "O(n)", "O(h)",
        "dfs,inorder,bounds"
    ),
    (
        "Serialize and Deserialize Binary Tree", "Both", "Trees", "Hard", 297,
        "Serialization is the process of converting a data structure or object into a sequence of bits so that it can be stored in a file or memory buffer.\nDesign an algorithm to serialize and deserialize a binary tree. There is no restriction on how your serialization/deserialization algorithm should work.",
        "Input: root = [1,2,3,null,null,4,5]\nOutput: [1,2,3,null,null,4,5]\n\nInput: root = []\nOutput: []",
        "The number of nodes in the tree is in the range [0, 10^4].\n-1000 <= Node.val <= 1000",
        "O(n)", "O(n)",
        "bfs,dfs,design"
    ),
    # ── Binary Search ──
    (
        "Binary Search", "NeetCode", "Binary Search", "Easy", 704,
        "Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums.\nIf target exists, then return its index. Otherwise, return -1.\nYou must write an algorithm with O(log n) runtime complexity.",
        "Input: nums = [-1,0,3,5,9,12], target = 9\nOutput: 4\n\nInput: nums = [-1,0,3,5,9,12], target = 2\nOutput: -1",
        "1 <= nums.length <= 10^4\n-10^4 < nums[i], target < 10^4\nAll the integers in nums are unique.\nnums is sorted in ascending order.",
        "O(log n)", "O(1)",
        "binary search,sorted"
    ),
    (
        "Koko Eating Bananas", "NeetCode", "Binary Search", "Medium", 875,
        "Koko loves to eat bananas. There are n piles of bananas, the ith pile has piles[i] bananas. The guards have gone and will come back in h hours.\nKoko can decide her bananas-per-hour eating speed of k. Each hour, she chooses some pile of bananas and eats k bananas from that pile.\nReturn the minimum integer k such that she can eat all the bananas within h hours.",
        "Input: piles = [3,6,7,11], h = 8\nOutput: 4\n\nInput: piles = [30,11,23,4,20], h = 5\nOutput: 30",
        "1 <= piles.length <= 10^4\npiles.length <= h <= 10^9\n1 <= piles[i] <= 10^9",
        "O(n log m) where m = max(piles)", "O(1)",
        "binary search on answer"
    ),
    # ── Sliding Window ──
    (
        "Longest Substring Without Repeating Characters", "Both", "Sliding Window", "Medium", 3,
        "Given a string s, find the length of the longest substring without repeating characters.",
        "Input: s = \"abcabcbb\"\nOutput: 3\nExplanation: The answer is \"abc\", with the length of 3.\n\nInput: s = \"bbbbb\"\nOutput: 1\n\nInput: s = \"pwwkew\"\nOutput: 3",
        "0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
        "O(n)", "O(min(m,n)) where m is charset size",
        "sliding window,hash set"
    ),
    (
        "Longest Repeating Character Replacement", "NeetCode", "Sliding Window", "Medium", 424,
        "You are given a string s and an integer k. You can choose any character of the string and change it to any other uppercase English character. You can perform this operation at most k times.\nReturn the length of the longest substring containing the same letter you can get after performing the above operations.",
        "Input: s = \"ABAB\", k = 2\nOutput: 4\n\nInput: s = \"AABABBA\", k = 1\nOutput: 4",
        "1 <= s.length <= 10^5\ns consists of only uppercase English letters.\n0 <= k <= s.length",
        "O(n)", "O(1) (26 letters)",
        "sliding window,frequency"
    ),
    (
        "Minimum Window Substring", "Both", "Sliding Window", "Hard", 76,
        "Given two strings s and t of lengths m and n respectively, return the minimum window substring of s such that every character in t (including duplicates) is included in the window. If there is no such substring, return the empty string \"\".",
        "Input: s = \"ADOBECODEBANC\", t = \"ABC\"\nOutput: \"BANC\"\n\nInput: s = \"a\", t = \"a\"\nOutput: \"a\"\n\nInput: s = \"a\", t = \"aa\"\nOutput: \"\"",
        "m == s.length\nn == t.length\n1 <= m, n <= 10^5\ns and t consist of uppercase and lowercase English letters.",
        "O(m + n)", "O(m + n)",
        "sliding window,two pointers,hash map"
    ),
    # ── Stack ──
    (
        "Valid Parentheses", "Both", "Stack", "Easy", 20,
        "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.",
        "Input: s = \"()\"\nOutput: true\n\nInput: s = \"()[]{}\"\nOutput: true\n\nInput: s = \"(]\"\nOutput: false",
        "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'.",
        "O(n)", "O(n)",
        "stack,matching"
    ),
    (
        "Min Stack", "NeetCode", "Stack", "Medium", 155,
        "Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.\nImplement the MinStack class with O(1) operations.",
        "Input: [\"MinStack\",\"push\",\"push\",\"push\",\"getMin\",\"pop\",\"top\",\"getMin\"]\n[[],[-2],[0],[-3],[],[],[],[]]\nOutput: [null,null,null,null,-3,null,0,-2]",
        "Methods: push(val), pop(), top(), getMin()\n-2^31 <= val <= 2^31 - 1\nMethods pop, top and getMin operations will always be called on non-empty stacks.",
        "O(1) all operations", "O(n)",
        "stack,design,auxiliary stack"
    ),
    (
        "Daily Temperatures", "Both", "Stack", "Medium", 739,
        "Given an array of integers temperatures represents the daily temperatures, return an array answer such that answer[i] is the number of days you have to wait after the ith day to get a warmer temperature. If there is no future day for which this is possible, keep answer[i] == 0 instead.",
        "Input: temperatures = [73,74,75,71,69,72,76,73]\nOutput: [1,1,4,2,1,1,0,0]\n\nInput: temperatures = [30,40,50,60]\nOutput: [1,1,1,0]",
        "1 <= temperatures.length <= 10^5\n30 <= temperatures[i] <= 100",
        "O(n)", "O(n)",
        "monotonic stack"
    ),
    # ── Dynamic Programming ──
    (
        "Climbing Stairs", "Both", "Dynamic Programming", "Easy", 70,
        "You are climbing a staircase. It takes n steps to reach the top.\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
        "Input: n = 2\nOutput: 2\nExplanation: (1 step + 1 step) or (2 steps)\n\nInput: n = 3\nOutput: 3\nExplanation: (1+1+1), (1+2), (2+1)",
        "1 <= n <= 45",
        "O(n)", "O(1)",
        "fibonacci,memoization,tabulation"
    ),
    (
        "House Robber", "Both", "Dynamic Programming", "Medium", 198,
        "You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed, the only constraint stopping you from robbing each of them is that adjacent houses have security systems connected.\nGiven an integer array nums representing the amount of money of each house, return the maximum amount of money you can rob tonight without alerting the police.",
        "Input: nums = [1,2,3,1]\nOutput: 4\nExplanation: Rob house 1 (money=1) then rob house 3 (money=3). Total = 4.\n\nInput: nums = [2,7,9,3,1]\nOutput: 12",
        "1 <= nums.length <= 100\n0 <= nums[i] <= 400",
        "O(n)", "O(1)",
        "dp,linear"
    ),
    (
        "Longest Common Subsequence", "Both", "Dynamic Programming", "Medium", 1143,
        "Given two strings text1 and text2, return the length of their longest common subsequence. If there is no common subsequence, return 0.\nA subsequence of a string is a new string generated from the original string with some characters (can be none) deleted without changing the relative order of the remaining characters.",
        "Input: text1 = \"abcde\", text2 = \"ace\"\nOutput: 3\nExplanation: LCS is \"ace\".\n\nInput: text1 = \"abc\", text2 = \"abc\"\nOutput: 3",
        "1 <= text1.length, text2.length <= 1000\ntext1 and text2 consist of only lowercase English characters.",
        "O(m × n)", "O(m × n)",
        "dp,2d,lcs,subsequence"
    ),
    (
        "0/1 Knapsack", "Striver", "Dynamic Programming", "Medium", 0,
        "Given weights and values of n items, put these items in a knapsack of capacity W to get the maximum total value in the knapsack.\nEach item can be included at most once (0/1 knapsack).",
        "Input: weights = [1,3,4,5], values = [1,4,5,7], W = 7\nOutput: 9\nExplanation: Pick items with weights 3 and 4 (values 4+5=9)\n\nInput: weights = [1,2,3], values = [6,10,12], W = 5\nOutput: 22",
        "1 <= n <= 1000\n1 <= W <= 1000\n0 <= weights[i] <= W\n0 <= values[i] <= 10^4",
        "O(n × W)", "O(n × W) or O(W) with optimization",
        "dp,2d,classic"
    ),
    (
        "Coin Change", "Both", "Dynamic Programming", "Medium", 322,
        "You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money.\nReturn the fewest number of coins that you need to make up that amount. If that amount of money cannot be made up by any combination of the coins, return -1.\nYou may assume that you have an infinite number of each kind of coin.",
        "Input: coins = [1,5,11], amount = 15\nOutput: 3\nExplanation: 5+5+5=15\n\nInput: coins = [2], amount = 3\nOutput: -1",
        "1 <= coins.length <= 12\n1 <= coins[i] <= 2^31 - 1\n0 <= amount <= 10^4",
        "O(amount × n)", "O(amount)",
        "dp,unbounded knapsack,bfs"
    ),
    (
        "Word Break", "Both", "Dynamic Programming", "Medium", 139,
        "Given a string s and a dictionary of strings wordDict, return true if s can be segmented into a space-separated sequence of one or more dictionary words.",
        "Input: s = \"leetcode\", wordDict = [\"leet\",\"code\"]\nOutput: true\n\nInput: s = \"applepenapple\", wordDict = [\"apple\",\"pen\"]\nOutput: true\n\nInput: s = \"catsandog\", wordDict = [\"cats\",\"dog\",\"sand\",\"and\",\"cat\"]\nOutput: false",
        "1 <= s.length <= 300\n1 <= wordDict.length <= 1000\n1 <= wordDict[i].length <= 20\ns and wordDict[i] consist of only lowercase English letters.",
        "O(n²)", "O(n)",
        "dp,trie,memoization"
    ),
    (
        "Longest Increasing Subsequence", "Both", "Dynamic Programming", "Medium", 300,
        "Given an integer array nums, return the length of the longest strictly increasing subsequence.",
        "Input: nums = [10,9,2,5,3,7,101,18]\nOutput: 4\nExplanation: [2,3,7,101]\n\nInput: nums = [0,1,0,3,2,3]\nOutput: 4",
        "1 <= nums.length <= 2500\n-10^4 <= nums[i] <= 10^4",
        "O(n log n) with patience sorting, O(n²) naive", "O(n)",
        "dp,patience sorting,binary search"
    ),
    # ── Graphs ──
    (
        "Number of Islands", "Both", "Graphs", "Medium", 200,
        "Given an m x n 2D binary grid grid which represents a map of '1's (land) and '0's (water), return the number of islands.\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.",
        "Input: grid = [[\"1\",\"1\",\"1\",\"1\",\"0\"],[\"1\",\"1\",\"0\",\"1\",\"0\"],[\"1\",\"1\",\"0\",\"0\",\"0\"],[\"0\",\"0\",\"0\",\"0\",\"0\"]]\nOutput: 1\n\nInput: grid = [[\"1\",\"1\",\"0\",\"0\",\"0\"],[\"1\",\"1\",\"0\",\"0\",\"0\"],[\"0\",\"0\",\"1\",\"0\",\"0\"],[\"0\",\"0\",\"0\",\"1\",\"1\"]]\nOutput: 3",
        "m == grid.length\nn == grid[i].length\n1 <= m, n <= 300\ngrid[i][j] is '0' or '1'.",
        "O(m × n)", "O(m × n)",
        "dfs,bfs,union find"
    ),
    (
        "Clone Graph", "NeetCode", "Graphs", "Medium", 133,
        "Given a reference of a node in a connected undirected graph, return a deep copy (clone) of the graph.\nEach node in the graph contains a value (int) and a list (List[Node]) of its neighbors.",
        "Input: adjList = [[2,4],[1,3],[2,4],[1,3]]\nOutput: [[2,4],[1,3],[2,4],[1,3]]\n\nInput: adjList = [[]]\nOutput: [[]]",
        "The number of nodes in the graph is in the range [0, 100].\n1 <= Node.val <= 100\nNode.val is unique for each node.",
        "O(V + E)", "O(V)",
        "dfs,bfs,hash map"
    ),
    (
        "Course Schedule", "Both", "Graphs", "Medium", 207,
        "There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1.\nYou are given an array prerequisites where prerequisites[i] = [ai, bi] indicates that you must take course bi first if you want to take course ai.\nReturn true if you can finish all courses. Otherwise, return false.",
        "Input: numCourses = 2, prerequisites = [[1,0]]\nOutput: true\n\nInput: numCourses = 2, prerequisites = [[1,0],[0,1]]\nOutput: false",
        "1 <= numCourses <= 2000\n0 <= prerequisites.length <= 5000\nprerequisites[i].length == 2\n0 <= ai, bi < numCourses",
        "O(V + E)", "O(V + E)",
        "topological sort,cycle detection,dfs"
    ),
    (
        "Rotting Oranges", "NeetCode", "Graphs", "Medium", 994,
        "You are given an m x n integer grid where each cell can have one of three values:\n0: empty cell\n1: fresh orange\n2: rotten orange\nReturn the minimum number of minutes that must elapse until no cell has a fresh orange. If this is impossible, return -1.",
        "Input: grid = [[2,1,1],[1,1,0],[0,1,1]]\nOutput: 4\n\nInput: grid = [[2,1,1],[0,1,1],[1,0,1]]\nOutput: -1",
        "m == grid.length\nn == grid[i].length\n1 <= m, n <= 10\ngrid[i][j] is 0, 1, or 2.",
        "O(m × n)", "O(m × n)",
        "bfs,multi-source bfs"
    ),
    (
        "Pacific Atlantic Water Flow", "NeetCode", "Graphs", "Medium", 417,
        "There is an m x n rectangular island that borders both the Pacific Ocean and Atlantic Ocean.\nReturn a 2D list of grid coordinates where rain water can flow to both the Pacific and Atlantic oceans.",
        "Input: heights = [[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]\nOutput: [[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]",
        "m == heights.length\nn == heights[i].length\n1 <= m, n <= 200\n0 <= heights[i][j] <= 10^5",
        "O(m × n)", "O(m × n)",
        "dfs,bfs,reverse flow"
    ),
    # ── Two Pointers ──
    (
        "Valid Palindrome", "NeetCode", "Two Pointers", "Easy", 125,
        "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.\nGiven a string s, return true if it is a palindrome, or false otherwise.",
        "Input: s = \"A man, a plan, a canal: Panama\"\nOutput: true\n\nInput: s = \"race a car\"\nOutput: false",
        "1 <= s.length <= 2 * 10^5\ns consists only of printable ASCII characters.",
        "O(n)", "O(1)",
        "two pointers,string"
    ),
    (
        "Trapping Rain Water", "Both", "Two Pointers", "Hard", 42,
        "Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
        "Input: height = [0,1,0,2,1,0,1,3,2,1,2,1]\nOutput: 6\n\nInput: height = [4,2,0,3,2,5]\nOutput: 9",
        "n == height.length\n1 <= n <= 2 * 10^4\n0 <= height[i] <= 10^5",
        "O(n)", "O(1)",
        "two pointers,prefix max,suffix max"
    ),
    # ── Hashing ──
    (
        "Group Anagrams", "Both", "Hashing", "Medium", 49,
        "Given an array of strings strs, group the anagrams together. You can return the answer in any order.\nAn Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.",
        "Input: strs = [\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"]\nOutput: [[\"bat\"],[\"nat\",\"tan\"],[\"ate\",\"eat\",\"tea\"]]\n\nInput: strs = [\"\"]\nOutput: [[\"\"]]",
        "1 <= strs.length <= 10^4\n0 <= strs[i].length <= 100\nstrs[i] consists of lowercase English letters.",
        "O(n × k log k) where k = max string length", "O(n × k)",
        "sorting,character count,hash map"
    ),
    (
        "Top K Frequent Elements", "Both", "Hashing", "Medium", 347,
        "Given an integer array nums and an integer k, return the k most frequent elements. You may return the answer in any order.\nYou must write a solution where the time complexity is better than O(n log n).",
        "Input: nums = [1,1,1,2,2,3], k = 2\nOutput: [1,2]\n\nInput: nums = [1], k = 1\nOutput: [1]",
        "1 <= nums.length <= 10^5\nk is in the range [1, the number of unique elements in the array].",
        "O(n)", "O(n)",
        "bucket sort,heap,hash map"
    ),
    # ── Heap / Priority Queue ──
    (
        "Find Median from Data Stream", "Both", "Heap", "Hard", 295,
        "The median is the middle value in an ordered integer list. If the size of the list is even, there is no middle value, and the median is the mean of the two middle values.\nDesign and implement the MedianFinder class with addNum and findMedian methods.",
        "Input: [\"MedianFinder\",\"addNum\",\"addNum\",\"findMedian\",\"addNum\",\"findMedian\"]\n[[],[1],[2],[],[3],[]]\nOutput: [null,null,null,1.5,null,2.0]",
        "addNum: -10^5 <= num <= 10^5\nThere will be at least one element in the data structure before calling findMedian.\nAt most 5 * 10^4 calls will be made to addNum and findMedian.",
        "O(log n) addNum, O(1) findMedian", "O(n)",
        "two heaps,max heap,min heap,design"
    ),
    (
        "K Closest Points to Origin", "NeetCode", "Heap", "Medium", 973,
        "Given an array of points where points[i] = [xi, yi] represents a point on the X-Y plane and an integer k, return the k closest points to the origin (0, 0).\nThe distance between two points on the X-Y plane is the Euclidean distance.",
        "Input: points = [[1,3],[-2,2]], k = 1\nOutput: [[-2,2]]\n\nInput: points = [[3,3],[5,-1],[-2,4]], k = 2\nOutput: [[3,3],[-2,4]]",
        "1 <= k <= points.length <= 10^4\n-10^4 <= xi, yi <= 10^4",
        "O(n log k)", "O(k)",
        "heap,quickselect,sorting"
    ),
    # ── Backtracking ──
    (
        "Subsets", "Both", "Backtracking", "Medium", 78,
        "Given an integer array nums of unique elements, return all possible subsets (the power set).\nThe solution set must not contain duplicate subsets. Return the solution in any order.",
        "Input: nums = [1,2,3]\nOutput: [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]\n\nInput: nums = [0]\nOutput: [[],[0]]",
        "1 <= nums.length <= 10\n-10 <= nums[i] <= 10\nAll the numbers of nums are unique.",
        "O(n × 2^n)", "O(n × 2^n)",
        "backtracking,bit manipulation,dfs"
    ),
    (
        "Permutations", "Both", "Backtracking", "Medium", 46,
        "Given an array nums of distinct integers, return all the possible permutations. You can return the answer in any order.",
        "Input: nums = [1,2,3]\nOutput: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]\n\nInput: nums = [0,1]\nOutput: [[0,1],[1,0]]",
        "1 <= nums.length <= 6\n-10 <= nums[i] <= 10\nAll the integers of nums are unique.",
        "O(n!)", "O(n!)",
        "backtracking,dfs"
    ),
    (
        "Combination Sum", "Both", "Backtracking", "Medium", 39,
        "Given an array of distinct integers candidates and a target integer target, return a list of all unique combinations of candidates where the chosen numbers sum to target.\nYou may return the combinations in any order. The same number may be chosen from candidates an unlimited number of times.",
        "Input: candidates = [2,3,6,7], target = 7\nOutput: [[2,2,3],[7]]\n\nInput: candidates = [2,3], target = 6\nOutput: [[2,2,2],[3,3]]",
        "1 <= candidates.length <= 30\n2 <= candidates[i] <= 40\nAll elements of candidates are distinct.\n1 <= target <= 500",
        "O(2^t) where t = target/min_candidate", "O(target/min_candidate)",
        "backtracking,dfs"
    ),
    (
        "N-Queens", "Striver", "Backtracking", "Hard", 51,
        "The n-queens puzzle is the problem of placing n queens on an n x n chessboard such that no two queens attack each other.\nGiven an integer n, return all distinct solutions to the n-queens puzzle.",
        "Input: n = 4\nOutput: [[\".Q..\",\"...Q\",\"Q...\",\"..Q.\"],  [\"..Q.\",\"Q...\",\"...Q\",\".Q..\"]]\n\nInput: n = 1\nOutput: [[\"Q\"]]",
        "1 <= n <= 9",
        "O(n!)", "O(n²)",
        "backtracking,constraint satisfaction"
    ),
    # ── Sorting ──
    (
        "Sort Colors", "Striver", "Sorting", "Medium", 75,
        "Given an array nums with n objects colored red, white, or blue, sort them in-place so that objects of the same color are adjacent, with the colors in the order red, white, and blue.\nWe will use the integers 0, 1, and 2 to represent the color red, white, and blue, respectively.\nYou must solve this problem without using the library's sort function.",
        "Input: nums = [2,0,2,1,1,0]\nOutput: [0,0,1,1,2,2]\n\nInput: nums = [2,0,1]\nOutput: [0,1,2]",
        "n == nums.length\n1 <= n <= 300\nnums[i] is either 0, 1, or 2.",
        "O(n)", "O(1)",
        "dutch national flag,three pointers"
    ),
    (
        "Merge Intervals", "Both", "Sorting", "Medium", 56,
        "Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
        "Input: intervals = [[1,3],[2,6],[8,10],[15,18]]\nOutput: [[1,6],[8,10],[15,18]]\n\nInput: intervals = [[1,4],[4,5]]\nOutput: [[1,5]]",
        "1 <= intervals.length <= 10^4\nintervals[i].length == 2\n0 <= starti <= endi <= 10^4",
        "O(n log n)", "O(n)",
        "sorting,interval"
    ),
    # ── Math / Number Theory ──
    (
        "Reverse Integer", "Striver", "Math", "Medium", 7,
        "Given a signed 32-bit integer x, return x with its digits reversed. If reversing x causes the value to go outside the signed 32-bit integer range [-2^31, 2^31 - 1], then return 0.",
        "Input: x = 123\nOutput: 321\n\nInput: x = -123\nOutput: -321\n\nInput: x = 120\nOutput: 21",
        "-2^31 <= x <= 2^31 - 1",
        "O(log x)", "O(1)",
        "overflow check,modulo"
    ),
    (
        "Power Function (Pow(x, n))", "Striver", "Math", "Medium", 50,
        "Implement pow(x, n), which calculates x raised to the power n (i.e., x^n).",
        "Input: x = 2.00000, n = 10\nOutput: 1024.00000\n\nInput: x = 2.10000, n = 3\nOutput: 9.26100\n\nInput: x = 2.00000, n = -2\nOutput: 0.25000",
        "-100.0 < x < 100.0\n-2^31 <= n <= 2^31-1\nn is an integer.\n-10^4 <= x^n <= 10^4",
        "O(log n)", "O(log n) recursive / O(1) iterative",
        "binary exponentiation,fast power"
    ),
    # ── Bit Manipulation ──
    (
        "Number of 1 Bits", "NeetCode", "Bit Manipulation", "Easy", 191,
        "Write a function that takes the binary representation of an unsigned integer and returns the number of '1' bits it has (also known as the Hamming weight).",
        "Input: n = 00000000000000000000000000001011\nOutput: 3\n\nInput: n = 00000000000000000000000010000000\nOutput: 1",
        "The input must be a binary string of length 32.",
        "O(1) (32 bits max)", "O(1)",
        "bit manipulation,popcount"
    ),
    (
        "Counting Bits", "NeetCode", "Bit Manipulation", "Easy", 338,
        "Given an integer n, return an array ans of length n + 1 such that for each i (0 <= i <= n), ans[i] is the number of 1's in the binary representation of i.",
        "Input: n = 2\nOutput: [0,1,1]\n\nInput: n = 5\nOutput: [0,1,1,2,1,2]",
        "0 <= n <= 10^5",
        "O(n)", "O(n)",
        "dp,bit manipulation"
    ),
    (
        "Sum of Two Integers", "NeetCode", "Bit Manipulation", "Medium", 371,
        "Given two integers a and b, return the sum of the two integers without using the operators + and -.",
        "Input: a = 1, b = 2\nOutput: 3\n\nInput: a = 2, b = 3\nOutput: 5",
        "-1000 <= a, b <= 1000",
        "O(1)", "O(1)",
        "bit manipulation,XOR,carry"
    ),
    # ── Batch 1: Strings and Hashing ──
    ("Valid Anagram", "Both", "Strings", "Easy", 242, "Decide whether t can be made by rearranging every character of s exactly once.", "Input: s=anagram, t=nagaram\nOutput: true\n\nInput: s=rat, t=car\nOutput: false", "1 <= len(s), len(t) <= 5*10^4; lowercase letters.", "O(n)", "O(1)", "frequency,counting"),
    ("Longest Palindromic Substring", "Both", "Strings", "Medium", 5, "Return the longest contiguous part of s that reads identically in either direction.", "Input: s=babad\nOutput: bab\n\nInput: s=cbbd\nOutput: bb", "1 <= len(s) <= 1000; s contains letters and digits.", "O(n^2)", "O(1)", "expand-around-center"),
    ("Palindromic Substrings", "Both", "Strings", "Medium", 647, "Count every contiguous substring of s that is a palindrome.", "Input: s=abc\nOutput: 3\n\nInput: s=aaa\nOutput: 6", "1 <= len(s) <= 1000; lowercase letters.", "O(n^2)", "O(1)", "palindrome,center"),
    ("Encode and Decode Strings", "NeetCode", "Strings", "Medium", 271, "Design reversible encoding for a list of arbitrary strings so boundaries are preserved.", "Input: [lint,code]\nOutput: decode(encode(...)) = [lint,code]\n\nInput: []\nOutput: []", "0 <= number of strings <= 200; strings may contain delimiter characters.", "O(total characters)", "O(total characters)", "design,length-prefix"),
    ("Longest Common Prefix", "Both", "Strings", "Easy", 14, "Find the longest opening sequence shared by every string in an array.", "Input: [flower,flow,flight]\nOutput: fl\n\nInput: [dog,racecar,car]\nOutput: ''", "1 <= number of strings <= 200; each length <= 200.", "O(total characters)", "O(1)", "strings,scanning"),
    ("String to Integer (atoi)", "Striver", "Strings", "Medium", 8, "Parse a signed decimal prefix from a string, discarding whitespace and clamping 32-bit overflow.", "Input: s='   -42'\nOutput: -42\n\nInput: s='4193 with words'\nOutput: 4193", "0 <= len(s) <= 200; printable ASCII.", "O(n)", "O(1)", "parsing,overflow"),
    ("Valid Sudoku", "Both", "Hashing", "Medium", 36, "Check that filled cells in a 9 by 9 board do not repeat a digit in any row, column, or 3 by 3 box.", "Input: valid partially filled board\nOutput: true\n\nInput: board with duplicate 8 in a row\nOutput: false", "board is 9x9; cells are '.' or digits 1 through 9.", "O(1)", "O(1)", "hash-set,matrix"),
    ("Longest Consecutive Sequence", "Both", "Hashing", "Medium", 128, "Find the largest count of consecutive integer values present in an unsorted array.", "Input: [100,4,200,1,3,2]\nOutput: 4\n\nInput: [0,3,7,2,5,8,4,6,0,1]\nOutput: 9", "0 <= n <= 10^5; values fit signed 32-bit integers.", "O(n)", "O(n)", "hash-set,sequence"),
    ("Encode and Decode TinyURL", "NeetCode", "Design", "Medium", 535, "Build a service that maps long URLs to compact keys and restores each original URL.", "Input: encode('https://a.example/x')\nOutput: a short URL\n\nInput: decode(short URL)\nOutput: 'https://a.example/x'", "URLs are nonempty strings up to 10^4 characters.", "O(1) average", "O(n)", "hash-map,design"),
    ("Subarray Sum Equals K", "Both", "Hashing", "Medium", 560, "Count contiguous subarrays whose elements add to k.", "Input: nums=[1,1,1], k=2\nOutput: 2\n\nInput: nums=[1,2,3], k=3\nOutput: 2", "1 <= n <= 2*10^4; -1000 <= nums[i] <= 1000.", "O(n)", "O(n)", "prefix-sum,hash-map"),
    ("Isomorphic Strings", "NeetCode", "Strings", "Easy", 205, "Determine whether a one-to-one character replacement transforms s into t.", "Input: s=egg, t=add\nOutput: true\n\nInput: s=foo, t=bar\nOutput: false", "1 <= len(s) == len(t) <= 5*10^4.", "O(n)", "O(1)", "hash-map,bijective"),
    ("Ransom Note", "NeetCode", "Hashing", "Easy", 383, "Determine if the letters for ransomNote can be taken from magazine, each at most once.", "Input: ransomNote=a, magazine=b\nOutput: false\n\nInput: ransomNote=aa, magazine=aab\nOutput: true", "Lengths are at most 10^5; lowercase letters.", "O(n+m)", "O(1)", "counting,frequency"),
    ("First Unique Character in a String", "Striver", "Strings", "Easy", 387, "Return the index of the first character that occurs exactly once, or -1.", "Input: s=leetcode\nOutput: 0\n\nInput: s=aabb\nOutput: -1", "1 <= len(s) <= 10^5; lowercase letters.", "O(n)", "O(1)", "frequency,strings"),
    ("Find All Anagrams in a String", "NeetCode", "Strings", "Medium", 438, "Return all start positions where a permutation of p occurs as a substring of s.", "Input: s=cbaebabacd, p=abc\nOutput: [0,6]\n\nInput: s=abab, p=ab\nOutput: [0,1,2]", "1 <= len(p) <= len(s) <= 3*10^4; lowercase letters.", "O(n)", "O(1)", "sliding-window,frequency"),
    ("Word Pattern", "Striver", "Hashing", "Easy", 290, "Check whether words in a sentence match a pattern using a one-to-one correspondence.", "Input: pattern=abba, s='dog cat cat dog'\nOutput: true\n\nInput: pattern=abba, s='dog cat cat fish'\nOutput: false", "Pattern and sentence length are at most 3000.", "O(n)", "O(n)", "hash-map,bijection"),
    # ── Batch 2: Arrays and Two Pointers ──
    ("Set Matrix Zeroes", "Both", "Matrix", "Medium", 73, "If a matrix cell is zero, set its full row and column to zero in place.", "Input: [[1,1,1],[1,0,1],[1,1,1]]\nOutput: [[1,0,1],[0,0,0],[1,0,1]]\n\nInput: [[0,1],[1,1]]\nOutput: [[0,0],[0,1]]", "1 <= rows, cols <= 200; values fit signed 32-bit integers.", "O(mn)", "O(1)", "matrix,in-place"),
    ("Spiral Matrix", "Both", "Matrix", "Medium", 54, "Visit every matrix value by repeatedly traversing its remaining outer boundary clockwise.", "Input: [[1,2,3],[4,5,6],[7,8,9]]\nOutput: [1,2,3,6,9,8,7,4,5]\n\nInput: [[1,2,3,4]]\nOutput: [1,2,3,4]", "1 <= rows, cols <= 10; values fit signed 32-bit integers.", "O(mn)", "O(1)", "matrix,simulation"),
    ("Rotate Image", "Both", "Matrix", "Medium", 48, "Rotate an n by n image matrix clockwise by 90 degrees without allocating another matrix.", "Input: [[1,2],[3,4]]\nOutput: [[3,1],[4,2]]\n\nInput: [[1,2,3],[4,5,6],[7,8,9]]\nOutput: [[7,4,1],[8,5,2],[9,6,3]]", "1 <= n <= 20; matrix is square.", "O(n^2)", "O(1)", "matrix,transpose"),
    ("Next Permutation", "Both", "Arrays", "Medium", 31, "Rearrange numbers into the next lexicographic ordering, wrapping to the smallest if needed.", "Input: [1,2,3]\nOutput: [1,3,2]\n\nInput: [3,2,1]\nOutput: [1,2,3]", "1 <= n <= 100; values are nonnegative integers.", "O(n)", "O(1)", "permutation,reverse"),
    ("Pascal's Triangle", "Both", "Arrays", "Easy", 118, "Build the first numRows rows where each inner value equals the sum of the two values above it.", "Input: numRows=5\nOutput: [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]\n\nInput: numRows=1\nOutput: [[1]]", "1 <= numRows <= 30.", "O(n^2)", "O(n^2)", "dp,combinatorics"),
    ("Majority Element", "Both", "Arrays", "Easy", 169, "Return the value that occurs more than half the time in nums.", "Input: [3,2,3]\nOutput: 3\n\nInput: [2,2,1,1,1,2,2]\nOutput: 2", "1 <= n <= 5*10^4; a majority value always exists.", "O(n)", "O(1)", "boyer-moore,voting"),
    ("4Sum", "Both", "Two Pointers", "Medium", 18, "Return unique groups of four distinct indices whose values sum to target.", "Input: [1,0,-1,0,-2,2], target=0\nOutput: [[-2,-1,1,2],[-2,0,0,2],[-1,0,0,1]]\n\nInput: [2,2,2,2,2], target=8\nOutput: [[2,2,2,2]]", "1 <= n <= 200; values and target fit signed 32-bit integers.", "O(n^3)", "O(n)", "sorting,two-pointers"),
    ("Longest Subarray With Sum K", "Striver", "Hashing", "Medium", 0, "Find the largest length of a contiguous array segment whose sum equals k.", "Input: [1,2,3,1,1,1,1], k=6\nOutput: 4\n\nInput: [1,-1,5,-2,3], k=3\nOutput: 4", "1 <= n <= 10^5; values fit signed 32-bit integers.", "O(n)", "O(n)", "prefix-sum,hash-map"),
    ("Two Sum II - Input Array Is Sorted", "Both", "Two Pointers", "Medium", 167, "In a sorted array, return one-based positions of two values that add to target.", "Input: [2,7,11,15], target=9\nOutput: [1,2]\n\nInput: [2,3,4], target=6\nOutput: [1,3]", "2 <= n <= 3*10^4; exactly one answer exists.", "O(n)", "O(1)", "two-pointers,sorted"),
    ("3Sum Closest", "Striver", "Two Pointers", "Medium", 16, "Find three values whose sum has the smallest absolute difference from target.", "Input: [-1,2,1,-4], target=1\nOutput: 2\n\nInput: [0,0,0], target=1\nOutput: 0", "3 <= n <= 500; values fit signed 32-bit integers.", "O(n^2)", "O(1)", "sorting,two-pointers"),
    ("Remove Duplicates from Sorted Array", "Both", "Two Pointers", "Easy", 26, "Compact a sorted array in place so each distinct value appears once and return the new length.", "Input: [1,1,2]\nOutput: 2, [1,2]\n\nInput: [0,0,1,1,2]\nOutput: 3, [0,1,2]", "1 <= n <= 3*10^4; nums is sorted.", "O(n)", "O(1)", "two-pointers,in-place"),
    ("Move Zeroes", "Both", "Two Pointers", "Easy", 283, "Move all zero values to the end while retaining the order of nonzero values.", "Input: [0,1,0,3,12]\nOutput: [1,3,12,0,0]\n\nInput: [0]\nOutput: [0]", "1 <= n <= 10^4; values fit signed 32-bit integers.", "O(n)", "O(1)", "two-pointers,swap"),
    ("Squares of a Sorted Array", "NeetCode", "Two Pointers", "Easy", 977, "Return the squares of a nondecreasing array, also sorted nondecreasingly.", "Input: [-4,-1,0,3,10]\nOutput: [0,1,9,16,100]\n\nInput: [-7,-3,2,3,11]\nOutput: [4,9,9,49,121]", "1 <= n <= 10^4; nums is sorted.", "O(n)", "O(n)", "two-pointers,square"),
    ("Sort Array By Parity", "Striver", "Two Pointers", "Easy", 905, "Rearrange an array so every even value appears before every odd value.", "Input: [3,1,2,4]\nOutput: [4,2,1,3]\n\nInput: [0]\nOutput: [0]", "1 <= n <= 5000; values are nonnegative.", "O(n)", "O(1)", "partition,two-pointers"),
    ("Find the Difference of Two Arrays", "NeetCode", "Hashing", "Easy", 2215, "List values unique to each of two integer arrays.", "Input: [1,2,3], [2,4,6]\nOutput: [[1,3],[4,6]]\n\nInput: [1,2,3,3], [1,1,2,2]\nOutput: [[3],[]]", "1 <= lengths <= 1000; values range from -1000 to 1000.", "O(n+m)", "O(n+m)", "sets,arrays"),
    # ── Batch 3: Binary Search, Sorting, and Intervals ──
    ("Median of Two Sorted Arrays", "Both", "Binary Search", "Hard", 4, "Find the median of two sorted arrays without merging them fully.", "Input: [1,3], [2]\nOutput: 2.0\n\nInput: [1,2], [3,4]\nOutput: 2.5", "0 <= m,n <= 1000; 1 <= m+n <= 2000.", "O(log(min(m,n)))", "O(1)", "binary-search,partition"),
    ("Search a 2D Matrix", "Both", "Binary Search", "Medium", 74, "Search a matrix whose rows and flattened values are sorted for target.", "Input: [[1,3,5],[7,9,11]], target=9\nOutput: true\n\nInput: [[1,3]], target=2\nOutput: false", "1 <= rows,cols <= 100; rows are globally ordered.", "O(log(mn))", "O(1)", "binary-search,matrix"),
    ("Find Peak Element", "NeetCode", "Binary Search", "Medium", 162, "Return any index whose value is greater than its immediate neighbors.", "Input: [1,2,3,1]\nOutput: 2\n\nInput: [1,2,1,3,5,6,4]\nOutput: 1 or 5", "1 <= n <= 1000; adjacent values differ.", "O(log n)", "O(1)", "binary-search,peak"),
    ("Time Based Key-Value Store", "NeetCode", "Binary Search", "Medium", 981, "Store timestamped values by key and retrieve the latest value at or before a query time.", "Input: set(foo,bar,1), get(foo,1)\nOutput: bar\n\nInput: get(foo,3) after set(foo,bar2,4)\nOutput: bar", "At most 2*10^5 calls; timestamps for one key increase.", "O(log n) get", "O(n)", "binary-search,design"),
    ("Search in Rotated Sorted Array II", "NeetCode", "Binary Search", "Medium", 81, "Determine whether target occurs in a rotated sorted array that may contain duplicates.", "Input: [2,5,6,0,0,1,2], target=0\nOutput: true\n\nInput: [2,5,6,0,0,1,2], target=3\nOutput: false", "1 <= n <= 5000; values fit signed 32-bit integers.", "O(n) worst case", "O(1)", "binary-search,rotation"),
    ("Insert Interval", "Both", "Intervals", "Medium", 57, "Insert one interval into sorted disjoint intervals and merge any overlap.", "Input: [[1,3],[6,9]], new=[2,5]\nOutput: [[1,5],[6,9]]\n\nInput: [[1,2],[3,5]], new=[6,7]\nOutput: [[1,2],[3,5],[6,7]]", "0 <= n <= 10^4; intervals are sorted and nonoverlapping.", "O(n)", "O(n)", "intervals,merge"),
    ("Non-overlapping Intervals", "Both", "Intervals", "Medium", 435, "Remove the fewest intervals needed so the remaining intervals do not overlap.", "Input: [[1,2],[2,3],[3,4],[1,3]]\nOutput: 1\n\nInput: [[1,2],[1,2],[1,2]]\nOutput: 2", "1 <= n <= 10^5; endpoints fit signed 32-bit integers.", "O(n log n)", "O(1)", "greedy,intervals"),
    ("Meeting Rooms", "NeetCode", "Intervals", "Easy", 252, "Determine whether a person can attend every meeting interval without overlap.", "Input: [[0,30],[5,10],[15,20]]\nOutput: false\n\nInput: [[7,10],[2,4]]\nOutput: true", "0 <= n <= 10^4; start < end.", "O(n log n)", "O(1)", "sorting,intervals"),
    ("Meeting Rooms II", "NeetCode", "Intervals", "Medium", 253, "Return the smallest number of rooms needed to host all meetings.", "Input: [[0,30],[5,10],[15,20]]\nOutput: 2\n\nInput: [[7,10],[2,4]]\nOutput: 1", "1 <= n <= 10^4; start < end.", "O(n log n)", "O(n)", "heap,intervals"),
    ("Minimum Number of Arrows to Burst Balloons", "Both", "Intervals", "Medium", 452, "Find the fewest vertical arrows that intersect every balloon interval.", "Input: [[10,16],[2,8],[1,6],[7,12]]\nOutput: 2\n\nInput: [[1,2],[3,4]]\nOutput: 2", "1 <= n <= 10^5; endpoints fit signed 32-bit integers.", "O(n log n)", "O(1)", "greedy,intervals"),
    ("Find First and Last Position of Element", "Both", "Binary Search", "Medium", 34, "Return the first and last indices of target in a sorted array, or [-1,-1].", "Input: [5,7,7,8,8,10], target=8\nOutput: [3,4]\n\nInput: [5,7], target=6\nOutput: [-1,-1]", "0 <= n <= 10^5; nums is nondecreasing.", "O(log n)", "O(1)", "binary-search,bounds"),
    ("Find Minimum in Rotated Sorted Array II", "Striver", "Binary Search", "Hard", 154, "Return the minimum in a rotated sorted array whose values may repeat.", "Input: [1,3,5]\nOutput: 1\n\nInput: [2,2,2,0,1]\nOutput: 0", "1 <= n <= 5000; values fit signed 32-bit integers.", "O(n) worst case", "O(1)", "binary-search,duplicates"),
    ("Merge Sorted Array", "Both", "Sorting", "Easy", 88, "Merge nums2 into nums1 in sorted order using nums1's trailing space.", "Input: [1,2,3,0,0,0], m=3; [2,5,6], n=3\nOutput: [1,2,2,3,5,6]\n\nInput: [1],m=1; [],n=0\nOutput: [1]", "0 <= m,n <= 200; arrays are sorted.", "O(m+n)", "O(1)", "two-pointers,merge"),
    ("Sort an Array", "NeetCode", "Sorting", "Medium", 912, "Sort an integer array without using library sorting as the core algorithm.", "Input: [5,2,3,1]\nOutput: [1,2,3,5]\n\nInput: [5,1,1,2,0,0]\nOutput: [0,0,1,1,2,5]", "1 <= n <= 5*10^4; values fit signed 32-bit integers.", "O(n log n)", "O(n)", "merge-sort,sorting"),
    ("Kth Largest Element in an Array", "Both", "Heap", "Medium", 215, "Return the kth greatest value by sorted order, counting duplicates separately.", "Input: [3,2,1,5,6,4], k=2\nOutput: 5\n\nInput: [3,2,3,1,2,4,5,5,6], k=4\nOutput: 4", "1 <= k <= n <= 10^5.", "O(n log k)", "O(k)", "heap,quickselect"),
    # ── Batch 4: Linked Lists and Stacks ──
    ("Reorder List", "Both", "Linked List", "Medium", 143, "Rearrange a list from first-to-last order into first, last, second, second-last order.", "Input: [1,2,3,4]\nOutput: [1,4,2,3]\n\nInput: [1,2,3,4,5]\nOutput: [1,5,2,4,3]", "1 <= nodes <= 5*10^4; values fit signed 32-bit integers.", "O(n)", "O(1)", "linked-list,reverse"),
    ("Copy List with Random Pointer", "Both", "Linked List", "Medium", 138, "Deep-copy a list where every node also points to an arbitrary node or null.", "Input: [[7,null],[13,0]]\nOutput: equivalent deep copy\n\nInput: [[1,1],[2,1]]\nOutput: equivalent deep copy", "0 <= nodes <= 1000; random is null or a list node.", "O(n)", "O(1)", "linked-list,copy"),
    ("Add Two Numbers", "Both", "Linked List", "Medium", 2, "Add two reversed digit lists and return the sum as a reversed digit list.", "Input: [2,4,3], [5,6,4]\nOutput: [7,0,8]\n\nInput: [0], [0]\nOutput: [0]", "1 <= list lengths <= 100; digits 0 through 9.", "O(max(m,n))", "O(1) excluding output", "linked-list,carry"),
    ("Find the Duplicate Number", "Both", "Linked List", "Medium", 287, "Find the repeated value in n+1 values from 1 through n without modifying the array.", "Input: [1,3,4,2,2]\nOutput: 2\n\nInput: [3,1,3,4,2]\nOutput: 3", "2 <= n+1 <= 10^5; exactly one value repeats.", "O(n)", "O(1)", "floyd-cycle,arrays"),
    ("LRU Cache", "Both", "Design", "Medium", 146, "Implement a bounded cache that discards the least recently used key when full.", "Input: put(1,1), put(2,2), get(1)\nOutput: 1\n\nInput: put(3,3) after capacity 2, get(2)\nOutput: -1", "1 <= capacity <= 3000; at most 2*10^5 operations.", "O(1) average", "O(capacity)", "hash-map,doubly-linked-list"),
    ("Rotate List", "Striver", "Linked List", "Medium", 61, "Rotate a linked list right by k positions.", "Input: [1,2,3,4,5], k=2\nOutput: [4,5,1,2,3]\n\nInput: [0,1,2], k=4\nOutput: [2,0,1]", "0 <= nodes <= 500; 0 <= k <= 2*10^9.", "O(n)", "O(1)", "linked-list,cycle"),
    ("Flatten a Multilevel Doubly Linked List", "NeetCode", "Linked List", "Medium", 430, "Flatten child doubly linked lists into one depth-first doubly linked sequence.", "Input: 1-2-3 with child 7-8 at 3\nOutput: 1-2-3-7-8\n\nInput: empty list\nOutput: empty list", "1 <= nodes <= 1000; child links may nest.", "O(n)", "O(n)", "linked-list,dfs"),
    ("Evaluate Reverse Polish Notation", "Both", "Stack", "Medium", 150, "Evaluate an arithmetic expression whose operators follow their operands.", "Input: [2,1,+,3,*]\nOutput: 9\n\nInput: [4,13,5,/,+]\nOutput: 6", "1 <= tokens <= 10^4; operators are +,-,*,/.", "O(n)", "O(n)", "stack,parsing"),
    ("Largest Rectangle in Histogram", "Both", "Stack", "Hard", 84, "Find the maximum rectangular area supported by adjacent histogram bars.", "Input: [2,1,5,6,2,3]\nOutput: 10\n\nInput: [2,4]\nOutput: 4", "1 <= n <= 10^5; heights are nonnegative.", "O(n)", "O(n)", "monotonic-stack"),
    ("Generate Parentheses", "Both", "Backtracking", "Medium", 22, "Generate every well-formed string containing n pairs of parentheses.", "Input: n=3\nOutput: five valid strings\n\nInput: n=1\nOutput: [()]", "1 <= n <= 8.", "O(Cn*n)", "O(n)", "backtracking,parentheses"),
    ("Car Fleet", "NeetCode", "Stack", "Medium", 853, "Count groups of cars that reach a target together without passing each other.", "Input: target=12, pos=[10,8,0,5,3], speed=[2,4,1,1,3]\nOutput: 3\n\nInput: target=10, pos=[3], speed=[3]\nOutput: 1", "1 <= n <= 10^5; positions are unique.", "O(n log n)", "O(n)", "sorting,stack"),
    ("Simplify Path", "NeetCode", "Stack", "Medium", 71, "Normalize an absolute Unix path by handling dots and parent-directory components.", "Input: /home/\nOutput: /home\n\nInput: /../\nOutput: /", "1 <= len(path) <= 3000; path starts with '/'.", "O(n)", "O(n)", "stack,strings"),
    ("Basic Calculator II", "Striver", "Stack", "Medium", 227, "Evaluate an expression of nonnegative integers with +, -, *, and / operators.", "Input: 3+2*2\nOutput: 7\n\nInput: 3/2\nOutput: 1", "1 <= len(s) <= 3*10^5; spaces may occur.", "O(n)", "O(n)", "stack,parsing"),
    ("Asteroid Collision", "NeetCode", "Stack", "Medium", 735, "Simulate collisions between moving asteroids and return survivors in order.", "Input: [5,10,-5]\nOutput: [5,10]\n\nInput: [8,-8]\nOutput: []", "2 <= n <= 10^4; values are nonzero.", "O(n)", "O(n)", "stack,simulation"),
    ("Remove K Digits", "Striver", "Stack", "Medium", 402, "Remove exactly k digits to form the numerically smallest remaining decimal string.", "Input: num=1432219, k=3\nOutput: 1219\n\nInput: num=10200, k=1\nOutput: 200", "1 <= len(num) <= 10^5; 0 <= k < len(num).", "O(n)", "O(n)", "monotonic-stack,greedy"),
    # ── Batch 5: Trees and Tries ──
    ("Same Tree", "Both", "Trees", "Easy", 100, "Return whether two binary trees have the same shape and value at every node.", "Input: [1,2,3], [1,2,3]\nOutput: true\n\nInput: [1,2], [1,null,2]\nOutput: false", "0 <= nodes <= 100; values fit signed 32-bit integers.", "O(n)", "O(h)", "tree,dfs"),
    ("Subtree of Another Tree", "Both", "Trees", "Easy", 572, "Determine if subRoot occurs as an exactly matching subtree of root.", "Input: root=[3,4,5,1,2], sub=[4,1,2]\nOutput: true\n\nInput: root=[3,4,5,1,2], sub=[4,1,2,0]\nOutput: false", "Trees have at most 2000 nodes.", "O(m*n)", "O(h)", "tree,dfs"),
    ("Construct Binary Tree from Preorder and Inorder Traversal", "Both", "Trees", "Medium", 105, "Rebuild the unique binary tree described by preorder and inorder traversals.", "Input: pre=[3,9,20,15,7], in=[9,3,15,20,7]\nOutput: [3,9,20,null,null,15,7]\n\nInput: pre=[-1], in=[-1]\nOutput: [-1]", "1 <= n <= 3000; values are unique.", "O(n)", "O(n)", "tree,recursion"),
    ("Kth Smallest Element in a BST", "Both", "Trees", "Medium", 230, "Return the kth value in sorted order from a binary search tree.", "Input: [3,1,4,null,2], k=1\nOutput: 1\n\nInput: [5,3,6,2,4,null,null,1], k=3\nOutput: 3", "1 <= k <= nodes <= 10^4.", "O(h+k)", "O(h)", "bst,inorder"),
    ("Binary Tree Maximum Path Sum", "Both", "Trees", "Hard", 124, "Find the greatest sum along any nonempty path between two tree nodes.", "Input: [1,2,3]\nOutput: 6\n\nInput: [-10,9,20,null,null,15,7]\nOutput: 42", "1 <= nodes <= 3*10^4; values fit signed 32-bit integers.", "O(n)", "O(h)", "tree,dfs"),
    ("Count Good Nodes in Binary Tree", "NeetCode", "Trees", "Medium", 1448, "Count nodes no smaller than every value encountered from root to that node.", "Input: [3,1,4,3,null,1,5]\nOutput: 4\n\nInput: [3,3,null,4,2]\nOutput: 3", "1 <= nodes <= 10^5.", "O(n)", "O(h)", "tree,dfs"),
    ("Symmetric Tree", "Both", "Trees", "Easy", 101, "Determine whether a binary tree is a mirror of itself.", "Input: [1,2,2,3,4,4,3]\nOutput: true\n\nInput: [1,2,2,null,3,null,3]\nOutput: false", "1 <= nodes <= 1000.", "O(n)", "O(h)", "tree,recursion"),
    ("Implement Trie (Prefix Tree)", "Both", "Tries", "Medium", 208, "Implement insert, exact-word search, and prefix search for lowercase words.", "Input: insert(apple), search(apple)\nOutput: true\n\nInput: startsWith(app)\nOutput: true", "At most 3*10^4 calls; lowercase words length <= 2000.", "O(L)", "O(total characters)", "trie,design"),
    ("Design Add and Search Words Data Structure", "Both", "Tries", "Medium", 211, "Support adding words and searching patterns where dot matches any one letter.", "Input: addWord(bad), search(.ad)\nOutput: true\n\nInput: search(b..)\nOutput: true", "At most 2.5*10^4 calls; lowercase words length <= 25.", "O(L) average", "O(total characters)", "trie,backtracking"),
    ("Word Search II", "Both", "Tries", "Hard", 212, "Find all dictionary words that can be traced through adjacent board cells without reuse.", "Input: board=[[o,a],[e,t]], words=[oat,eat]\nOutput: [oat,eat]\n\nInput: board=[[a]], words=[a]\nOutput: [a]", "Board <= 12x12; words length <= 10.", "O(mn*4^L)", "O(total characters)", "trie,dfs"),
    ("Binary Tree Preorder Traversal", "Striver", "Trees", "Easy", 144, "Return tree values in root, left, right order.", "Input: [1,null,2,3]\nOutput: [1,2,3]\n\nInput: []\nOutput: []", "0 <= nodes <= 100.", "O(n)", "O(h)", "tree,dfs"),
    ("Binary Tree Inorder Traversal", "Striver", "Trees", "Easy", 94, "Return tree values in left, root, right order.", "Input: [1,null,2,3]\nOutput: [1,3,2]\n\nInput: []\nOutput: []", "0 <= nodes <= 100.", "O(n)", "O(h)", "tree,dfs"),
    ("Lowest Common Ancestor of a Binary Tree", "Both", "Trees", "Medium", 236, "Find the deepest node that has both given nodes in its subtree.", "Input: [3,5,1,6,2,0,8], p=5, q=1\nOutput: 3\n\nInput: same tree, p=5, q=4\nOutput: 5", "2 <= nodes <= 10^5; nodes exist in tree.", "O(n)", "O(h)", "tree,dfs"),
    ("Path Sum", "Striver", "Trees", "Easy", 112, "Check whether a root-to-leaf path adds exactly to targetSum.", "Input: [5,4,8,11,null,13,4,7,2], target=22\nOutput: true\n\nInput: [1,2,3], target=5\nOutput: false", "0 <= nodes <= 5000.", "O(n)", "O(h)", "tree,dfs"),
    ("Binary Tree Zigzag Level Order Traversal", "Striver", "Trees", "Medium", 103, "Return levels of a tree while alternating left-to-right and right-to-left order.", "Input: [3,9,20,null,null,15,7]\nOutput: [[3],[20,9],[15,7]]\n\nInput: [1]\nOutput: [[1]]", "0 <= nodes <= 2000.", "O(n)", "O(n)", "tree,bfs"),
    ("Recover Binary Search Tree", "Striver", "Trees", "Medium", 99, "Repair a BST where exactly two node values were exchanged.", "Input: [1,3,null,null,2]\nOutput: [3,1,null,null,2]\n\nInput: [3,1,4,null,null,2]\nOutput: [2,1,4,null,null,3]", "2 <= nodes <= 1000; two values are swapped.", "O(n)", "O(h)", "bst,inorder"),
    ("Maximum Width of Binary Tree", "NeetCode", "Trees", "Medium", 662, "Return the greatest positional width across all levels of a binary tree.", "Input: [1,3,2,5,3,null,9]\nOutput: 4\n\nInput: [1,3,2,5]\nOutput: 2", "1 <= nodes <= 3000.", "O(n)", "O(n)", "tree,bfs"),
    ("Prefix and Suffix Search", "NeetCode", "Tries", "Hard", 745, "Return the greatest word index matching a requested prefix and suffix.", "Input: words=[apple], f(ap,le)\nOutput: 0\n\nInput: words=[apple], f(b, )\nOutput: -1", "At most 10^4 words and queries; words length <= 10.", "O(P+S) query", "O(total characters squared)", "trie,design"),
    # ── Batch 6: Graphs ──
    ("Word Ladder", "Both", "Graphs", "Hard", 127, "Return the shortest one-letter-at-a-time transformation length from beginWord to endWord.", "Input: hit->cog, [hot,dot,dog,lot,log,cog]\nOutput: 5\n\nInput: hit->cog, [hot,dot,dog]\nOutput: 0", "Words have equal length <= 10; list <= 5000.", "O(N*L^2)", "O(N*L)", "bfs,graph"),
    ("Surrounded Regions", "Both", "Graphs", "Medium", 130, "Flip O regions fully surrounded by X while preserving border-connected regions.", "Input: [[X,X,X],[X,O,X],[X,X,X]]\nOutput: all X\n\nInput: [[O]]\nOutput: [[O]]", "1 <= rows,cols <= 200.", "O(mn)", "O(mn)", "dfs,matrix"),
    ("Graph Valid Tree", "NeetCode", "Graphs", "Medium", 261, "Determine if n vertices and undirected edges form exactly one tree.", "Input: n=5, edges=[[0,1],[0,2],[0,3],[1,4]]\nOutput: true\n\nInput: n=5, edges=[[0,1],[1,2],[2,3],[1,3]]\nOutput: false", "1 <= n <= 2000; edges <= 5000.", "O(n+e)", "O(n)", "union-find,dfs"),
    ("Number of Connected Components in an Undirected Graph", "NeetCode", "Graphs", "Medium", 323, "Count disconnected groups among n vertices linked by undirected edges.", "Input: n=5, edges=[[0,1],[1,2],[3,4]]\nOutput: 2\n\nInput: n=5, edges=[]\nOutput: 5", "1 <= n <= 2000; edges <= 5000.", "O(n+e)", "O(n)", "union-find,graph"),
    ("Redundant Connection", "Both", "Graphs", "Medium", 684, "Return the last edge that creates a cycle in an undirected graph.", "Input: [[1,2],[1,3],[2,3]]\nOutput: [2,3]\n\nInput: [[1,2],[2,3],[3,4],[1,4]]\nOutput: [1,4]", "3 <= edges <= 1000; vertices labels are positive.", "O(n alpha(n))", "O(n)", "union-find,cycle"),
    ("Network Delay Time", "Both", "Graphs", "Medium", 743, "Find when all nodes receive a signal sent from one node, or report impossible.", "Input: [[2,1,1],[2,3,1],[3,4,1]], n=4, k=2\nOutput: 2\n\nInput: [[1,2,1]], n=2, k=2\nOutput: -1", "1 <= n <= 100; weighted directed edges <= 6000.", "O(E log V)", "O(V+E)", "dijkstra,graph"),
    ("Swim in Rising Water", "NeetCode", "Graphs", "Hard", 778, "Find the earliest water level permitting travel from the grid's top-left to bottom-right.", "Input: [[0,2],[1,3]]\nOutput: 3\n\nInput: [[0,1,2],[5,4,3],[6,7,8]]\nOutput: 8", "1 <= n <= 50; grid is a permutation of 0 through n^2-1.", "O(n^2 log n)", "O(n^2)", "dijkstra,heap"),
    ("Alien Dictionary", "NeetCode", "Graphs", "Hard", 269, "Infer a valid character ordering from a sorted dictionary of an unknown alphabet.", "Input: [wrt,wrf,er,ett,rftt]\nOutput: wertf\n\nInput: [z,x,z]\nOutput: ''", "1 <= words <= 100; lowercase word length <= 100.", "O(total characters)", "O(unique characters)", "topological-sort,graph"),
    ("Min Cost to Connect All Points", "Both", "Graphs", "Medium", 1584, "Connect all coordinate points using Manhattan-distance edges with minimum total cost.", "Input: [[0,0],[2,2],[3,10],[5,2],[7,0]]\nOutput: 20\n\nInput: [[3,12],[-2,5],[-4,1]]\nOutput: 18", "1 <= n <= 1000; coordinates <= 10^6.", "O(n^2)", "O(n)", "mst,prim"),
    ("Cheapest Flights Within K Stops", "Both", "Graphs", "Medium", 787, "Find the least flight cost from src to dst using at most k stops.", "Input: n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], k=1\nOutput: 200\n\nInput: same, k=0\nOutput: 500", "1 <= n <= 100; flights <= n*(n-1).", "O(kE)", "O(n)", "bellman-ford,graph"),
    ("Reconstruct Itinerary", "Both", "Graphs", "Hard", 332, "Use every flight ticket once and return the lexicographically smallest route from JFK.", "Input: [[MUC,LHR],[JFK,MUC],[SFO,SJC],[LHR,SFO]]\nOutput: [JFK,MUC,LHR,SFO,SJC]\n\nInput: [[JFK,KUL],[JFK,NRT],[NRT,JFK]]\nOutput: [JFK,NRT,JFK,KUL]", "1 <= tickets <= 300; valid itinerary exists.", "O(E log E)", "O(E)", "eulerian-path,graph"),
    ("Walls and Gates", "NeetCode", "Graphs", "Medium", 286, "Fill each empty room with distance to its nearest gate, leaving unreachable rooms unchanged.", "Input: [[INF,-1,0],[INF,INF,INF]]\nOutput: distances from gate\n\nInput: [[0]]\nOutput: [[0]]", "1 <= rows,cols <= 250.", "O(mn)", "O(mn)", "multi-source-bfs"),
    ("Evaluate Division", "NeetCode", "Graphs", "Medium", 399, "Answer quotient queries using known variable ratios.", "Input: a/b=2, b/c=3; a/c\nOutput: 6\n\nInput: a/b=2; b/a\nOutput: 0.5", "Variables and queries <= 20.", "O(V+E) per query", "O(V+E)", "dfs,weighted-graph"),
    ("Open the Lock", "NeetCode", "Graphs", "Medium", 752, "Find the fewest wheel turns from 0000 to target while avoiding blocked combinations.", "Input: deadends=[0201], target=0202\nOutput: 6\n\nInput: deadends=[0000], target=8888\nOutput: -1", "deadends <= 500; target has four digits.", "O(10^4)", "O(10^4)", "bfs,state-space"),
    ("Accounts Merge", "NeetCode", "Graphs", "Medium", 721, "Merge accounts sharing email addresses and return each owner with sorted emails.", "Input: [[John,a,b],[John,b,c]]\nOutput: [[John,a,b,c]]\n\nInput: [[Mary,x]]\nOutput: [[Mary,x]]", "Accounts <= 1000; emails <= 10 per account.", "O(N log N)", "O(N)", "union-find,graph"),
    # ── Batch 7: Dynamic Programming, Part 1 ──
    ("Unique Paths", "Both", "Dynamic Programming", "Medium", 62, "Count routes from a grid's top-left to bottom-right using only down and right moves.", "Input: m=3,n=7\nOutput: 28\n\nInput: m=3,n=2\nOutput: 3", "1 <= m,n <= 100.", "O(mn)", "O(n)", "dp,grid"),
    ("Decode Ways", "Both", "Dynamic Programming", "Medium", 91, "Count ways to split a digit string into valid 1 through 26 letter codes.", "Input: 12\nOutput: 2\n\nInput: 06\nOutput: 0", "1 <= len(s) <= 100; s contains digits.", "O(n)", "O(1)", "dp,strings"),
    ("House Robber II", "Both", "Dynamic Programming", "Medium", 213, "Maximize nonadjacent house value when the first and last houses are neighbors.", "Input: [2,3,2]\nOutput: 3\n\nInput: [1,2,3,1]\nOutput: 4", "1 <= n <= 100; values <= 1000.", "O(n)", "O(1)", "dp,circular"),
    ("Edit Distance", "Both", "Dynamic Programming", "Medium", 72, "Find the fewest insertions, deletions, or replacements turning one word into another.", "Input: horse,ros\nOutput: 3\n\nInput: intention,execution\nOutput: 5", "Word lengths <= 500.", "O(mn)", "O(mn)", "dp,strings"),
    ("Partition Equal Subset Sum", "Both", "Dynamic Programming", "Medium", 416, "Determine if nums can split into two groups with equal total.", "Input: [1,5,11,5]\nOutput: true\n\nInput: [1,2,3,5]\nOutput: false", "1 <= n <= 200; values <= 100.", "O(n*sum)", "O(sum)", "knapsack,dp"),
    ("Minimum Path Sum", "Both", "Dynamic Programming", "Medium", 64, "Find the smallest total along a top-left to bottom-right grid path.", "Input: [[1,3,1],[1,5,1],[4,2,1]]\nOutput: 7\n\nInput: [[1,2,3],[4,5,6]]\nOutput: 12", "1 <= rows,cols <= 200.", "O(mn)", "O(n)", "dp,grid"),
    ("Triangle", "Striver", "Dynamic Programming", "Medium", 120, "Find the least root-to-base sum in a triangle using adjacent lower moves.", "Input: [[2],[3,4],[6,5,7],[4,1,8,3]]\nOutput: 11\n\nInput: [[-10]]\nOutput: -10", "1 <= rows <= 200.", "O(n^2)", "O(n)", "dp,triangle"),
    ("Best Time to Buy and Sell Stock with Cooldown", "Both", "Dynamic Programming", "Medium", 309, "Maximize stock profit when selling forces one day of rest before buying.", "Input: [1,2,3,0,2]\nOutput: 3\n\nInput: [1]\nOutput: 0", "1 <= n <= 5000.", "O(n)", "O(1)", "dp,state-machine"),
    ("Distinct Subsequences", "Both", "Dynamic Programming", "Hard", 115, "Count ways target can be obtained by deleting characters from source.", "Input: rabbbit,rabbit\nOutput: 3\n\nInput: babgbag,bag\nOutput: 5", "Lengths <= 1000.", "O(mn)", "O(n)", "dp,subsequence"),
    ("Interleaving String", "Both", "Dynamic Programming", "Medium", 97, "Decide whether s3 can be formed by intermixing s1 and s2 while retaining both orders.", "Input: aabcc,dbbca,aadbbcbcac\nOutput: true\n\nInput: aabcc,dbbca,aadbbbaccc\nOutput: false", "Each length <= 100.", "O(mn)", "O(n)", "dp,strings"),
    ("Maximum Length of Repeated Subarray", "Striver", "Dynamic Programming", "Medium", 718, "Find the greatest length of a contiguous sequence shared by two arrays.", "Input: [1,2,3,2,1], [3,2,1,4,7]\nOutput: 3\n\nInput: [0,0,0], [0,0]\nOutput: 2", "Array lengths <= 1000.", "O(mn)", "O(n)", "dp,arrays"),
    ("Matrix Chain Multiplication", "Striver", "Dynamic Programming", "Hard", 0, "Choose parenthesization minimizing scalar operations for compatible matrix dimensions.", "Input: dims=[10,30,5,60]\nOutput: 4500\n\nInput: dims=[40,20,30,10,30]\nOutput: 26000", "2 <= dimensions <= 100; values positive.", "O(n^3)", "O(n^2)", "interval-dp"),
    ("Egg Drop Problem", "Striver", "Dynamic Programming", "Hard", 0, "Find the minimum worst-case attempts needed to locate the highest safe floor.", "Input: eggs=1,floors=2\nOutput: 2\n\nInput: eggs=2,floors=6\nOutput: 3", "1 <= eggs <= 100; 0 <= floors <= 10^4.", "O(eggs*floors log floors)", "O(eggs*floors)", "dp,optimization"),
    ("Arithmetic Slices", "NeetCode", "Dynamic Programming", "Medium", 413, "Count contiguous subarrays of length at least three with one common difference.", "Input: [1,2,3,4]\nOutput: 3\n\nInput: [1]\nOutput: 0", "1 <= n <= 5000.", "O(n)", "O(1)", "dp,arrays"),
    ("Delete and Earn", "NeetCode", "Dynamic Programming", "Medium", 740, "Maximize points when taking value x removes all x-1 and x+1 values.", "Input: [3,4,2]\nOutput: 6\n\nInput: [2,2,3,3,3,4]\nOutput: 9", "1 <= n <= 2*10^4; values <= 10^4.", "O(n+maxValue)", "O(maxValue)", "dp,house-robber"),
    ("Maximal Square", "Both", "Dynamic Programming", "Medium", 221, "Find the area of the largest square consisting solely of ones in a binary matrix.", "Input: [[1,0,1],[1,1,1],[1,1,1]]\nOutput: 4\n\nInput: [[0,1]]\nOutput: 1", "1 <= rows,cols <= 300.", "O(mn)", "O(n)", "dp,matrix"),
    ("Longest Palindromic Subsequence", "Both", "Dynamic Programming", "Medium", 516, "Return the greatest length of a palindrome obtainable by deleting characters from s.", "Input: bbbab\nOutput: 4\n\nInput: cbbd\nOutput: 2", "1 <= len(s) <= 1000.", "O(n^2)", "O(n^2)", "dp,palindrome"),
    ("Count Vowels Permutation", "NeetCode", "Dynamic Programming", "Hard", 1220, "Count vowel strings of length n that obey specified next-vowel rules.", "Input: n=1\nOutput: 5\n\nInput: n=2\nOutput: 10", "1 <= n <= 2*10^4.", "O(n)", "O(1)", "dp,states"),
    # ── Batch 8: Remaining DP, Greedy, Design, Matrix, Math, and Heap ──
    ("Burst Balloons", "Both", "Dynamic Programming", "Hard", 312, "Choose balloon popping order to maximize coins earned from adjacent remaining values.", "Input: [3,1,5,8]\nOutput: 167\n\nInput: [1,5]\nOutput: 10", "1 <= n <= 300; values <= 100.", "O(n^3)", "O(n^2)", "interval-dp"),
    ("Target Sum", "Both", "Dynamic Programming", "Medium", 494, "Count sign assignments before nums that produce target.", "Input: [1,1,1,1,1], target=3\nOutput: 5\n\nInput: [1], target=1\nOutput: 1", "1 <= n <= 20; values <= 1000.", "O(n*sum)", "O(sum)", "dp,subset-sum"),
    ("Regular Expression Matching", "Both", "Dynamic Programming", "Hard", 10, "Match a string against a pattern containing dot and star operators.", "Input: aa,a\nOutput: false\n\nInput: aa,a*\nOutput: true", "String and pattern lengths <= 20.", "O(mn)", "O(mn)", "dp,strings"),
    ("Jump Game", "Both", "Greedy", "Medium", 55, "Determine whether jumps up to nums[i] can reach the final index.", "Input: [2,3,1,1,4]\nOutput: true\n\nInput: [3,2,1,0,4]\nOutput: false", "1 <= n <= 10^4.", "O(n)", "O(1)", "greedy"),
    ("Jump Game II", "Both", "Greedy", "Medium", 45, "Return the fewest jumps needed to reach the final index.", "Input: [2,3,1,1,4]\nOutput: 2\n\nInput: [2,3,0,1,4]\nOutput: 2", "1 <= n <= 10^4; end is reachable.", "O(n)", "O(1)", "greedy"),
    ("Gas Station", "Both", "Greedy", "Medium", 134, "Find a start index permitting one full circuit with available gas and travel costs.", "Input: gas=[1,2,3,4,5], cost=[3,4,5,1,2]\nOutput: 3\n\nInput: gas=[2,3,4], cost=[3,4,3]\nOutput: -1", "1 <= n <= 10^5; gas and cost nonnegative.", "O(n)", "O(1)", "greedy,circular"),
    ("Hand of Straights", "Both", "Greedy", "Medium", 846, "Check whether cards can form groups of consecutive groupSize cards.", "Input: [1,2,3,6,2,3,4,7,8], size=3\nOutput: true\n\nInput: [1,2,3,4,5], size=4\nOutput: false", "1 <= n <= 10^4.", "O(n log n)", "O(n)", "greedy,hashing"),
    ("Design Twitter", "NeetCode", "Design", "Medium", 355, "Implement posting, following, unfollowing, and a ten-item recent news feed.", "Input: post(1,5), feed(1)\nOutput: [5]\n\nInput: follow(1,2), post(2,6), feed(1)\nOutput: [6,5]", "At most 3*10^4 operations.", "O(F log F) feed", "O(posts+follows)", "design,heap"),
    ("Implement Queue using Stacks", "Both", "Design", "Easy", 232, "Implement FIFO queue operations using only stack operations.", "Input: push(1),push(2),peek()\nOutput: 1\n\nInput: pop(),empty()\nOutput: 1,false", "At most 100 calls; values fit signed 32-bit integers.", "O(1) amortized", "O(n)", "design,stacks"),
    ("Word Search", "Both", "Backtracking", "Medium", 79, "Decide if a word can be traced through adjacent distinct cells of a board.", "Input: board=[[A,B],[C,D]], word=AB\nOutput: true\n\nInput: board=[[A]], word=B\nOutput: false", "Board <= 6x6; word length <= 15.", "O(mn*4^L)", "O(L)", "dfs,backtracking"),
    ("Multiply Strings", "Both", "Math", "Medium", 43, "Multiply two nonnegative integer strings without converting them to built-in big integers.", "Input: 2,3\nOutput: 6\n\nInput: 123,456\nOutput: 56088", "Lengths <= 200; digits only.", "O(mn)", "O(m+n)", "math,simulation"),
    ("Task Scheduler", "Both", "Heap", "Medium", 621, "Find minimum intervals needed with equal-task cooldown n.", "Input: [A,A,A,B,B,B], n=2\nOutput: 8\n\nInput: [A,A,A,B,B,B], n=0\nOutput: 6", "1 <= tasks <= 10^4; task labels A-Z.", "O(n)", "O(1)", "greedy,frequency"),
    ("Find K Pairs with Smallest Sums", "NeetCode", "Heap", "Medium", 373, "Return k index pairs from sorted arrays having smallest pair sums.", "Input: [1,7,11],[2,4,6],k=3\nOutput: [[1,2],[1,4],[1,6]]\n\nInput: [1,1,2],[1,2,3],k=2\nOutput: [[1,1],[1,1]]", "Arrays <= 10^5; 1 <= k <= 10^4.", "O(k log k)", "O(k)", "heap,arrays"),
    ("Happy Number", "Both", "Math", "Easy", 202, "Determine whether repeatedly replacing n by digit-square sum eventually reaches one.", "Input: 19\nOutput: true\n\nInput: 2\nOutput: false", "1 <= n <= 2^31-1.", "O(log n)", "O(log n)", "math,hash-set"),
    ("Missing Number", "Both", "Bit Manipulation", "Easy", 268, "Find the missing value from n distinct numbers drawn from 0 through n.", "Input: [3,0,1]\nOutput: 2\n\nInput: [0,1]\nOutput: 2", "1 <= n <= 10^4; values are distinct.", "O(n)", "O(1)", "xor,math"),
]


def seed(force: bool = False) -> int:
    """
    Seed the question bank. Returns number of rows inserted.
    If force=True, clears existing data first.
    """
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        existing = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if existing > 0 and not force:
            print(f"[ncode] Question bank already seeded with {existing} questions. Skipping.")
            return 0

        if force:
            conn.execute("DELETE FROM questions")

        inserted = 0
        for q in QUESTIONS:
            (title, source, topic, difficulty, lc_num,
             problem, examples, constraints, time_c, space_c, tags) = q
            conn.execute(
                """
                INSERT OR IGNORE INTO questions
                (title, source, topic, difficulty, lc_number, problem_statement,
                 examples, constraints, time_complexity, space_complexity, tags)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (title, source, topic, difficulty, lc_num,
                 problem, examples, constraints, time_c, space_c, tags),
            )
            inserted += conn.execute("SELECT changes()").fetchone()[0]

        conn.commit()
        print(f"[ncode] Seeded {inserted} questions into {DB_PATH}")
        return inserted
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Re-seed even if data exists")
    args = ap.parse_args()
    n = seed(force=args.force)
    print(f"Done. {n} questions added.")
