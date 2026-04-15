from agent.services.knowledge_service import knowledge_service
from langchain.tools import tool


@tool
async def get_kohtao_arrival_guide():
    """
    Get general guidance and recommendations on how to travel to Koh Tao
    from different provinces (Chumphon, Surat Thani, and Bangkok) and islands.
    Use this when the user is asking for 'how' to get to Koh Tao or needs advice on routes.
    """
    doc = await knowledge_service.get_document("kohtao_arrival_guide")
    if not doc:
        return {"error": "Arrival guide document not found."}
    return doc
