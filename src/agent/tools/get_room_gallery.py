from typing import List
from langchain.tools import tool
from utils.google_drive_client import list_images_in_folder

@tool
def get_room_gallery(room_number: str) -> List[str]:
    """
    Get a collection of additional photos for a specific room.
    Use this when the user asks to see 'more pictures', 'better photos', 
    or 'more details' about a specific room.
    
    Args:
        room_number: The room identifier (e.g., 'S1', 'V2').
    """
    # Normalize room number to lowercase for GDrive path consistency
    room_id = room_number.strip().lower()
    path = f"/cooper-project/data/photos/rooms/{room_id}"
    
    return list_images_in_folder(path)
