from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph.ui import push_ui_message
from langgraph.types import Command
from pydantic import BaseModel

from agent.criteria_discovery.discovery_agent import criteria_discovery_graph
from agent.criteria_discovery.schema import Criteria
from agent.types import GlobalState


class ConfirmationDecision(BaseModel):
    is_yes: bool


async def _check_confirmation(state: GlobalState) -> bool:
    """Return True if the user's latest message is an affirmative."""
    last_user_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break

    llm = ChatOpenAI(model="openai/gpt-4.1-nano", temperature=0)
    structured_llm = llm.with_structured_output(ConfirmationDecision)

    decision = await structured_llm.ainvoke(
        [
            SystemMessage(
                content="Did the user say yes / confirm? "
                "Set is_yes=true ONLY for clear, standalone affirmatives: yes, ok, sure, ใช่, ตกลง, ได้เลย, ยืนยัน, จอง, จองเลย. "
                "IMPORTANT: ครับ/ค่ะ are Thai politeness particles added to almost every sentence. "
                "They count as 'yes' ONLY when the entire message is just 'ครับ' or 'ค่ะ' alone. "
                "If ครับ/ค่ะ appears at the end of a longer sentence (e.g. 'เปลี่ยนวันหน่อยครับ'), set is_yes=false. "
                "Set is_yes=false for everything else (questions, change requests, unrelated messages)."
            ),
            last_user_msg,
        ]
    )
    return decision.is_yes


# ── Main node ──────────────────────────────────────────────────────
async def criteria_discovery_node(state: GlobalState, config: RunnableConfig):
    # Gate: if criteria ready but not confirmed, classify user response
    if state.get("criteria_ready") and not state.get("criteria_confirmed"):
        if await _check_confirmation(state):
            return Command(
                goto="room_searching_node",
                update={"criteria_confirmed": True},
            )
        # Not a clear "yes" — fall through to discovery subgraph
        # which will handle changes, questions, or unrelated messages

    sub_config = {**(config or {}), "recursion_limit": 10}
    result = await criteria_discovery_graph.ainvoke(state, config=sub_config)

    criteria = result.get("criteria") or Criteria()
    criteria_ready = result.get("criteria_ready", False)

    if criteria_ready:
        push_ui_message(
            "suggested_answers",
            {
                "options": ["ยืนยันการจอง", "ต้องการแก้ไข"],
            },
        )

    return {
        "criteria": criteria,
        "criteria_ready": criteria_ready,
        "ui": result.get("ui"),
        "messages": [result["messages"][-1]],
    }
