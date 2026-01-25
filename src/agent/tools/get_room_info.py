from pathlib import Path
from langchain.tools import tool
from utils.google_drive_client import read_spreadsheet_data


@tool   
def get_room_info(room_number: str) -> str:
    """
    Get room information for a specific room number.
    
    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """
    
    try:
        rooms = read_spreadsheet_data("/cooper-project/data/rooms_info")
        room = list(filter(lambda x: x["room_number"] == room_number, rooms))
        
        if room:
            return room[0]
        else:
            return f"ขออภัยค่ะ ไม่พบข้อมูลห้องพัก {room_number} กรุณาระบุหมายเลขห้องพักให้ถูกต้อง"
    except Exception as e:
        return f"ขออภัยค่ะ ข้อมูลห้องพัก {room_number} ยังไม่พร้อมให้บริการในขณะนี้ สามารถสอบถามประเภทอื่นได้นะคะ"