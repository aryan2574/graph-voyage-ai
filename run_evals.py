"""
Phase 1 Evaluation Demo
-----------------------
This script demonstrates how to use the evaluation functions with your multi-agent
travel planning system.

Usage:
    python run_evals.py

This will:
1. Load test cases from eval_dataset.json
2. Run each test through your agent system (simulated for demo)
3. Apply evaluation functions
4. Print results
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

# Import evaluation functions
from evals import (
    evaluate_answer,
    evaluate_tool_selection,
    evaluate_trajectory,
    evaluate_latency,
    evaluate_safety_and_reliability,
    llm_as_judge,
    contains_forbidden_text,
)

# Uncomment when you want to test with real backend
# from backend import run_travel_agent, resume_travel_agent


def load_eval_dataset(path="eval_dataset.json"):
    """Load test cases from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def simulate_agent_result(test_case):
    """
    Simulate agent execution for demo purposes.
    
    In production, replace this with actual call to run_travel_agent():
        result = run_travel_agent(test_case["query"])
    """
    # Simulated result for demonstration
    return {
        "answer": f"Simulated response for: {test_case['query']}",
        "tools_used": test_case.get("expected_tools", []),
        "trajectory": test_case.get("expected_trajectory", []),
        "latency_seconds": 10.5,
        "guardrail_allowed": test_case["type"] != "safety",
        "thread_id": "test_thread_001"
    }


def run_single_eval(test_case):
    """Run evaluation on a single test case."""
    print(f"\n{'='*80}")
    print(f"Test ID: {test_case['id']}")
    print(f"Type: {test_case['type']}")
    print(f"Query: {test_case['query']}")
    print(f"-" * 80)
    
    # Get agent result (simulated for demo)
    result = simulate_agent_result(test_case)
    
    # Initialize eval results
    eval_results = {
        "test_id": test_case["id"],
        "query": test_case["query"],
        "type": test_case["type"],
    }
    
    # 1. Evaluate Answer Correctness (if expected keywords provided)
    if "expected_keywords" in test_case:
        answer_correct = evaluate_answer(
            result["answer"],
            test_case["expected_keywords"]
        )
        eval_results["answer_correct"] = answer_correct
        print(f"✓ Answer Correctness: {'PASS' if answer_correct else 'FAIL'}")
        print(f"  Expected keywords: {test_case['expected_keywords']}")
    
    # 2. Evaluate Tool Selection (if expected tools provided)
    if "expected_tools" in test_case:
        tool_selection_correct = evaluate_tool_selection(
            result["tools_used"],
            test_case["expected_tools"]
        )
        eval_results["tool_selection_correct"] = tool_selection_correct
        print(f"✓ Tool Selection: {'PASS' if tool_selection_correct else 'FAIL'}")
        print(f"  Expected: {test_case['expected_tools']}")
        print(f"  Actual: {result['tools_used']}")
    
    # 3. Evaluate Trajectory (if expected trajectory provided)
    if "expected_trajectory" in test_case:
        trajectory_correct = evaluate_trajectory(
            result["trajectory"],
            test_case["expected_trajectory"]
        )
        eval_results["trajectory_correct"] = trajectory_correct
        print(f"✓ Trajectory: {'PASS' if trajectory_correct else 'FAIL'}")
        print(f"  Expected: {test_case['expected_trajectory']}")
        print(f"  Actual: {result['trajectory']}")
    
    # 4. Evaluate Latency
    if "max_latency" in test_case:
        latency_ok = evaluate_latency(
            result["latency_seconds"],
            test_case["max_latency"]
        )
        eval_results["latency_ok"] = latency_ok
        print(f"✓ Latency: {'PASS' if latency_ok else 'FAIL'}")
        print(f"  Actual: {result['latency_seconds']:.2f}s | Max: {test_case['max_latency']}s")
    
    # 5. Evaluate Safety (for all test types)
    safety_passed = evaluate_safety_and_reliability(test_case, result)
    eval_results["safety_passed"] = safety_passed
    print(f"✓ Safety & Reliability: {'PASS' if safety_passed else 'FAIL'}")
    
    # 6. LLM-as-Judge (optional, costs tokens - uncomment to use)
    # Uncomment the following lines to enable LLM-based evaluation:
    # llm_verdict = llm_as_judge(test_case["query"], result["answer"])
    # eval_results["llm_verdict"] = llm_verdict
    # print(f"✓ LLM Judge Verdict:\n  {llm_verdict}")
    
    print(f"{'='*80}\n")
    
    return eval_results


def run_all_evals(dataset_path="eval_dataset.json"):
    """Run evaluations on all test cases."""
    print("\n" + "="*80)
    print("PHASE 1: EVALUATION SYSTEM DEMO")
    print("="*80)
    
    # Load test cases
    test_cases = load_eval_dataset(dataset_path)
    print(f"\nLoaded {len(test_cases)} test cases from {dataset_path}")
    
    # Run evals
    all_results = []
    for test_case in test_cases:
        try:
            result = run_single_eval(test_case)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR in test {test_case['id']}: {e}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_tests = len(all_results)
    
    # Count passes by type
    answer_passes = sum(1 for r in all_results if r.get("answer_correct", True))
    tool_passes = sum(1 for r in all_results if r.get("tool_selection_correct", True))
    trajectory_passes = sum(1 for r in all_results if r.get("trajectory_correct", True))
    latency_passes = sum(1 for r in all_results if r.get("latency_ok", True))
    safety_passes = sum(1 for r in all_results if r.get("safety_passed", True))
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Answer Correctness: {answer_passes}/{total_tests} ({100*answer_passes/total_tests:.1f}%)")
    print(f"Tool Selection: {tool_passes}/{total_tests} ({100*tool_passes/total_tests:.1f}%)")
    print(f"Trajectory: {trajectory_passes}/{total_tests} ({100*trajectory_passes/total_tests:.1f}%)")
    print(f"Latency: {latency_passes}/{total_tests} ({100*latency_passes/total_tests:.1f}%)")
    print(f"Safety: {safety_passes}/{total_tests} ({100*safety_passes/total_tests:.1f}%)")
    
    # Breakdown by test type
    print("\n" + "-"*80)
    print("BREAKDOWN BY TEST TYPE")
    print("-"*80)
    
    test_types = {}
    for result in all_results:
        test_type = result["type"]
        if test_type not in test_types:
            test_types[test_type] = []
        test_types[test_type].append(result)
    
    for test_type, results in test_types.items():
        passes = sum(1 for r in results if r.get("safety_passed", True))
        print(f"{test_type.upper()}: {passes}/{len(results)} passed")
    
    print("\n" + "="*80)
    print("Phase 1 Complete! ✓")
    print("="*80)
    print("\nNext Steps:")
    print("1. Uncomment 'from backend import run_travel_agent' to test with real agents")
    print("2. Replace simulate_agent_result() with actual run_travel_agent() calls")
    print("3. Enable LLM-as-Judge evaluation (line 102) for quality scoring")
    print("4. Expand eval_dataset.json with more test cases")
    print("5. Move to Phase 2-3: Build offline eval pipeline with Pandas\n")
    
    return all_results


if __name__ == "__main__":
    results = run_all_evals()
