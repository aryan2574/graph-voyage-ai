"""
MCP (Model Context Protocol) Integration

This package contains MCP client and server implementations.
"""

from .client import (
    tavily_mcp_search,
    extract_destination,
    forecast_mcp_search,
    weather_mcp_search,
)

__all__ = [
    "tavily_mcp_search",
    "extract_destination",
    "forecast_mcp_search",
    "weather_mcp_search",
]
