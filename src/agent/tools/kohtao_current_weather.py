import os
import requests
from langchain.tools import tool
from dotenv import load_dotenv

# Find the project root (where .env should be)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_ROOT_DIR, ".env")

# Load environment variables
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH, override=True)

@tool
def get_kohtao_weather():
    """
    Get the current weather for Koh Tao, Thailand.
    Includes temperature, weather description, humidity, and wind speed.
    Use this when users ask about the current weather, temperature, or conditions on Koh Tao.
    """
    api_key = os.getenv("OPEN_WEATHER_API_KEY")
    if not api_key:
        return "Weather service is currently unavailable (API key missing)."

    # Koh Tao coordinates
    lat = 10.10
    lon = 99.83

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"  # For Celsius
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather_desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return {
            "location": "Koh Tao, Thailand",
            "condition": weather_desc,
            "temperature": f"{temp}°C",
            "feels_like": f"{feels_like}°C",
            "humidity": f"{humidity}%",
            "wind_speed": f"{wind_speed} m/s",
            "summary": f"The current weather in Koh Tao is {weather_desc} with a temperature of {temp}°C (feels like {feels_like}°C). Humidity is at {humidity}% and wind speed is {wind_speed} m/s."
        }
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"
