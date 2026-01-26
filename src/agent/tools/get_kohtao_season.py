from utils.google_drive_client import read_markdown
from langchain.tools import tool


@tool
def get_kohtao_season():
    """
    Get official information about Koh Tao's seasons, weather patterns throughout the year, 
    best times to visit for diving, and monthly climate conditions.
    
    CRITICAL: Use this tool for ANY question about weather in a specific month (e.g., "weather in October"), 
    seasonal advice, or general climate patterns. Never rely on internal knowledge for seasonal weather.
    """
    details = read_markdown("/cooper-project/data/kohtao_seasons.md")
    return {"details": details}