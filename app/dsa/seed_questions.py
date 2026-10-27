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
