# SPDX-License-Identifier: GPL-3.0-only
"""Comprehensive Ollama Model Tester - Evaluates model intelligence and coding ability.

This module tests LLM models on:
1. SMARTNESS: Logic, reasoning, math, comprehension, and problem-solving
2. CODING: Ability to write correct, functional code across different difficulties

Results include detailed scoring with breakdowns for each category.
"""
import time
import statistics
import re
import json
from typing import Any, Dict, List, Optional, Tuple


def _get_response_text(resp) -> Optional[str]:
    """Extract text from various response formats."""
    if resp is None:
        return None
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        return resp.get('message', {}).get('content') or resp.get('response') or resp.get('text') or str(resp)
    # Object response
    return (getattr(resp, 'text', None) or 
            getattr(resp, 'response', None) or 
            getattr(resp, 'content', None) or
            (getattr(resp, 'message', {}).get('content') if hasattr(resp, 'message') else None) or
            str(resp))


def _chat_with_model(client, model: str, prompt: str, timeout: int = 60) -> Tuple[float, Optional[str], Optional[str]]:
    """Send a prompt to the model and return (latency, response_text, error)."""
    start = time.time()
    try:
        resp = client.chat(model=model, messages=[{"role": "user", "content": prompt}])
        text = _get_response_text(resp)
        return time.time() - start, text, None
    except Exception as e:
        return time.time() - start, None, str(e)


# ==================== SMARTNESS TESTS ====================

SMARTNESS_TESTS = [
    # Basic Math (10 points each, 30 total)
    {
        "name": "Basic Arithmetic",
        "prompt": "What is 17 + 28? Reply with just the number.",
        "check": lambda r: bool(re.search(r'\b45\b', str(r))),
        "points": 10,
        "category": "math"
    },
    {
        "name": "Multiplication",
        "prompt": "What is 12 × 15? Reply with just the number.",
        "check": lambda r: bool(re.search(r'\b180\b', str(r))),
        "points": 10,
        "category": "math"
    },
    {
        "name": "Word Problem",
        "prompt": "A store sells apples for $2 each. If you buy 7 apples and pay with a $20 bill, how much change do you get? Just the number.",
        "check": lambda r: bool(re.search(r'\b6\b', str(r))),
        "points": 10,
        "category": "math"
    },
    
    # Logic & Reasoning (15 points each, 45 total)
    {
        "name": "Sequence Pattern",
        "prompt": "What comes next in this sequence: 2, 6, 12, 20, 30, ? Reply with just the number.",
        "check": lambda r: bool(re.search(r'\b42\b', str(r))),
        "points": 15,
        "category": "logic"
    },
    {
        "name": "Logical Deduction",
        "prompt": "All roses are flowers. Some flowers fade quickly. Can we conclude that some roses fade quickly? Answer yes or no only.",
        "check": lambda r: 'no' in str(r).lower(),
        "points": 15,
        "category": "logic"
    },
    {
        "name": "Comparison Logic",
        "prompt": "If A > B, B > C, and C > D, is A > D? Answer yes or no only.",
        "check": lambda r: 'yes' in str(r).lower() and 'no' not in str(r).lower(),
        "points": 15,
        "category": "logic"
    },
    
    # Comprehension & Knowledge (10 points each, 25 total)
    {
        "name": "Factual Knowledge",
        "prompt": "What is the capital of France? Reply with just the city name.",
        "check": lambda r: 'paris' in str(r).lower(),
        "points": 10,
        "category": "knowledge"
    },
    {
        "name": "Reading Comprehension",
        "prompt": "Read this: 'The blue car is faster than the red car. The green car is slower than the red car.' Which car is the slowest? Reply with just the color.",
        "check": lambda r: 'green' in str(r).lower(),
        "points": 15,
        "category": "knowledge"
    }
]


def _run_smartness_tests(client, model: str) -> Dict[str, Any]:
    """Run all smartness tests and return detailed results."""
    results = []
    total_points = 0
    earned_points = 0
    category_scores = {"math": {"earned": 0, "total": 0}, 
                       "logic": {"earned": 0, "total": 0}, 
                       "knowledge": {"earned": 0, "total": 0}}
    
    for test in SMARTNESS_TESTS:
        total_points += test["points"]
        category_scores[test["category"]]["total"] += test["points"]
        
        latency, response, error = _chat_with_model(client, model, test["prompt"])
        
        passed = False
        if response and not error:
            try:
                passed = test["check"](response)
            except Exception:
                passed = False
        
        if passed:
            earned_points += test["points"]
            category_scores[test["category"]]["earned"] += test["points"]
        
        results.append({
            "name": test["name"],
            "category": test["category"],
            "points": test["points"],
            "passed": passed,
            "latency_s": round(latency, 3),
            "response": response[:500] if response else error,
            "error": error
        })
    
    # Calculate percentage scores
    overall_score = round((earned_points / total_points) * 100, 1) if total_points > 0 else 0
    
    category_percentages = {}
    for cat, scores in category_scores.items():
        if scores["total"] > 0:
            category_percentages[cat] = round((scores["earned"] / scores["total"]) * 100, 1)
        else:
            category_percentages[cat] = 0
    
    return {
        "score": overall_score,
        "earned_points": earned_points,
        "total_points": total_points,
        "category_scores": category_percentages,
        "tests": results
    }

# ==================== CODING TESTS ====================

CODING_TESTS = [
    # Easy (25 points each, 50 total)
    {
        "name": "Sum of List",
        "difficulty": "easy",
        "prompt": """Write a Python function called `solve(nums)` that returns the sum of all numbers in the list.
Example: solve([1, 2, 3]) should return 6
Return ONLY the function definition, no explanations.""",
        "test_cases": [([1, 2, 3], 6), ([0, 0, 0], 0), ([-1, 1, 5], 5), ([10], 10), ([], 0)],
        "points": 25
    },
    {
        "name": "Find Maximum",
        "difficulty": "easy",
        "prompt": """Write a Python function called `solve(nums)` that returns the maximum number in the list.
Example: solve([1, 5, 3]) should return 5
Return ONLY the function definition, no explanations.""",
        "test_cases": [([1, 5, 3], 5), ([-1, -5, -3], -1), ([7], 7), ([0, 0, 1], 1)],
        "points": 25
    },
    
    # Medium (30 points each, 60 total)
    {
        "name": "Count Vowels",
        "difficulty": "medium",
        "prompt": """Write a Python function called `solve(text)` that returns the count of vowels (a, e, i, o, u) in the string.
Example: solve("hello") should return 2
Return ONLY the function definition, no explanations.""",
        "test_cases": [("hello", 2), ("AEIOU", 5), ("xyz", 0), ("Programming", 3), ("", 0)],
        "points": 30
    },
    {
        "name": "Reverse Words",
        "difficulty": "medium", 
        "prompt": """Write a Python function called `solve(text)` that reverses the order of words in a string.
Example: solve("hello world") should return "world hello"
Return ONLY the function definition, no explanations.""",
        "test_cases": [("hello world", "world hello"), ("a b c", "c b a"), ("single", "single"), ("  spaced  ", "spaced")],
        "points": 30
    },
    
    # Hard (40 points)
    {
        "name": "Fibonacci Sequence",
        "difficulty": "hard",
        "prompt": """Write a Python function called `solve(n)` that returns the nth Fibonacci number (0-indexed).
F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)
Example: solve(6) should return 8 (sequence: 0,1,1,2,3,5,8)
Return ONLY the function definition, no explanations.""",
        "test_cases": [(0, 0), (1, 1), (6, 8), (10, 55), (15, 610)],
        "points": 40
    }
]


def _extract_code(text: str) -> str:
    """Extract Python code from model response."""
    if not text:
        return ''
    
    # Extract from code blocks first
    m = re.search(r"```(?:python)?\s*([\s\S]*?)```", text, flags=re.I)
    if m:
        code = m.group(1).strip()
    else:
        # Find function definition
        func_match = re.search(r'def\s+\w+\s*\([^)]*\):', text)
        if func_match:
            code = text[func_match.start():]
            # Get just the function
            lines = code.split('\n')
            result = []
            in_function = False
            base_indent = None
            
            for line in lines:
                if not line.strip():
                    if in_function:
                        result.append(line)
                    continue
                    
                current_indent = len(line) - len(line.lstrip())
                
                if line.strip().startswith('def '):
                    if in_function and base_indent is not None and current_indent <= base_indent:
                        break  # New function at same or lower indent
                    in_function = True
                    base_indent = current_indent
                    result.append(line)
                elif in_function:
                    if current_indent <= base_indent and not line.strip().startswith(('#', '"', "'")):
                        if not line.strip().startswith('return') and current_indent == base_indent:
                            break
                    result.append(line)
            
            code = '\n'.join(result).strip()
        else:
            return ''
    
    # Handle escape sequences
    try:
        code = code.encode('utf-8').decode('unicode_escape')
    except Exception:
        code = code.replace('\\n', '\n').replace('\\t', '\t')
    
    return code


def _run_code_safely(code_src: str, test_cases: List[Tuple], timeout: int = 5) -> Tuple[int, int, List[Dict]]:
    """Execute code in sandbox and run test cases. Returns (passed, total, details)."""
    import tempfile
    import subprocess
    import sys
    import os
    
    if not code_src:
        return 0, len(test_cases), [{'error': 'No code extracted from response'}]
    
    # Security check
    dangerous = ['subprocess', 'socket', 'requests', 'eval(', 'exec(', '__import__', 'open(', 'os.system']
    for pattern in dangerous:
        if pattern in code_src:
            return 0, len(test_cases), [{'error': f'Forbidden pattern: {pattern}'}]
    
    # Build test harness
    harness = f'''# -*- coding: utf-8 -*-
import json
import sys

{code_src}

def _run():
    tests = {repr(test_cases)}
    results = []
    passed = 0
    
    # Find the solve function
    fn = None
    for name in ('solve', 'solution', 'main'):
        if name in globals() and callable(globals()[name]):
            fn = globals()[name]
            break
    
    if not fn:
        for v in list(globals().values()):
            if callable(v) and not v.__name__.startswith('_'):
                fn = v
                break
    
    if not fn:
        print(json.dumps({{"error": "No function found"}}))
        return
    
    for inp, expected in tests:
        try:
            # Handle both single arg and tuple args
            if isinstance(inp, (list, str, int)):
                result = fn(inp)
            else:
                result = fn(*inp)
            
            # Flexible comparison for strings
            ok = result == expected
            if not ok and isinstance(expected, str) and isinstance(result, str):
                ok = result.strip() == expected.strip()
            
            if ok:
                passed += 1
            results.append({{"input": repr(inp), "expected": expected, "got": result, "passed": ok}})
        except Exception as e:
            results.append({{"input": repr(inp), "expected": expected, "error": str(e), "passed": False}})
    
    print(json.dumps({{"passed": passed, "total": len(tests), "results": results}}))

if __name__ == "__main__":
    _run()
'''
    
    tf = None
    try:
        tf = tempfile.NamedTemporaryFile('w', delete=False, suffix='.py', encoding='utf-8')
        tf.write(harness)
        tf.flush()
        tf_name = tf.name
        tf.close()
        
        try:
            result = subprocess.run(
                [sys.executable, tf_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return 0, len(test_cases), [{'error': f'Execution timeout ({timeout}s)'}]
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if not stdout:
            return 0, len(test_cases), [{'error': f'No output. Stderr: {stderr[:200]}'}]
        
        try:
            data = json.loads(stdout)
            if 'error' in data:
                return 0, len(test_cases), [{'error': data['error']}]
            return data.get('passed', 0), data.get('total', len(test_cases)), data.get('results', [])
        except json.JSONDecodeError:
            return 0, len(test_cases), [{'error': f'Invalid JSON: {stdout[:100]}'}]
    
    finally:
        if tf:
            try:
                os.unlink(tf_name)
            except Exception:
                pass


def _run_coding_tests(client, model: str) -> Dict[str, Any]:
    """Run all coding tests and return detailed results."""
    results = []
    total_points = 0
    earned_points = 0
    difficulty_scores = {"easy": {"earned": 0, "total": 0},
                         "medium": {"earned": 0, "total": 0},
                         "hard": {"earned": 0, "total": 0}}
    
    for test in CODING_TESTS:
        total_points += test["points"]
        difficulty_scores[test["difficulty"]]["total"] += test["points"]
        
        latency, response, error = _chat_with_model(client, model, test["prompt"])
        
        if error:
            results.append({
                "name": test["name"],
                "difficulty": test["difficulty"],
                "points": test["points"],
                "earned": 0,
                "passed_tests": 0,
                "total_tests": len(test["test_cases"]),
                "latency_s": round(latency, 3),
                "error": error,
                "code": None,
                "test_results": []
            })
            continue
        
        code = _extract_code(response)
        passed, total, test_details = _run_code_safely(code, test["test_cases"])
        
        # Calculate points based on test pass rate
        if total > 0:
            points_earned = int((passed / total) * test["points"])
        else:
            points_earned = 0
        
        earned_points += points_earned
        difficulty_scores[test["difficulty"]]["earned"] += points_earned
        
        results.append({
            "name": test["name"],
            "difficulty": test["difficulty"],
            "points": test["points"],
            "earned": points_earned,
            "passed_tests": passed,
            "total_tests": total,
            "latency_s": round(latency, 3),
            "code": code[:500] if code else None,
            "raw_response": response[:300] if response else None,
            "test_results": test_details[:5]  # Limit to first 5 for display
        })
    
    # Calculate scores
    overall_score = round((earned_points / total_points) * 100, 1) if total_points > 0 else 0
    
    difficulty_percentages = {}
    for diff, scores in difficulty_scores.items():
        if scores["total"] > 0:
            difficulty_percentages[diff] = round((scores["earned"] / scores["total"]) * 100, 1)
        else:
            difficulty_percentages[diff] = 0
    
    return {
        "score": overall_score,
        "earned_points": earned_points,
        "total_points": total_points,
        "difficulty_scores": difficulty_percentages,
        "tests": results
    }


# ==================== MAIN TEST FUNCTION ====================

def test_model(client, model: str, repeat: int = 1) -> Dict[str, Any]:
    """Run comprehensive tests against a model.
    
    Tests include:
    - Smartness: Math, logic, reasoning, and knowledge tests
    - Coding: Easy, medium, and hard programming challenges
    
    Returns detailed results with scores and breakdowns.
    """
    all_latencies = []
    
    # Run smartness tests
    smartness_results = _run_smartness_tests(client, model)
    for test in smartness_results.get("tests", []):
        if test.get("latency_s"):
            all_latencies.append(test["latency_s"])
    
    # Run coding tests
    coding_results = _run_coding_tests(client, model)
    for test in coding_results.get("tests", []):
        if test.get("latency_s"):
            all_latencies.append(test["latency_s"])
    
    # Calculate latency stats
    if all_latencies:
        latency_stats = {
            "mean": round(statistics.mean(all_latencies), 4),
            "median": round(statistics.median(all_latencies), 4),
            "min": round(min(all_latencies), 4),
            "max": round(max(all_latencies), 4),
        }
    else:
        latency_stats = {"mean": None, "median": None, "min": None, "max": None}
    
    # Build test passes for UI compatibility
    smartness_passes = []
    for t in smartness_results.get("tests", []):
        smartness_passes.append({
            "latency_s": t.get("latency_s", 0),
            "response": f"[{t['category'].upper()}] {t['name']}: {'✓ PASS' if t['passed'] else '✗ FAIL'} ({t['points']}pts) - {str(t.get('response', ''))[:100]}"
        })
    
    coding_passes = []
    for t in coding_results.get("tests", []):
        status = f"✓ {t['passed_tests']}/{t['total_tests']}" if t.get('passed_tests', 0) > 0 else f"✗ {t['passed_tests']}/{t['total_tests']}"
        coding_passes.append({
            "latency_s": t.get("latency_s", 0),
            "response": f"[{t['difficulty'].upper()}] {t['name']}: {status} ({t['earned']}/{t['points']}pts)"
        })
        if t.get('error'):
            coding_passes[-1]['response'] += f" - Error: {t['error']}"
        elif t.get('code'):
            coding_passes[-1]['response'] += f"\nCode: {t['code'][:200]}..."
    
    return {
        "model": model,
        "latency_stats": latency_stats,
        "smartness_score": smartness_results.get("score"),
        "code_score": coding_results.get("score"),
        "smartness_details": {
            "score": smartness_results.get("score"),
            "points": f"{smartness_results.get('earned_points', 0)}/{smartness_results.get('total_points', 0)}",
            "categories": smartness_results.get("category_scores", {})
        },
        "coding_details": {
            "score": coding_results.get("score"),
            "points": f"{coding_results.get('earned_points', 0)}/{coding_results.get('total_points', 0)}",
            "difficulties": coding_results.get("difficulty_scores", {})
        },
        "tests": [
            {"name": "smartness", "passes": smartness_passes},
            {"name": "coding", "passes": coding_passes}
        ],
    }
