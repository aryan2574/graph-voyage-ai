"""
PHASE 3: Offline Batch Evaluation Demo
=======================================

This script demonstrates the batch evaluation pipeline.
It shows you how to:
1. Run all tests at once
2. Get aggregate metrics
3. Analyze results by test type
4. Export results for later analysis

Usage:
    python run_offline_evals_demo.py
"""

from evals import (
    run_offline_eval,
    compute_aggregate_metrics,
    compute_per_test_type_metrics,
    print_eval_summary
)

def main():
    print("\n🎯 WELCOME TO BATCH EVALUATION SYSTEM")
    print("="*80)
    print("This will run ALL 12 tests automatically and give you a complete report!\n")
    
    # STEP 1: Run batch evaluation (simulated mode for now)
    print("Step 1: Running batch evaluation...\n")
    results_df = run_offline_eval(
        dataset_path="eval_dataset.json",
        use_simulation=True  # Set to False to use real agent
    )
    
    # STEP 2: Print beautiful summary
    print_eval_summary(results_df)
    
    # STEP 3: Show you how to access the data programmatically
    print("="*80)
    print("📊 ACCESSING DATA PROGRAMMATICALLY")
    print("="*80)
    print("\n1. Get aggregate metrics as dictionary:")
    metrics = compute_aggregate_metrics(results_df)
    print(f"   Pass Rate: {metrics['pass_rate']:.1f}%")
    print(f"   Avg Latency: {metrics['avg_latency_seconds']:.2f}s")
    print(f"   P95 Latency: {metrics['p95_latency_seconds']:.2f}s")
    
    print("\n2. Get metrics by test type:")
    by_type = compute_per_test_type_metrics(results_df)
    print(by_type)
    
    print("\n3. Query specific tests:")
    failed = results_df[results_df['passed'] == False]
    print(f"   Failed Tests: {len(failed)}")
    if len(failed) > 0:
        print(f"   Failed IDs: {failed['test_id'].tolist()}")
    
    print("\n4. Filter by test type:")
    safety_tests = results_df[results_df['test_type'] == 'safety']
    print(f"   Safety Tests Pass Rate: {safety_tests['passed'].mean() * 100:.1f}%")
    
    # STEP 4: Save results (optional)
    print("\n" + "="*80)
    print("💾 SAVING RESULTS")
    print("="*80)
    
    # Save full results to CSV
    output_file = "eval_results_latest.csv"
    results_df.to_csv(output_file, index=False)
    print(f"✓ Saved detailed results to: {output_file}")
    
    # Save metrics summary to JSON
    import json
    metrics_file = "eval_metrics_latest.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Saved aggregate metrics to: {metrics_file}")
    
    print("\n" + "="*80)
    print("🎉 BATCH EVALUATION COMPLETE!")
    print("="*80)
    print("\nWhat you can do next:")
    print("1. Review the eval_results_latest.csv file for detailed test-by-test results")
    print("2. Check eval_metrics_latest.json for quick metrics overview")
    print("3. Switch to real agent by editing this file:")
    print("   - Uncomment: from backend import run_travel_agent")
    print("   - Change: use_simulation=False")
    print("   - Pass: run_agent_fn=run_travel_agent")
    print("4. Run this anytime you make changes to catch regressions!")
    print()


if __name__ == "__main__":
    main()
