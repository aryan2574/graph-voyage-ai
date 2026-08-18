"""
Database Schema for Online Evaluation Monitoring

This creates a table to store evaluation logs from production traffic.
Run this once to set up the table in your Render PostgreSQL database.

Usage:
    python create_eval_logs_table.py
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env")
    
    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    return database_url


def create_eval_logs_table():
    """
    Create table to store online evaluation logs.
    
    This table tracks:
    - Every request to your travel agent
    - Evaluation results (for sampled requests)
    - Performance metrics
    - Safety checks
    """
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS eval_logs (
        -- Primary key
        id SERIAL PRIMARY KEY,
        
        -- Request metadata
        timestamp TIMESTAMP DEFAULT NOW(),
        thread_id VARCHAR(255),
        
        -- Request data
        query TEXT NOT NULL,
        answer TEXT,
        
        -- Agent execution data
        tools_used TEXT[],
        trajectory TEXT[],
        latency_seconds FLOAT,
        
        -- Evaluation results (NULL if not evaluated)
        was_evaluated BOOLEAN DEFAULT FALSE,
        passed BOOLEAN,
        correctness_score FLOAT,
        safety_passed BOOLEAN,
        guardrail_allowed BOOLEAN,
        
        -- Indexes for faster queries
        CONSTRAINT eval_logs_thread_id_idx 
            CHECK (thread_id IS NOT NULL)
    );
    
    -- Create indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_eval_logs_timestamp 
        ON eval_logs(timestamp DESC);
    
    CREATE INDEX IF NOT EXISTS idx_eval_logs_was_evaluated 
        ON eval_logs(was_evaluated) 
        WHERE was_evaluated = TRUE;
    
    CREATE INDEX IF NOT EXISTS idx_eval_logs_passed 
        ON eval_logs(passed) 
        WHERE passed IS NOT NULL;
    """
    
    print("🔧 Creating eval_logs table...")
    print("="*80)
    
    try:
        # Connect to database
        database_url = get_database_url()
        conn = psycopg.connect(database_url)
        
        # Create table
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
            conn.commit()
        
        print("✅ Table 'eval_logs' created successfully!")
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - timestamp: When request was made")
        print("  - thread_id: LangGraph thread ID")
        print("  - query: User's travel query")
        print("  - answer: Agent's response")
        print("  - tools_used: Which tools were called")
        print("  - trajectory: Agent execution path")
        print("  - latency_seconds: Response time")
        print("  - was_evaluated: Whether this request was evaluated")
        print("  - passed: Overall evaluation result")
        print("  - correctness_score: Answer quality score")
        print("  - safety_passed: Safety check result")
        print("  - guardrail_allowed: Guardrail decision")
        print("\n✅ Indexes created for fast queries")
        print("="*80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PHASE 5: ONLINE MONITORING - Database Setup")
    print("="*80 + "\n")
    
    create_eval_logs_table()
    
    print("\n✅ Database setup complete!")
    print("\nNext steps:")
    print("1. Deploy your app to Render")
    print("2. Online monitoring will start automatically")
    print("3. View metrics at /api/metrics endpoint\n")
