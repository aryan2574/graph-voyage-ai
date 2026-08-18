"""
Run Guardrail Evaluation Demo

This script demonstrates Phase 6: Guardrail evaluation and improvement.

What it does:
1. Loads guardrail test cases from eval_dataset.json
2. Runs each test through your travel agent's guardrail
3. Calculates confusion matrix metrics
4. Shows which attacks got through (security issues)
5. Shows which safe queries were blocked (UX issues)
6. Provides actionable recommendations for improvement

Usage:
    python run_guardrail_evals.py
    
Output:
    - Confusion matrix visualization
    - Precision, Recall, F1 Score
    - Specific failures with recommendations
    - Overall guardrail assessment
"""

import json
import time
from backend import run_travel_agent
from evals import (
    evaluate_guardrail_performance,
    get_guardrail_failures,
    print_guardrail_report
)
import pandas as pd


def run_guardrail_tests():
    """
    Run all guardrail tests and generate a comprehensive report.
    
    This tests your guardrail against:
    - Safe queries (should NOT be blocked)
    - Attack queries (should be blocked)
    - Off-topic queries (should be blocked)
    - Edge cases (tricky borderline queries)
    """
    
    print("\n" + "="*80)
    print("PHASE 6: GUARDRAIL EVALUATION")
    print("="*80)
    print("\nTesting your guardrail security system...")
    print("This will run 60+ test cases to evaluate guardrail performance.\n")
    
    # Load test dataset
    print("📂 Loading test dataset...")
    with open("eval_dataset.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    
    # Filter only guardrail tests
    guardrail_tests = [tc for tc in test_cases if tc.get("type") == "guardrail_test"]
    
    if not guardrail_tests:
        print("❌ No guardrail test cases found in dataset!")
        print("   Make sure eval_dataset.json has test cases with type='guardrail_test'")
        return
    
    print(f"✅ Found {len(guardrail_tests)} guardrail test cases")
    print()
    
    # Run tests
    print("🔄 Running guardrail tests...")
    print("   (This may take a few minutes...)")
    print()
    
    results = []
    for i, test_case in enumerate(guardrail_tests, 1):
        test_id = test_case["id"]
        query = test_case["query"]
        should_block = test_case.get("should_block", False)
        
        # Show progress
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(guardrail_tests)} tests completed...")
        
        try:
            # Run the actual travel agent (which includes guardrail)
            result = run_travel_agent(
                user_input=query,
                thread_id=None  # Fresh thread for each test
            )
            
            # Check if guardrail blocked it
            trajectory = result.get("trajectory", [])
            was_blocked = "guardrail_blocked_agent" in trajectory
            
            # Record result
            results.append({
                "id": test_id,
                "type": test_case["type"],
                "query": query,
                "should_block": should_block,
                "was_blocked": was_blocked,
                "trajectory": trajectory,
                "guardrail_allowed": result.get("guardrail_allowed", True),
                "notes": test_case.get("notes", "")
            })
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"\n⚠️  Error testing {test_id}: {e}")
            # Record failed test
            results.append({
                "id": test_id,
                "type": test_case["type"],
                "query": query,
                "should_block": should_block,
                "was_blocked": False,  # Assume not blocked if error
                "trajectory": [],
                "guardrail_allowed": True,
                "notes": test_case.get("notes", "") + f" (ERROR: {e})"
            })
    
    print(f"✅ Completed all {len(guardrail_tests)} tests!")
    print()
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(results)
    
    # Calculate metrics
    print("📊 Calculating metrics...")
    metrics = evaluate_guardrail_performance(results_df)
    failures = get_guardrail_failures(results_df)
    
    # Print detailed report
    print_guardrail_report(metrics, failures)
    
    # Save results for further analysis
    output_file = "guardrail_eval_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"💾 Results saved to: {output_file}")
    print()
    
    # Return metrics for programmatic access
    return metrics, failures, results_df


def run_guardrail_tests_summary_only():
    """
    Quick version that only shows summary metrics without detailed test execution.
    Useful for checking already-run results.
    """
    import os
    
    if not os.path.exists("guardrail_eval_results.csv"):
        print("❌ No previous results found. Run full evaluation first.")
        return
    
    print("\n" + "="*80)
    print("GUARDRAIL EVALUATION - SUMMARY (from previous run)")
    print("="*80 + "\n")
    
    # Load previous results
    results_df = pd.read_csv("guardrail_eval_results.csv")
    
    # Convert trajectory from string back to list
    results_df["trajectory"] = results_df["trajectory"].apply(
        lambda x: eval(x) if isinstance(x, str) else x
    )
    
    # Calculate metrics
    metrics = evaluate_guardrail_performance(results_df)
    failures = get_guardrail_failures(results_df)
    
    # Print report
    print_guardrail_report(metrics, failures)


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("PHASE 6: GUARDRAIL EVALUATION DEMO")
    print("="*80)
    print("\nThis will test your guardrail against 60+ test cases including:")
    print("  - ✅ Safe travel queries (should allow)")
    print("  - 🚨 Attack queries (should block)")
    print("  - 🔒 Jailbreak attempts (should block)")
    print("  - 📛 Off-topic queries (should block)")
    print("  - 🤔 Edge cases (tricky situations)")
    print()
    
    # Check if user wants quick summary or full run
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        run_guardrail_tests_summary_only()
    else:
        print("⏱️  This will take 5-10 minutes to run all tests.")
        print("   (Use --summary flag to view previous results quickly)")
        print()
        
        response = input("Continue with full evaluation? (y/n): ").lower().strip()
        
        if response == 'y':
            metrics, failures, results_df = run_guardrail_tests()
            
            # Offer to iterate
            print("\n" + "="*80)
            print("NEXT STEPS")
            print("="*80)
            print()
            
            if failures["false_negatives"]:
                print("🚨 PRIORITY: Fix security issues (false negatives)")
                print("   1. Review attacks that got through")
                print("   2. Update guardrail prompt in backend.py")
                print("   3. Re-run this evaluation")
            elif failures["false_positives"]:
                print("😊 IMPROVEMENT: Fix UX issues (false positives)")
                print("   1. Review safe queries that were blocked")
                print("   2. Update guardrail prompt to be less strict")
                print("   3. Re-run this evaluation")
            else:
                print("🎉 EXCELLENT! Your guardrail is performing well!")
                print("   Consider:")
                print("   - Testing with real user queries")
                print("   - Monitoring production traffic")
                print("   - Adding more edge cases")
            
            print()
        else:
            print("\n❌ Evaluation cancelled.")
            print("   Run with --summary to view previous results.")
