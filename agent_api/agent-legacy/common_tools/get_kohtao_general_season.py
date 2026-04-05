from langchain.tools import tool

from agent.services.knowledge_service import knowledge_service


@tool
async def get_kohtao_general_season():
    """
    Get official information about Koh Tao's seasons, weather patterns throughout the year,
    best times to visit for diving, and monthly climate conditions.

    CRITICAL: Use this tool for ANY question about weather in a specific month (e.g., "weather in October"),
    seasonal advice, or general climate patterns. Never rely on internal knowledge for seasonal weather.
    """
    doc = await knowledge_service.get_document("kohtao_seasons")
    if not doc:
        return {"error": "Seasons document not found."}
    return doc
