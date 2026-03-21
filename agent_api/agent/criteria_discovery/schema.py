import operator
from datetime import datetime, timedelta
from typing import List, Optional
from typing_extensions import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field



class DateWindow(BaseModel):
    start_date: str = Field(..., description="Start of the search window (YYYY-MM-DD).")
    end_date: str = Field(..., description="End of the search window (YYYY-MM-DD).")

    def window_days(self) -> int:
        """Total span of this window in days."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        return (end - start).days


class Criteria(BaseModel):
    """Search criteria for booking."""

    date_windows: List[DateWindow] = Field(default_factory=list)
    duration_nights: Optional[int] = Field(None)
    total_guests: Optional[int] = Field(None)
    requested_rooms: Optional[List[str]] = Field(None)
    requested_room_types: Optional[List[str]] = Field(None)

    def get_expanded_windows(self, expanded_days: int) -> List[tuple]:
        """
        Return each window expanded by ±expanded_days.
        Used as fallback when all windows return no rooms.
        """
        result = []
        for w in self.date_windows:
            try:
                start_dt = datetime.strptime(w.start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(w.end_date, "%Y-%m-%d")
            except ValueError:
                result.append((w.start_date, w.end_date))
                continue
            if expanded_days and expanded_days > 0:
                result.append(
                    (
                        (start_dt - timedelta(days=expanded_days)).strftime("%Y-%m-%d"),
                        (end_dt + timedelta(days=expanded_days)).strftime("%Y-%m-%d"),
                    )
                )
            else:
                result.append((w.start_date, w.end_date))
        return result

    def get_criteria_id(self) -> str:
        windows_key = "_".join(
            f"{w.start_date}-{w.end_date}"
            for w in sorted(self.date_windows, key=lambda w: w.start_date)
        )
        return f"{windows_key}_{self.duration_nights}_{self.total_guests}"

class PendingUIItem(TypedDict):
    name: str
    props: dict
    id: str

class CriteriaDiscoveryState(TypedDict):
    subgraph_messages: Annotated[list[AnyMessage], add_messages]
    criteria: Criteria
    is_criteria_ready: bool
    pending_ui: Annotated[list[PendingUIItem], operator.add]