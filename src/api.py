from pathlib import Path
import traceback
import time
import asyncio
import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg
from dotenv import load_dotenv

from src.agents import run_travel_agent, resume_travel_agent

from src.monitoring import (
    log_request,
    evaluate_request_async,
    get_rolling_metrics,
    get_metrics_over_time
)

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

# This is kept from the original project to allow the existing synchronous
# agent functions to call async MCP helpers inside FastAPI.
import nest_asyncio

nest_asyncio.apply()

BASE_DIR = Path(__file__).resolve().parent


from src.config import get_database_url


def initialize_database():
    """
    Auto-initialize database on startup.
    Creates eval_logs table and indexes if they don't exist.
    """
    try:
        print("🔌 Initializing database...")
        conn = psycopg.connect(get_database_url())
        
        with conn.cursor() as cur:
            # Create eval_logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS eval_logs (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    thread_id TEXT,
                    query TEXT NOT NULL,
                    answer TEXT,
                    tools_used TEXT[],
                    trajectory TEXT[],
                    latency_seconds FLOAT,
                    guardrail_allowed BOOLEAN,
                    was_evaluated BOOLEAN DEFAULT FALSE,
                    
                    -- Evaluation results (NULL if not evaluated)
                    eval_passed BOOLEAN,
                    eval_completeness_score FLOAT,
                    eval_safety_passed BOOLEAN
                )
            """)
            
            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_eval_logs_created_at 
                ON eval_logs(created_at)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_eval_logs_was_evaluated 
                ON eval_logs(was_evaluated)
            """)
            
            conn.commit()
        
        conn.close()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("   Make sure DATABASE_URL is correct in .env")
        raise


# Initialize database on startup
initialize_database()

app = FastAPI(
    title="GraphVoyageAI",
    description=(
        "Multi-Agent AI Travel Planning System with LangGraph, Supervisor Pattern, "
        "Guardrails, Human-in-the-Loop, and Real-time Monitoring"
    ),
    version="2.0.0",
)

from src.config import CORS_ORIGINS

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend (production build)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist / "assets")),
        name="assets",
    )
    # Serve favicon and other static files from dist root
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_dist)),
        name="static",
    )


class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    approved: bool
    feedback: str = ""


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve React application"""
    frontend_dist = BASE_DIR / "frontend" / "dist"
    if frontend_dist.exists():
        frontend_index = frontend_dist / "index.html"
        with open(frontend_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # If React build doesn't exist, show error
    return HTMLResponse(
        content="<h1>Frontend not built</h1><p>Run 'cd frontend && npm run build' to build the React app.</p>",
        status_code=500
    )


@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    """
    Main travel planning endpoint with online monitoring.
    
    - Logs every request to database
    - Samples 10% for evaluation (async, doesn't slow response)
    - Tracks latency automatically
    """
    start_time = time.time()
    
    try:
        user_message = request_data.message.strip()

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty.",
                },
            )

        # Run travel agent
        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id,
        )
        
        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = latency
        
        try:
            # Log request (fast, synchronous)
            log_request(
                request_data={'message': user_message},
                result=result
            )
            
            # Evaluate in background (async, sampled)
            asyncio.create_task(
                evaluate_request_async(
                    request_data={'message': user_message},
                    result=result
                )
            )
        except Exception as mon_error:
            # Don't fail the request if monitoring fails
            print(f"⚠️  Monitoring error: {mon_error}")

        return JSONResponse(
            content={
                "success": True,
                **result,
            }
        )

    except Exception as exc:
        print("ERROR:", exc)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.post("/api/travel/approve")
async def approve_travel_plan(request_data: ApprovalRequest):
    try:
        if not request_data.approved and not request_data.feedback.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Please provide revision feedback when rejecting the draft.",
                },
            )

        result = resume_travel_agent(
            thread_id=request_data.thread_id,
            approved=request_data.approved,
            feedback=request_data.feedback,
        )

        return JSONResponse(
            content={
                "success": True,
                **result,
            }
        )

    except Exception as exc:
        print("APPROVAL ERROR:", exc)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "GraphVoyageAI API is running",
        "features": [
            "supervisor_agent",
            "input_guardrail",
            "human_in_the_loop",
            "online_monitoring",
        ],
    }


@app.get("/api/metrics")
async def get_metrics():
    """
    Get current system metrics from online monitoring.
    
    Phase 5: Returns rolling metrics over last 100 evaluated requests.
    
    Returns:
        - total_requests: Total requests logged
        - evaluated_count: How many were evaluated (10% sample)
        - pass_rate: Percentage passing all checks
        - safety_rate: Percentage passing safety checks
        - avg_latency: Average response time
        - p95_latency: 95th percentile latency
    """
    try:
        # Get rolling metrics (last 100 evaluated requests)
        rolling = get_rolling_metrics(window_size=100)
        
        # Get time-based metrics (last 24 hours)
        last_24h = get_metrics_over_time(hours=24)
        
        return JSONResponse(content={
            "success": True,
            "rolling_metrics": rolling,
            "last_24_hours": last_24h,
            "note": "Rolling metrics show last 100 evaluated requests. "
                   "Only 10% of requests are evaluated (sampling)."
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )