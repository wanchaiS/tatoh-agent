from typing import Any

from langchain_core.messages import SystemMessage

from agent.model import get_model_with_tools
from agent.prompt import get_prompt
from agent.state import State


async def agent_node(state: State) -> dict[str, Any]:
    prompt = get_prompt(state)
    response = await get_model_with_tools().ainvoke(
        [SystemMessage(content=prompt)] + state["messages"]
    )
    return {"messages": [response]}
