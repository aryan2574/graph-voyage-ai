# GraphVoyageAI

A production-ready multi-agent travel planning system built with LangGraph. Transforms natural language queries into comprehensive travel itineraries using orchestrated specialist agents, human-in-the-loop approval, and real-time monitoring.

## Architecture

**Supervisor Pattern with Dynamic Routing**

- Supervisor agent analyzes queries and routes to specialized workers
- Pre-execution guardrails validate and filter requests
- State persistence via PostgreSQL with LangGraph checkpointing

**Guardrail System**

- Request validation before agent execution
- Safety checks for out-of-scope queries
- Automatic rejection of non-travel requests
- Reasoning explanation for blocked requests

**Specialized Agent System**

- **Flight Agent** - Real-time flight search (AviationStack API)
- **Hotel Agent** - Accommodation research (Tavily MCP)
- **Weather Agent** - Forecast data (OpenWeather MCP)
- **Budget Agent** - Cost analysis and optimization
- **Itinerary Agent** - Day-by-day planning with constraints
- **Final Agent** - Structured output formatting

**Human-in-the-Loop (HITL)**

- LangGraph interrupts for approval workflow
- Draft review before final itinerary generation
- Feedback incorporation and revision handling
- Thread resumption with stateful context

**Production Monitoring & Evaluation**

- LLM-as-Judge evaluation system
- Async evaluation with configurable sampling (default 10%)
- Completeness scoring (0-10 scale)
- Safety checks (API key leakage prevention, forbidden patterns)
- Rolling metrics over last N requests
- Real-time dashboard with Recharts visualization
- Automated alerting on metric degradation

## Tech Stack

**Backend:** Python 3.11+, FastAPI, LangGraph, LangChain, PostgreSQL  
**Frontend:** React 19, TypeScript, Vite  
**LLM:** Groq (Llama models)  
**MCP:** Tavily Search, OpenWeather  
**Infrastructure:** Docker, Kubernetes, GitHub Actions

## Key Features

- **Supervisor-Based Orchestration** - Dynamic agent routing with execution planning
- **Pre-Execution Guardrails** - Request validation, scope checking, safety filtering
- **LLM-as-Judge Evaluations** - Automated completeness and safety scoring
- **Persistent State** - PostgreSQL-backed LangGraph checkpointing
- **Human-in-the-Loop** - Interrupt-driven approval workflow with feedback
- **MCP Integration** - Tavily search and OpenWeather via Model Context Protocol
- **Production Monitoring** - Async evaluation (10% sampling), rolling metrics, alerting
- **Auto-Initialization** - Database schema and eval_logs table setup on startup
- **RESTful API** - FastAPI with OpenAPI documentation
- **Metrics Dashboard** - Real-time visualization of system performance
- **Kubernetes-Ready** - LoadBalancer services, HPA, PDB configurations

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 16+
- API Keys: Groq, Tavily, AviationStack, OpenWeather

### Installation

```bash
git clone https://github.com/aryan2574/graph-voyage-ai.git
cd graph-voyage-ai
pip install -r requirements.txt
```

### Environment Configuration

Create `.env` in project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/travel_db

# LLM
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b

# APIs
AVIATIONSTACK_API_KEY=...
TAVILY_API_KEY=tvly-...
OPENWEATHER_API_KEY=...

# Configuration
DEFAULT_ORIGIN_IATA=DAC
EVAL_SAMPLE_RATE=0.1
EVAL_ROLLING_WINDOW=100
```

### Local Development

```bash
# Backend (auto-initializes DB schema)
uvicorn src.api:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

**Access:**

- App: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:5173/dashboard

### Docker Deployment

```bash
docker-compose up --build
```

Includes PostgreSQL, FastAPI backend, and serves built frontend.

### Kubernetes Deployment

```bash
# Create secret from template
cp k8s/01-secret.yaml.template k8s/01-secret.yaml
# Edit k8s/01-secret.yaml with real API keys

# Deploy all resources
kubectl apply -f k8s/

# Verify
kubectl get pods -n graphvoyage -w
```

**K8s Resources:**

- Namespace isolation (`graphvoyage`)
- ConfigMap for non-sensitive config
- Secret for API keys (base64-encoded)
- PersistentVolumeClaim (5Gi for PostgreSQL)
- Deployments: PostgreSQL (1 replica), App (2 replicas), Adminer (1 replica)
- Services: LoadBalancer for external access
- HorizontalPodAutoscaler (CPU-based scaling)
- PodDisruptionBudget (high availability)

**Access (LoadBalancer):**

- App: http://localhost:8000
- Adminer: http://localhost:8080

See `k8s/README.md` for advanced configurations.

## API Usage

### Initial Request (Returns Draft)

```bash
curl -X POST http://localhost:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Plan a 3-day trip to Tokyo from New York with $1500 budget"
  }'
```

**Response:**

```json
{
  "answer": "Draft itinerary...",
  "thread_id": "uuid-thread-id",
  "requires_approval": true,
  "draft_itinerary": "...",
  "tools_used": ["flight_agent", "hotel_agent", "weather_agent", "budget_agent"],
  "trajectory": ["supervisor_agent", "flight_agent", ...],
  "latency_seconds": 12.5
}
```

### Approval/Revision

```bash
curl -X POST http://localhost:8000/api/travel/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "uuid-thread-id",
    "approved": true,
    "feedback": ""
  }'
```

Set `approved: false` and provide `feedback` to request revisions.

### Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics
```

Returns rolling window metrics and evaluation statistics.

## System Workflow

1. **Request Ingress** → Logged to `eval_logs` table with metadata
2. **Guardrail Check** → Validates scope (travel-related?), safety checks
   - If blocked: Returns rejection reason, workflow ends
   - If passed: Proceeds to supervisor
3. **Supervisor Agent** → Analyzes query, extracts constraints, selects agents
4. **Specialist Agents** → Execute in parallel/sequence based on dependencies
5. **Itinerary Agent** → Synthesizes results into structured plan
6. **HITL Interrupt** → Thread pauses, returns draft for approval
7. **User Review** → Approves or requests changes via `/approve` endpoint
8. **Final Agent** → Generates polished output incorporating feedback
9. **Async Evaluation** → Background task (10% sampled):
   - Completeness score (0-10)
   - Safety check (forbidden patterns, API key leakage)
   - Updates `eval_logs` table with results
10. **Metrics Update** → Rolling window calculations, alerting if degraded

## Evaluation System

**LLM-as-Judge Architecture:**
- Separate evaluator LLM (Groq gpt-oss-20b)
- Completeness scoring: Checks if answer addresses all query aspects
- Safety validation: Scans for API keys, credentials, forbidden patterns
- Trajectory analysis: Validates tool usage and agent execution order

**Evaluation Criteria:**
```python
# Completeness (0-10 scale)
- Does answer provide flight options?
- Are hotel suggestions included?
- Is weather information present?
- Is budget analysis provided?
- Is day-by-day itinerary complete?

# Safety (Pass/Fail)
- No API keys leaked
- No database credentials exposed
- No forbidden patterns present
- Appropriate content only
```

**Sampling & Performance:**
- Default: 10% of requests evaluated (configurable via `EVAL_SAMPLE_RATE`)
- Async execution doesn't block user response
- Results stored in `eval_logs` table for analysis
- Rolling window metrics (default: last 100 requests)

**Metrics Tracked:**
- Pass rate (% of requests meeting completeness threshold)
- Average completeness score
- Safety violation rate
- Average latency
- Tool usage frequency
- Guardrail block rate

## Project Structure

```
GraphVoyageAI/
├── src/
│   ├── api.py              # FastAPI app, CORS, endpoints
│   ├── agents.py           # LangGraph: supervisor, specialists, HITL
│   ├── monitoring.py       # Async eval, metrics, alerting
│   ├── config.py           # Environment variables, constants
│   ├── constants.py        # Domain constants (airports, countries)
│   ├── tools/
│   │   ├── flight_tool.py  # AviationStack integration
│   │   └── tavily_tool.py  # Tavily search wrapper
│   └── mcp/
│       ├── client.py       # MCP client setup
│       └── __init__.py     # Tavily/Weather MCP helpers
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TravelPlanner.tsx  # Main chat interface
│   │   │   └── Dashboard.tsx      # Metrics visualization
│   │   └── components/     # Reusable UI components
│   └── package.json
├── tests/
│   └── evals/
│       └── evaluators.py   # LLM-as-judge evaluation logic
├── k8s/                    # Numbered manifest files (00-11)
├── Dockerfile              # Multi-stage: development, production
├── docker-compose.yml      # PostgreSQL + app + frontend
└── requirements.txt        # Python dependencies
```
