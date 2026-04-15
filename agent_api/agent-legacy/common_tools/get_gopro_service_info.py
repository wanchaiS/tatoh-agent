from agent.services.knowledge_service import knowledge_service
from langchain.tools import tool


@tool
async def get_gopro_service_info():
    """
    Get information about GoPro cameras or cameras services borrow/rent.
    Includes pricing for various models, equipment inclusions, and rental duration.
    """
    doc = await knowledge_service.get_document("gopro_service_info")
    if not doc:
        return {"error": "GoPro service info document not found."}
    return doc
