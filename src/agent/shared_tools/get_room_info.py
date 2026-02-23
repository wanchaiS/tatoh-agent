from pathlib import Path
from langchain.tools import tool
from agent.utils.google_drive_client import read_spreadsheet_data
from agent.utils.tool_errors import handle_tool_error

@tool   
@handle_tool_error
def get_room_info(room_number: str) -> str:
    """
    Get room information for a specific room number.
    
    Args:
        room_number: The identifier for the room (e.g., "S1", "V2").
    """
    
    rooms = read_spreadsheet_data("/cooper-project/data/rooms_info")
    room = next((r for r in rooms if r.get("room_name") == room_number), None)
    
    if room:
        info = [
            f"ห้องพัก: {room.get('room_name')} ({room.get('room_type')})",
            f"รายละเอียด: {room.get('summary')}",
            f"เตียง: {room.get('beds')} | ห้องน้ำ: {room.get('baths')} | ขนาด: {room.get('size (sqrm)')} ตรม.",
            f"ราคา (วันธรรมดา): {room.get('price_weekdays')} บาท",
            f"ราคา (เสาร์-อาทิตย์/นักขัตฤกษ์): {room.get('price_weekends_holidays')} บาท",
            f"ราคา (ปีใหม่-สงกรานต์): {room.get('price_ny_songkran')} บาท",
            f"พักได้สูงสุด: {room.get('max_guests')} ท่าน",
            f"ใกล้หาด: {room.get('close_to_beach')}/10 | วิวทะเล: {room.get('sea_view')}/10 | ความเป็นส่วนตัว: {room.get('private')}/10",
            f"ความลำบากในการเดิน: {room.get('walking_difficulty')}/10"
        ]
        return "\n".join(info)
    else:
        return f"ขออภัยค่ะ ไม่พบข้อมูลห้องพัก {room_number} กรุณาระบุหมายเลขห้องพักให้ถูกต้อง เช่น S1, V2 เป็นต้น"