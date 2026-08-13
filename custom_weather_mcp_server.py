from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Weather MCP Server")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL="https://api.openweathermap.org/data/2.5"

# Use decorator to make it mcp tool
@mcp.tool()
def get_current_weather(city:str):
    
    url = f"{BASE_URL}/weather"
    response = requests.get(
        url,
        params={
            "q": city,
            "appid":OPENWEATHER_API_KEY,
            "units":"metric"
        }
    )

    data = response.json()

    if response.status_code != 200:
        return data

    return {
        "city": data["name"],
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"]
    }

@mcp.tool()
def get_forecast(city:str):

    url=f"{BASE_URL}/forecast"
    
    params = {
        "q":city,
        "appid":OPENWEATHER_API_KEY,
        "units":"metric"
    }

    response = requests.get(url,params = params)

    data = response.json()

    if response.status_code != 200:
        return {
            "error": True,
            "status_code": response.status_code,
            "details": data,
        }

    forecast=[]

    # Return first 5 forecast entries
    for item in data.get("list", [])[:5]:
        forecast.append(
            {
                "datetime": item["dt_txt"],
                "temperature": item["main"]["temp"],
                "weather": item["weather"][0]["description"]
            }
        )
    
    return {
        "city" : city,
        "forecast" : forecast
    }

if __name__ == "__main__":
    mcp.run()