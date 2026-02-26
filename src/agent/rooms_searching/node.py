import asyncio
from typing import Dict, Any
from langgraph.types import Command
from langgraph.graph import END

from agent.types import GlobalState
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from agent.rooms_searching.search_rooms import search_rooms, RunSearchResult
from agent.criteria_discovery.schema import Criteria

async def room_searching_node(state: GlobalState):
    """
    A room search node that search for rooms and return the result to the user.
    it decide to go to evaluate options node or criteria discovery node based on the search result.
    """
    criteria = state.get("criteria")
    validation_error = criteria.validate_data() if criteria else "Missing criteria"
    if validation_error:
        # Scream to the UI/logs that something bypassed discovery validation
        # TODO fire UI event to show that unexpected error happend, can we reset the conversation?
        # we should wait for user to say yes to reset the conversation, as of now we will just assume user say yes
        error_msg = f"Unexpected error during criteria discovery: {validation_error}. Let's start over."
        return Command(
            goto="criteria_discovery_node",
            update={
                "messages": [AIMessage(content=error_msg)],
                "criteria": None,
                "room_evaluation_state": None,
                "phase": "criteria_discovery"
            }
        ) 
    

    # check if criteria id has changed or it's a new criteria id (first search)
    new_criteria_id = criteria.get_criteria_id()
    evaluation_state = state.get("room_evaluation_state")
    current_criteria_id = getattr(evaluation_state, "current_criteria_id", None) if evaluation_state else None
    
    # safety net: this shouldnt happen since this node is only called when criteria id has changed or it's a new criteria id (first search)
    if new_criteria_id == current_criteria_id:
        return Command(goto="evaluate_options_node")

    # Run blocking search in a separate thread
    search_result = await asyncio.to_thread(search_rooms, criteria)
    
    rooms_data = search_result.rooms
    criteria_id = search_result.criteria_id
    
    # Generate raw facts for agent state
    raw_summary = _build_search_results_summary(search_result, criteria)
    
    # Generate conversational summary for the user
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    system_prompt = (
        "You are a helpful hotel booking assistant.\n"
        "Your task is to summarize the following search results for the user in a friendly, conversational way.\n"
        "If there are rooms, welcome them with the options. If dates were expanded, explicitly mention that the original dates were full but you found alternatives.\n"
        "If no rooms were found even after expansion, politely inform them and ask them to pick different dates.\n"
        "Always reply in the same language the user has been speaking.\n\n"
        f"Search Results Facts:\n{raw_summary}"
    )
    
    # We pass the conversation history so the LLM knows the language and context
    messages = state.get("messages", [])
    response = await llm.ainvoke([SystemMessage(content=system_prompt)] + messages[-3:]) # just the recent context is enough
    
    if not rooms_data:
         # No rooms found case: Transition back to discovery phase so user can adjust criteria
         new_criteria = criteria.model_copy()
         new_criteria.search_date_start = None
         new_criteria.search_date_end = None
         new_criteria.duration_nights = None
         
         return Command(
            goto=END,
            update={
                "messages": [response],
                "criteria": new_criteria, # clear dates so user is asked for new ones but keep guests/rooms
                "phase": "criteria_discovery"
            }
        )
    else:
        # Rooms found case (Exact or Expanded): Transition to evaluation phase
        return Command(
            goto=END,
            update={
                "messages": [response],
                "room_evaluation_state": {
                    "current_criteria_id": criteria_id,
                    "current_search_results": rooms_data,
                    "expanded_days": search_result.expanded_days,
                    "exhausted": search_result.exhausted,
                    "search_results_summary": raw_summary
                },
                "phase": "evaluate_options"
            }
        )


def _build_search_results_summary(search_result: RunSearchResult, criteria: Criteria) -> str:
    """Build a summary of the search results for the agent."""
    
    # Extract data
    rooms = search_result.rooms
    expanded_days = search_result.expanded_days
    exhausted = search_result.exhausted
    
    # Build summary string
    summary = []
    
    # Header
    summary.append(f"Search Original Date: {criteria.search_date_start} - {criteria.search_date_end}")
    summary.append(f"Expanded search by +-{expanded_days} days" if expanded_days > 0 else "No expansion used")
    summary.append(f"Search expanded date range: {criteria.get_expanded_windows(expanded_days) if expanded_days > 0 else 'No expansion used'}")
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
