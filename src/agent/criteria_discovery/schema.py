from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Criteria(BaseModel):
    search_date_start: Optional[str] = Field(None, description="Start date for availability window (YYYY-MM-DD).")
    search_date_end: Optional[str] = Field(None, description="End date for availability window (YYYY-MM-DD).")
    duration_nights: Optional[int] = Field(None, description="Duration of stay in number of nights.")
    total_guests: Optional[int] = Field(None, description="Total number of guests.")
    is_year_ambiguous: Optional[bool] = Field(None, description="Set to true if a date/month is mentioned but it's unclear if it's for the current year or next year.")
    def _parse(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str: return None
        try: return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError): return None

    def get_missing_fields(self) -> List[str]:
        """Determine missing fields."""
        required_fields = ["total_guests", "search_date_start", "search_date_end", "duration_nights"]
        return [f for f in required_fields if not getattr(self, f)]

    def validate_data(self) -> Optional[str]:
        """Validate state and return error message if invalid."""
        errors = []
        if self.total_guests is not None and (self.total_guests < 1 or self.total_guests > 30):
            errors.append("Number of guests is unlikely to be less than 1 or more than 30. Ask the user to confirm the number of guests.")

        start_dt = self._parse(self.search_date_start)
        end_dt = self._parse(self.search_date_end)

        if start_dt and end_dt:
            win_days = (end_dt - start_dt).days
            if win_days < 0:
                errors.append("Search end date must be after start date. Ask the user to confirm the dates.")
            elif self.duration_nights and self.duration_nights > win_days and win_days > 0:
                errors.append(f"Requested stay ({self.duration_nights} nights) is longer than the search window ({win_days} nights). Ask the user to confirm the duration.")

        return ". ".join(errors) if errors else None

    def get_criteria_id(self) -> str:
        return f"{self.search_date_start}_{self.search_date_end}_{self.total_guests}_{self.duration_nights}"
