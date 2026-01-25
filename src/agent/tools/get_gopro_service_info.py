from utils.google_drive_client import read_markdown, get_image_direct_link
from langchain.tools import tool

@tool
def get_gopro_service_info():
    """
    Get information about GoPro camera rental services for underwater photography.
    Includes pricing for various models, equipment inclusions, and rental duration.
    Use this when users ask about renting GoPro cameras, GoPro prices, or taking photos underwater.
    """

    details = read_markdown("/cooper-project/data/gopro_service_info")
    image_url = get_image_direct_link("/cooper-project/data/photos/cameras_rental.png")
    return {"details": details, "image_url": image_url}