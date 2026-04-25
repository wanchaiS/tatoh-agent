from typing import Any

from langgraph.prebuilt import ToolNode

from agent.tools.exceptions import ToolValidationError
from agent.tools.search_available_rooms import search_available_rooms


def tool_error_handler(error: Exception) -> str:
    match error:
        case ToolValidationError():
            return f"Tool validation error: {error}"
        case _:
            return f"Unexpected system error: {error}"


tools = [search_available_rooms]
tool_node = ToolNode(tools, handle_tool_errors=tool_error_handler).with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)

_model_with_tools: Any = None


def get_model_with_tools() -> Any:
    global _model_with_tools
    if _model_with_tools is None:
        from langchain_openai import ChatOpenAI

        from core.config import settings

        model = ChatOpenAI(
            model="openai/gpt-5.1-instant",
            temperature=0,
            streaming=True,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools
