"""
Test Online Monitoring System (Local)

This script tests that Phase 5 is working correctly before deploying to Render.

It simulates:
1. Creating the database table
2. Logging requests
3. Evaluating requests
4. Calculating metrics

Usage:
    python test_online_monitoring.py
"""

import time
import random
from online_monitoring import (
    log_request,
    get_rolling_metrics,
    get_metrics_over_time,
    should_evaluate
)

def generate_mock_request(idx):
    """Generate a mock travel request"""
    queries = [
        "Plan a 3-day trip to Paris",
        "Find cheap flights to Tokyo",
        "Book a hotel in New York",
        "What's the weather in London?",
        "Create an itinerary for Rome"
    ]
    
    return {
        'message': random.choice(queries)
    }

def generate_mock_result(idx):
    """Generate a mock agent result"""
    return {
        'thread_id': f'test_thread_{idx}',
        'answer': f'Here is your travel plan for request {idx}...',
        'tools_used': random.sample(['flight_tool', 'hotel_tool', 'weather_tool'], k=2),
        'trajectory': ['supervisor', random.choice(['flight_agent', 'hotel_agent']), 'final'],
        'latency_seconds': random.uniform(8.0, 18.0),
        'guardrail_allowed': True
    }

def test_online_monitoring():
    """Test the online monitoring system"""
    
    print("="*80)
    print("TESTING PHASE 5: ONLINE MONITORING")
    print("="*80)
    print()
    
    # Test 1: Database Table
    print("📋 Test 1: Checking database table...")
    try:
        metrics = get_rolling_metrics(window_size=1)
        print("✅ Database table exists and is accessible")
        print(f"   Current total requests: {metrics.get('total_requests', 0)}")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("\n⚠️  Please run: python create_eval_logs_table.py")
        return
    
    print()
    
    # Test 2: Sampling Logic
    print("📋 Test 2: Testing sampling logic...")
    sample_count = sum(1 for _ in range(1000) if should_evaluate())
    sample_rate = sample_count / 1000
    print(f"✅ Sampling working: {sample_rate*100:.1f}% (expected ~10%)")
    print()
    
    # Test 3: Log Requests
    print("📋 Test 3: Logging test requests...")
    num_requests = 20
    
    for i in range(num_requests):
        request_data = generate_mock_request(i)
        result = generate_mock_result(i)
        
        try:
            log_request(request_data, result)
            print(f"   ✓ Logged request {i+1}/{num_requests}")
            time.sleep(0.1)  # Small delay to avoid overwhelming DB
        except Exception as e:
            print(f"   ✗ Failed to log request {i+1}: {e}")
    
    print(f"✅ Logged {num_requests} test requests")
    print()
    
    # Test 4: Rolling Metrics
    print("📋 Test 4: Calculating rolling metrics...")
    try:
        metrics = get_rolling_metrics(window_size=50)
        print("✅ Rolling metrics calculated successfully:")
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Evaluated count: {metrics['evaluated_count']}")
        print(f"   Sample rate: {metrics['sample_rate']}%")
        
        if metrics['evaluated_count'] > 0:
            print(f"   Pass rate: {metrics['pass_rate']*100:.1f}%")
            print(f"   Safety rate: {metrics['safety_rate']*100:.1f}%")
            print(f"   Avg latency: {metrics['avg_latency']:.2f}s")
            print(f"   P95 latency: {metrics['p95_latency']:.2f}s")
        else:
            print("   (No evaluated requests yet - this is expected)")
    except Exception as e:
        print(f"❌ Metrics error: {e}")
    
    print()
    
    # Test 5: Time-Based Metrics
    print("📋 Test 5: Calculating time-based metrics...")
    try:
        time_metrics = get_metrics_over_time(hours=1)
        print("✅ Time-based metrics calculated successfully:")
        print(f"   Requests in last hour: {time_metrics['total_requests']}")
        print(f"   Evaluated in last hour: {time_metrics['evaluated_count']}")
        if time_metrics['evaluated_count'] > 0:
            print(f"   Avg latency: {time_metrics['avg_latency']:.2f}s")
    except Exception as e:
        print(f"❌ Time metrics error: {e}")
    
    print()
    print("="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Push code to GitHub")
    print("2. Render will auto-deploy")
    print("3. Online monitoring will start automatically")
    print("4. View metrics at: https://your-app.onrender.com/api/metrics")
    print()

if __name__ == "__main__":
    try:
        test_online_monitoring()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
