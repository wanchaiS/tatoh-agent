import asyncio
from typing import Dict, Any

from agent.types import GlobalState
from langchain_core.messages import AIMessage
from agent.rooms_searching.search_rooms import search_rooms, RunSearchResult
from agent.criteria_discovery.schema import Criteria

async def search_availability_node(state: GlobalState) -> Dict[str, Any]:
    """
    Programmatic node that performs the room search using the collected criteria.
    It does not use an LLM, it just runs the search and updates the state.
    """
    criteria = state.get("criteria")
    validation_error = criteria.validate_data() if criteria else "Missing criteria"
    if validation_error:
        # Scream to the UI/logs that something bypassed discovery validation
        error_msg = f"Unexpected error during criteria discovery: {validation_error}. Let's start over."
        return {
            "messages": [AIMessage(content=error_msg)],
            "criteria": None,
            "room_evaluation_state": None,
            "phase": "criteria_discovery"  # Revert phase so it doesn't enter evaluation
        } 
    
    # check if criteria id has changed or it's a new criteria id (first search)
    new_criteria_id = criteria.get_criteria_id()
    evaluation_state = state.get("room_evaluation_state")
    current_criteria_id = getattr(evaluation_state, "current_criteria_id", None) if evaluation_state else None
    
    if new_criteria_id == current_criteria_id:
        return {}

    # Run blocking search in a separate thread
    search_result = await asyncio.to_thread(search_rooms, criteria)
    
    rooms_data = search_result.rooms
    criteria_id = search_result.criteria_id
    
    return {
        "room_evaluation_state": {
            "current_criteria_id": criteria_id,
            "current_search_results": rooms_data,
            "expanded_days": search_result.expanded_days,
            "exhausted": search_result.exhausted,
            "search_results_summary": _build_search_results_summary(search_result, criteria)
        },
        "phase": "evaluate_options"
    }


def _build_search_results_summary(search_result: RunSearchResult, criteria: Criteria) -> str:
    """Build a summary of the search results for the agent."""
    
    # Extract data
    rooms = search_result.rooms
    expanded_days = search_result.expanded_days
    exhausted = search_result.exhausted
    
    # Build summary string
    summary = []
    
    # Header
    summary.append("[Search Results Summary]")
    summary.append(f"Search Original Date: {criteria.search_date_start} - {criteria.search_date_end}")
    summary.append(f"Expanded search by +-{expanded_days} days" if expanded_days > 0 else "No expansion needed")
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
