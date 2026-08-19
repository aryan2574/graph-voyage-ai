# ✈️ Graph Voyage AI — A Multi-Agent Travel Planner with LangGraph

An open-source AI travel planner that turns a natural-language trip request into a practical travel plan with flight suggestions, hotel ideas, and a day-by-day itinerary. The project uses a multi-agent workflow built with LangGraph, LangChain, and FastAPI.

## Why this project?

Planning a trip usually means jumping between multiple websites, tools, and spreadsheets. This project brings that flow into one experience by combining:

- a flight-search agent,
- a hotel-research agent,
- an itinerary-planning agent, and
- a final response agent,

all coordinated through a LangGraph workflow.

## Features

- ✈️ Flight research using AviationStack
- 🏨 Hotel suggestions using Tavily search
- 🧠 Multi-agent orchestration with LangGraph
- 📝 Structured travel itinerary generation
- ⚛️ Modern React + TypeScript frontend with Vite
- 📊 Real-time metrics dashboard with charts
- 🌐 FastAPI backend with RESTful API
- 💾 Conversation state persistence using PostgreSQL
- ⚡ LLM-powered responses with Groq
- 🐳 Docker & Kubernetes support
- 🔄 Complete CI/CD pipeline with GitHub Actions

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- LangGraph
- LangChain
- Groq LLMs
- PostgreSQL
- Tavily API
- AviationStack API

### Frontend
- React 19
- TypeScript
- Vite
- Recharts (for metrics visualization)
- Axios
- React Router

### DevOps
- Docker & Docker Compose
- Kubernetes
- GitHub Actions (CI/CD)
- Render (deployment)

## Project Structure

```text
GraphVoyageAI/
├── src/                    # Application source code
│   ├── api.py             # FastAPI application
│   ├── agents.py          # LangGraph multi-agent system
│   ├── monitoring.py      # Real-time monitoring
│   ├── mcp/               # MCP integration
│   └── tools/             # Agent tools
├── tests/                 # Testing & evaluation
│   ├── evals/            # Evaluation system
│   └── fixtures/         # Test data
├── frontend/              # React + TypeScript UI
├── k8s/                   # Kubernetes configs
├── .github/workflows/     # CI/CD
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker config
└── docker-compose.yml    # Local dev setup
```

## Prerequisites

Before running the project locally, make sure you have:

- Python 3.10 or newer installed
- PostgreSQL running and accessible
- API keys for:
  - Groq
  - Tavily
  - AviationStack

## Getting Started

### 1. Install Dependencies

```bash
# Clone repository
git clone <repository-url>
cd GraphVoyageAI

# Install Python packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and DATABASE_URL
```

### 3. Run Application

**Development Mode:**
```bash
# Start backend (auto-initializes database)
uvicorn src.api:app --reload --host 127.0.0.1 --port 8000

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

**Using Docker:**
```bash
docker-compose up
```

Visit:
- Frontend: `http://localhost:5173` (dev) or `http://localhost:8000` (production)
- API Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:5173/dashboard`

## Environment Variables

Create a .env file in the project root with the following variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/travel_db
GROQ_API_KEY=your_groq_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
TAVILY_API_KEY=your_tavily_api_key
DEFAULT_ORIGIN_IATA=DAC
```

## Development with Conda (Windows)

```bash
source /c/Users/HP/miniconda3/etc/profile.d/conda.sh
conda activate travel
uvicorn src.api:app --reload
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## API Endpoints

- `GET /` - Serve React frontend (production) or home page
- `GET /health` - Health check
- `GET /api/metrics` - Get system metrics
- `POST /api/travel` - Submit a travel request
- `POST /api/travel/approve` - Approve/reject travel plan

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo with a budget of $1200"}'
```

## How the Workflow Works

1. The user submits a travel request.
2. The flight agent gathers flight-related information.
3. The hotel agent searches for accommodation suggestions.
4. The itinerary agent creates a practical travel plan.
5. The final agent formats the result into a polished response.

## Contributing

Contributions are welcome. If you want to improve the app, add new travel features, or fix issues:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Open a pull request

## Acknowledgments

This project is built with the help of modern LLM tooling and travel APIs, and it is intended as a practical example of combining LangGraph agents with real-world applications.
