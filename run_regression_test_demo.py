"""
This demonstrates how to use the regression testing system to detect
when code changes degrade performance.

Workflow:
1. Capture baseline (current performance)
2. Make code changes
3. Run regression test to compare
4. Get report showing what improved/degraded

Usage:
    python run_regression_test_demo.py
"""

from evals import (
    capture_baseline,
    run_offline_eval,
    detect_regression,
    print_regression_report
)

def demo_regression_testing():
    print("\n🎯 PHASE 4: REGRESSION TESTING DEMO")
    print("="*80)
    print("This demo shows how regression testing catches performance degradation\n")
    
    # STEP 1: Capture baseline (simulating "before changes")
    print("STEP 1: Capturing baseline (current system performance)...")
    print("-"*80)
    baseline_metrics = capture_baseline(
        dataset_path="eval_dataset.json",
        baseline_file="baseline_eval_results.csv",
        use_simulation=True
    )
    
    input("\n✅ Baseline captured! Press Enter to simulate code changes and re-test...")
    
    # STEP 2: Simulate making code changes
    print("\n" + "="*80)
    print("STEP 2: Simulating code changes...")
    print("-"*80)
    print("  (Imagine you just updated the supervisor agent prompt)")
    print("  (Or added a new tool, or modified routing logic...)")
    print()
    
    input("✅ Code changes made! Press Enter to run regression test...")
    
    # STEP 3: Run current evaluation (simulating "after changes")
    print("\n" + "="*80)
    print("STEP 3: Running current evaluation...")
    print("-"*80)
    current_df = run_offline_eval(
        dataset_path="eval_dataset.json",
        use_simulation=True
    )
    
    # STEP 4: Detect regressions
    print("="*80)
    print("STEP 4: Comparing current vs baseline...")
    print("-"*80)
    regression_report = detect_regression(
        current_results=current_df,
        baseline_path="baseline_eval_results.csv",
        threshold=0.05  # 5% tolerance
    )
    
    # STEP 5: Print regression report
    print_regression_report(regression_report)
    
    # Summary
    print("="*80)
    print("🎓 WHAT YOU LEARNED")
    print("="*80)
    print("\n1. ✅ capture_baseline() - Saves current performance as reference")
    print("2. ✅ detect_regression() - Compares new results vs baseline")
    print("3. ✅ print_regression_report() - Beautiful summary of changes")
    print("\n4. In real usage:")
    print("   - Capture baseline BEFORE making changes")
    print("   - After changes, run regression test")
    print("   - If regressions found → fix or revert")
    print("   - If no regressions → update baseline\n")
    
    print("="*80)
    print("📝 NEXT STEPS")
    print("="*80)
    print("\n1. Try with real agent:")
    print("   - Modify this script to use run_agent_fn=run_travel_agent")
    print("   - Set use_simulation=False")
    print("\n2. Integrate into your workflow:")
    print("   - Capture baseline before major refactoring")
    print("   - Run regression tests after each change")
    print("   - Add to CI/CD pipeline to block bad deployments")
    print("\n3. The baseline files:")
    print("   - baseline_eval_results.csv - Test-by-test results")
    print("   - baseline_eval_metrics.json - Aggregate metrics")
    print("   - Commit these when you want to preserve a known-good state\n")


if __name__ == "__main__":
    demo_regression_testing()
