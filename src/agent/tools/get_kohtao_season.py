from utils.google_drive_client import read_markdown
from langchain.tools import tool


@tool
def get_kohtao_season():
    """
    Get information about Koh Tao's seasons, weather throughout the year, 
    best times to visit for diving, and general climate conditions.
    Use this when the user asks about the weather in a specific month, 
    general weather patterns, or the best season to visit Koh Tao.
    """
    details = read_markdown("/cooper-project/data/kohtao_seasons")
    return {"details": details}