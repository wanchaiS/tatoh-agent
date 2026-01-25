from utils.google_drive_client import read_markdown, get_image_direct_link
from langchain.tools import tool

@tool
def get_koh_tao_arrival_guide():
    """
    Get general guidance and recommendations on how to travel to Koh Tao 
    from different provinces (Chumphon, Surat Thani, and Bangkok) and islands.
    Use this when the user is asking for 'how' to get to Koh Tao or needs advice on routes.
    """
    details = read_markdown("/cooper-project/data/koh_tao_arrival_guide")
    image_url = get_image_direct_link("/cooper-project/data/photos/transports/all_kohtao.jpg")
    return {"details": details, "image_url": image_url}
