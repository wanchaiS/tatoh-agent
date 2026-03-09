from langchain.tools import tool

from agent.utils.google_drive_client import get_image_direct_link, read_markdown
from agent.utils.tool_errors import handle_tool_error


@tool
@handle_tool_error
def get_gopro_service_info():
    """
    Get information about GoPro cameras or cameras services borrow/rent.
    Includes pricing for various models, equipment inclusions, and rental duration.
    """

    details = read_markdown("/cooper-project/data/gopro_service_info.md")
    image_url = get_image_direct_link("/cooper-project/data/photos/cameras_rental.png")
    return {"details": details, "image_url": image_url}
