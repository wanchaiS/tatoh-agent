from typing import Any
import re

def is_thai(text: Any) -> bool:
    """Check if the text contains any Thai characters."""
    if isinstance(text, str):
        return bool(re.search(r'[\u0e00-\u0e7f]', text))
    if isinstance(text, list):
        # Extract text from message parts (multimodal)
        for part in text:
            if isinstance(part, dict) and part.get("type") == "text":
                if is_thai(part.get("text", "")):
                    return True
    return False