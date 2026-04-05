"""Lightweight language detection using Thai-character heuristic."""

import re

from langchain_core.messages import BaseMessage, HumanMessage

from agent.types import GlobalState

_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
DEFAULT_LANGUAGE = "th"


def _detect_language(text: str) -> str:
    """Return 'th' if any Thai character is present, else 'en'."""
    return "th" if _THAI_RE.search(text) else "en"


def _get_last_human_text(messages: list[BaseMessage]) -> str:
    """Extract text from the last HumanMessage."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    blk.get("text", "")
                    if isinstance(blk, dict) and blk.get("type") == "text"
                    else str(blk)
                    for blk in content
                )
    return ""


def language_detection_node(state: GlobalState) -> dict:
    """Detect language from the last human message and store in state."""
    text = _get_last_human_text(state.get("messages", []))
    if not text.strip():
        return {"user_language": state.get("user_language", DEFAULT_LANGUAGE)}

    return {"user_language": _detect_language(text)}
