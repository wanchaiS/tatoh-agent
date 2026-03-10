from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command

from agent.criteria_discovery.schema import Criteria
from agent.rooms_searching.schema import RoomSearchResult
from agent.rooms_searching.search_rooms import RunSearchResult, search_rooms
from agent.types import GlobalState



async def room_searching_node(state: GlobalState, config: RunnableConfig):
    """
    A room search node that search for rooms and return the result to the user.
    it decide to go to evaluate options node or criteria discovery node based on the search result.
    """
    criteria = state.get("criteria")
    criteria_ready = state.get("criteria_ready")
    criteria_confirmed = state.get("criteria_confirmed")
    if not criteria_ready or not criteria_confirmed:
        error_msg = (
            f"Criteria not ready or confirmed something went wrong. Let's start over."
        )
        return Command(
            goto="criteria_discovery_node",
            update={
                "messages": [AIMessage(content=error_msg)],
                "criteria": Criteria(),
                "room_search_result": None,
                "criteria_ready": False,
                "criteria_confirmed": False,
                "phase": "criteria_discovery",
            },
        )

    # check if criteria id has changed or it's a new criteria id (first search)
    new_criteria_id = criteria.get_criteria_id()
    closing_state = state.get("closing_state")
    current_criteria_id = (
        getattr(closing_state, "current_criteria_id", None) if closing_state else None
    )

    # safety net: this shouldnt happen since this node is only called when criteria id has changed or it's a new criteria id (first search)
    if new_criteria_id == current_criteria_id:
        return Command(goto="closing_node")

    # Wrap blocking search in a RunnableLambda for observability tracing
    search_runnable = RunnableLambda(search_rooms).with_config({"run_name": "execute_pms_search"})
    search_result = await search_runnable.ainvoke(criteria)

    # Generate raw facts for agent state
    raw_summary = _build_search_results_summary(search_result, criteria)

    # Generate conversational summary for the user
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    system_prompt = (
        "You are a helpful hotel booking assistant.\n"
        "Your task is to summarize the following search results for the user in a friendly, conversational way.\n"
        "If there are rooms, welcome them with the options. If dates were expanded, explicitly mention that the original dates were full but you found alternatives.\n"
        "If no rooms were found even after expansion, politely inform them and ask them to pick different dates.\n"
        "Always reply in the same language the user has been speaking.\n\n"
        f"Search Results Facts:\n{raw_summary}"
    )

    recent_messages = state.get("messages", [])[-5:]
    response = await llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            *recent_messages
        ],
        config
    )

    if not search_result.rooms:
        # No rooms found case: Transition back to discovery phase so user can adjust criteria
        new_criteria = criteria.model_copy()
        new_criteria.date_windows = []
        new_criteria.duration_nights = None

        return Command(
            goto=END,
            update={
                "messages": [response],
                "criteria": new_criteria,
                "criteria_ready": False,
                "criteria_confirmed": False,
                "room_search_result": RoomSearchResult(
                    criteria_id=search_result.criteria_id,
                    rooms=[],
                    expanded_days=search_result.expanded_days,
                    exhausted=search_result.exhausted,
                    search_results_summary=raw_summary,
                ),
                "phase": "criteria_discovery",
            },
        )
    else:
        # Rooms found case (Exact or Expanded): Transition to evaluation phase
        return Command(
            goto=END,
            update={
                "messages": [response],
                "room_search_result": RoomSearchResult(
                    criteria_id=search_result.criteria_id,
                    rooms=search_result.rooms,
                    expanded_days=search_result.expanded_days,
                    exhausted=search_result.exhausted,
                    search_results_summary=raw_summary,
                ),
                "phase": "closing",
            },
        )


def _build_search_results_summary(
    search_result: RunSearchResult, criteria: Criteria
) -> str:
    """Build a summary of the search results for the agent."""

    # Extract data
    rooms = search_result.rooms
    expanded_days = search_result.expanded_days
    exhausted = search_result.exhausted

    # Build summary string
    summary = []

    # Header
    original_windows_str = ", ".join(
        f"{w.start_date} to {w.end_date}" for w in criteria.date_windows
    )
    summary.append(f"Search Original Date Windows: {original_windows_str}")
    summary.append(
        f"Expanded search by +-{expanded_days} days"
        if expanded_days > 0
        else "No expansion used"
    )

    if expanded_days > 0:
        expanded_windows_str = ", ".join(
            f"{st} to {en}" for (st, en) in criteria.get_expanded_windows(expanded_days)
        )
        summary.append(f"Search expanded date range: {expanded_windows_str}")
    else:
        summary.append("Search expanded date range: No expansion used")
    summary.append(f"Exhausted: {exhausted}")
    summary.append("")

    # Room details
    if rooms:
        summary.append(f"Found {len(rooms)} room options:")
        for room in rooms:
            summary.append(f"- No.{room.room_no}  Type:{room.room_type}")
    else:
        summary.append("No rooms found matching the criteria.")

    return "\n".join(summary)
