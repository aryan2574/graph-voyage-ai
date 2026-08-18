from pathlib import Path
import traceback
import time
import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend import run_travel_agent, resume_travel_agent

from online_monitoring import (
    log_request,
    evaluate_request_async,
    get_rolling_metrics,
    get_metrics_over_time
)

# This is kept from the original project to allow the existing synchronous
# agent functions to call async MCP helpers inside FastAPI.
import nest_asyncio

nest_asyncio.apply()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="TripMate AI",
    description=(
        "LangGraph Multi-Agent Travel Planner with Supervisor, Guardrails, "
        "Human-in-the-Loop, and FastAPI Frontend"
    ),
    version="2.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    approved: bool
    feedback: str = ""


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
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
        "message": "TripMate AI API is running",
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