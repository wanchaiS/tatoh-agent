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
    Get the REAL-TIME current weather and marine conditions (waves) for Koh Tao, Thailand.
    Use this ONLY when users ask about the weather RIGHT NOW, today, or "how's the weather" without specifying a future month.
    Returns raw data including temperature, weather condition, humidity, wind speed, and wave height.
    """
    owm_api_key = os.getenv("OPEN_WEATHER_API_KEY")
    if not owm_api_key:
        return {"error": "Weather service API key missing."}

    # Koh Tao coordinates
    lat = 10.10
    lon = 99.83

    # 1. Fetch meteorological data from OpenWeatherMap
    owm_url = "https://api.openweathermap.org/data/2.5/weather"
    owm_params = {
        "lat": lat,
        "lon": lon,
        "appid": owm_api_key,
        "units": "metric"
    }

    # 2. Fetch marine data (waves) from Open-Meteo
    marine_url = "https://marine-api.open-meteo.com/v1/marine"
    marine_params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["wave_height", "wave_period"]
    }

    try:
        owm_response = requests.get(owm_url, params=owm_params, timeout=10)
        owm_response.raise_for_status()
        owm_data = owm_response.json()

        marine_response = requests.get(marine_url, params=marine_params, timeout=10)
        marine_response.raise_for_status()
        marine_data = marine_response.json()

        return {
            "location": "Koh Tao",
            "condition": owm_data["weather"][0]["description"],
            "temperature": owm_data["main"]["temp"],
            "humidity": owm_data["main"]["humidity"],
            "wind_speed_ms": owm_data["wind"]["speed"],
            "wave_height_m": marine_data.get("current", {}).get("wave_height", 0),
            "wave_period_s": marine_data.get("current", {}).get("wave_period", 0)
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
