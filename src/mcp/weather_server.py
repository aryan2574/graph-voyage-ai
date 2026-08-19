import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, parent_dir)

from src.config import (
    OPENWEATHER_BASE_URL,
    OPENWEATHER_API_KEY,
)

import requests
from mcp.server import Server
from mcp.types import TextContent, Tool


# Initialize MCP server
server = Server("weather-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available weather tools"""
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "country_code": {"type": "string", "description": "ISO country code (optional)"},
                },
                "required": ["city"],
            },
        ),
        Tool(
            name="get_forecast",
            description="Get 5-day weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "country_code": {"type": "string", "description": "ISO country code (optional)"},
                },
                "required": ["city"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle weather tool calls"""
    
    if name == "get_current_weather":
        city = arguments.get("city")
        country_code = arguments.get("country_code", "")
        
        query = f"{city},{country_code}" if country_code else city
        
        try:
            response = requests.get(
                f"{OPENWEATHER_BASE_URL}/weather",
                params={
                    "q": query,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            result = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
            }
            
            return [TextContent(
                type="text",
                text=f"Current weather in {result['city']}, {result['country']}:\n"
                     f"Temperature: {result['temperature']}°C (feels like {result['feels_like']}°C)\n"
                     f"Conditions: {result['description']}\n"
                     f"Humidity: {result['humidity']}%\n"
                     f"Wind speed: {result['wind_speed']} m/s"
            )]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching weather: {str(e)}")]
    
    elif name == "get_forecast":
        city = arguments.get("city")
        country_code = arguments.get("country_code", "")
        
        query = f"{city},{country_code}" if country_code else city
        
        try:
            response = requests.get(
                f"{OPENWEATHER_BASE_URL}/forecast",
                params={
                    "q": query,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for item in data["list"][:8]:  # Next 24 hours (8 x 3-hour intervals)
                forecasts.append({
                    "time": item["dt_txt"],
                    "temp": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                })
            
            result_text = f"Weather forecast for {data['city']['name']}, {data['city']['country']}:\n\n"
            for forecast in forecasts:
                result_text += f"{forecast['time']}: {forecast['temp']}°C - {forecast['description']}\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching forecast: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(main())
