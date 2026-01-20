from pathlib import Path
from langchain.tools import tool

@tool   
def get_room_info(room_number: str) -> str:
    """
    Get room information for a specific room number.
    
    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """
    # Resolve the data directory relative to this file's location
    # src/agent/tools/get_room_info.py -> 4 parents up -> root -> data/
    data_path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    
    file_path = data_path / f"{room_number.upper()}.md"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return content
    else:
        return f"ขออภัยค่ะ ข้อมูลห้องพัก {room_number} ยังไม่พร้อมให้บริการในขณะนี้ สามารถสอบถามประเภทอื่นได้นะคะ"