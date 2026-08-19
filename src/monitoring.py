"""
Online Monitoring System for Production Traffic

This module provides real-time evaluation of production requests without
slowing down user responses.

Key Features:
1. Request Logging - Log every request to database
2. Sampling - Only evaluate 10% (configurable)
3. Async Evaluation - Doesn't block user response
4. Rolling Metrics - Track trends over last N requests
5. Simple Alerting - Log warnings when metrics degrade

Usage in app.py:
    from online_monitoring import log_request, evaluate_request_async, get_rolling_metrics
    
    @app.post("/api/travel")
    async def travel_planner(request_data):
        result = run_travel_agent(...)
        
        # Log request (always, fast)
        log_request(request_data, result)
        
        # Evaluate in background (sampled, async)
        asyncio.create_task(evaluate_request_async(request_data, result))
        
        return result
"""

import os
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

from src.config import (
    ALERT_PASS_RATE_THRESHOLD,
    ALERT_SAFETY_RATE_THRESHOLD,
    ALERT_LATENCY_THRESHOLD,
    EVAL_SAMPLE_RATE,
    EVAL_ROLLING_WINDOW,
    get_database_url,
)


def should_evaluate() -> bool:
    """
    Determine if this request should be evaluated (sampling).
    
    Returns True 10% of the time (configurable via EVAL_SAMPLE_RATE).
    This prevents evaluating every request which would be expensive.
    """
    return random.random() < EVAL_SAMPLE_RATE


def log_request(request_data: Dict[str, Any], result: Dict[str, Any]):
    """
    Log request to database (synchronous, fast).
    
    This logs EVERY request for tracking purposes.
    Evaluation happens separately for only sampled requests.
    
    Args:
        request_data: Original user request
        result: Agent's response with metadata
    """
    try:
        conn = psycopg.connect(get_database_url())
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eval_logs (
                    thread_id,
                    query,
                    answer,
                    tools_used,
                    trajectory,
                    latency_seconds,
                    guardrail_allowed,
                    was_evaluated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                result.get('thread_id'),
                request_data.get('message'),
                result.get('answer', ''),
                result.get('tools_used', []),
                result.get('trajectory', []),
                result.get('latency_seconds', 0.0),
                result.get('guardrail_allowed', True),
                False
            ))
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"⚠️  Logging error: {e}")


async def evaluate_request_async(request_data: Dict[str, Any], result: Dict[str, Any]):
    """
    Evaluate request in background (async, doesn't block user).
    
    This runs AFTER the user has received their response.
    Only runs for sampled requests (10%).
    
    Args:
        request_data: Original user request
        result: Agent's response with metadata
    """
    # Check if we should evaluate this request
    if not should_evaluate():
        return
    
    try:
        # Import evaluation functions (lazy import to avoid circular deps)
        from tests.evals.evaluators import (
            evaluate_answer,
            evaluate_safety_and_reliability,
            evaluate_latency
        )
        
        # Run evaluations
        test_case = {
            'type': 'normal',  # Assume normal request (could be smarter)
            'query': request_data.get('message'),
        }
        
        # Safety check
        safety_passed = evaluate_safety_and_reliability(test_case, result)
        
        # Latency check (against 20s threshold)
        latency_ok = evaluate_latency(
            result.get('latency_seconds', 0),
            20.0  # 20 second threshold
        )
        
        # Overall pass (simple: safety + latency)
        passed = safety_passed and latency_ok
        
        # Correctness score (simple heuristic based on response length)
        answer_length = len(result.get('answer', ''))
        completeness_score = min(answer_length / 500, 1.0)  # Rough estimate
        
        # Update database with evaluation results
        conn = psycopg.connect(get_database_url())
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE eval_logs
                SET was_evaluated = TRUE,
                    eval_passed = %s,
                    eval_completeness_score = %s,
                    eval_safety_passed = %s
                WHERE thread_id = %s
                  AND was_evaluated = FALSE
                ORDER BY created_at DESC
                LIMIT 1
            """, (
                passed,
                completeness_score,
                safety_passed,
                result.get('thread_id')
            ))
            conn.commit()
        
        conn.close()
        
        # Check if we should alert (every 10 evaluations)
        if random.random() < 0.1:  # 10% chance after evaluation
            asyncio.create_task(check_and_alert())
        
    except Exception as e:
        print(f"⚠️  Evaluation error: {e}")


async def check_and_alert():
    """
    Check rolling metrics and alert if degraded.
    
    This runs occasionally (not every request) to avoid spamming.
    Calculates metrics over last N evaluated requests and logs warnings.
    """
    try:
        metrics = get_rolling_metrics(window_size=ROLLING_WINDOW_SIZE)
        
        if metrics['evaluated_count'] < 20:
            # Not enough data yet
            return
        
        # Check thresholds and alert
        if metrics['pass_rate'] < ALERT_PASS_RATE_THRESHOLD:
            print(f"🚨 ALERT: Pass rate dropped to {metrics['pass_rate']*100:.1f}%")
        
        if metrics['safety_rate'] < ALERT_SAFETY_RATE_THRESHOLD:
            print(f"🚨 ALERT: Safety rate dropped to {metrics['safety_rate']*100:.1f}%")
        
        if metrics['avg_latency'] > ALERT_LATENCY_THRESHOLD:
            print(f"🚨 ALERT: Latency increased to {metrics['avg_latency']:.1f}s")
    
    except Exception as e:
        print(f"⚠️  Alert check error: {e}")


def get_rolling_metrics(window_size: int = 100) -> Dict[str, Any]:
    """
    Calculate metrics over last N evaluated requests.
    
    This gives you a "rolling window" view of performance.
    More stable than single-request metrics.
    
    Args:
        window_size: Number of recent requests to analyze
    
    Returns:
        Dictionary with rolling metrics:
        - total_requests: Total logged requests
        - evaluated_count: How many were evaluated
        - pass_rate: Percentage that passed
        - safety_rate: Percentage that passed safety
        - avg_latency: Average response time
        - p95_latency: 95th percentile latency
    """
    try:
        conn = psycopg.connect(get_database_url(), row_factory=dict_row)
        
        # Get total request count
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM eval_logs")
            total_requests = cur.fetchone()['count']
        
        # Get last N evaluated requests
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    eval_passed,
                    eval_safety_passed,
                    latency_seconds,
                    created_at
                FROM eval_logs
                WHERE was_evaluated = TRUE
                ORDER BY created_at DESC
                LIMIT %s
            """, (window_size,))
            
            recent_evals = cur.fetchall()
        
        conn.close()
        
        if not recent_evals:
            return {
                'total_requests': total_requests,
                'evaluated_count': 0,
                'pass_rate': 0.0,
                'safety_rate': 0.0,
                'avg_latency': 0.0,
                'p95_latency': 0.0,
            }
        
        # Calculate metrics
        evaluated_count = len(recent_evals)
        pass_count = sum(1 for r in recent_evals if r['eval_passed'])
        safety_count = sum(1 for r in recent_evals if r['eval_safety_passed'])
        latencies = [r['latency_seconds'] for r in recent_evals if r['latency_seconds']]
        
        return {
            'total_requests': total_requests,
            'evaluated_count': evaluated_count,
            'sample_rate': EVAL_SAMPLE_RATE * 100,  # As percentage
            'pass_rate': pass_count / evaluated_count if evaluated_count > 0 else 0.0,
            'safety_rate': safety_count / evaluated_count if evaluated_count > 0 else 0.0,
            'avg_latency': sum(latencies) / len(latencies) if latencies else 0.0,
            'p95_latency': sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0,
            'window_size': window_size,
        }
    
    except Exception as e:
        print(f"⚠️  Metrics error: {e}")
        return {
            'error': str(e),
            'total_requests': 0,
            'evaluated_count': 0,
        }


def get_metrics_over_time(hours: int = 24) -> Dict[str, Any]:
    """
    Get metrics for the last N hours, broken down by hour.
    
    Returns hourly breakdown for charts.
    
    Args:
        hours: How many hours to look back
    
    Returns:
        Metrics aggregated by hour with labels, counts, and rates
    """
    try:
        conn = psycopg.connect(get_database_url(), row_factory=dict_row)
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with conn.cursor() as cur:
            # Get hourly breakdown
            cur.execute("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as request_count,
                    COUNT(CASE WHEN was_evaluated THEN 1 END) as evaluated_count,
                    AVG(CASE WHEN was_evaluated AND eval_passed THEN 1.0 ELSE 0.0 END) as pass_rate
                FROM eval_logs
                WHERE created_at >= %s
                GROUP BY hour
                ORDER BY hour ASC
            """, (cutoff_time,))
            
            hourly_data = cur.fetchall()
        
        conn.close()
        
        # Format for charts
        if not hourly_data:
            # Return empty data structure
            return {
                'labels': [],
                'hourly_counts': [],
                'hourly_pass_rates': [],
            }
        
        labels = [row['hour'].strftime('%H:%M') if row['hour'] else '' for row in hourly_data]
        hourly_counts = [row['request_count'] or 0 for row in hourly_data]
        hourly_pass_rates = [float(row['pass_rate'] or 0) for row in hourly_data]
        
        return {
            'labels': labels,
            'hourly_counts': hourly_counts,
            'hourly_pass_rates': hourly_pass_rates,
        }
    
    except Exception as e:
        print(f"⚠️  Time metrics error: {e}")
        return {
            'labels': [],
            'hourly_counts': [],
            'hourly_pass_rates': [],
            'error': str(e)
        }


# For testing
if __name__ == "__main__":
    print("Online Monitoring Module")
    print("Sample Rate:", SAMPLE_RATE * 100, "%")
    print("Rolling Window:", ROLLING_WINDOW_SIZE, "requests")
    
    # Test metrics
    metrics = get_rolling_metrics()
    print("\nCurrent Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
