"""
Configuration and Constants for GraphVoyageAI

Centralized configuration management following industry best practices.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# EXTERNAL API ENDPOINTS
# ============================================

# AviationStack API
AVIATIONSTACK_BASE_URL = "https://api.aviationstack.com/v1/flights"
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")

# OpenWeather API
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Tavily MCP API
TAVILY_MCP_URL = "https://mcp.tavily.com/mcp/"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ============================================
# DATABASE CONFIGURATION
# ============================================

DATABASE_URL = os.getenv("DATABASE_URL", "")

def get_database_url() -> str:
    """Get PostgreSQL connection string with SSL"""
    database_url = DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env")
    
    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
    
    return database_url

# ============================================
# LLM CONFIGURATION
# ============================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "JFK")

# ============================================
# APPLICATION SETTINGS
# ============================================

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:3000",      # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:5173",
]

# API Timeouts (seconds)
API_TIMEOUT = 30
FLIGHT_API_TIMEOUT = 30
WEATHER_API_TIMEOUT = 10

# LLM Settings
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4096

# Context Management
MAX_CONVERSATION_MESSAGES = 5
TEXT_TRUNCATE_LENGTH = 500

# ============================================
# MONITORING & EVALUATION
# ============================================

# Evaluation Settings
EVAL_SAMPLE_RATE = float(os.getenv("EVAL_SAMPLE_RATE", "0.1"))
EVAL_ROLLING_WINDOW = int(os.getenv("EVAL_ROLLING_WINDOW", "100"))

# Alert Thresholds
ALERT_PASS_RATE_THRESHOLD = 0.75      # Alert if < 75%
ALERT_SAFETY_RATE_THRESHOLD = 0.95    # Alert if < 95%
ALERT_LATENCY_THRESHOLD = 25.0        # Alert if > 25 seconds

# Latency Thresholds
LATENCY_WARNING_THRESHOLD = 20.0      # Warning if > 20s
LATENCY_ERROR_THRESHOLD = 30.0        # Error if > 30s

# ============================================
# FEATURE FLAGS
# ============================================

# LangSmith Tracing
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "graph-voyage-ai")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"
