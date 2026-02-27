from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

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
    
    def is_ready(self) -> bool:
        """Check if the criteria is ready to be used for searching."""
        return self.search_date_start is not None and self.search_date_end is not None and self.duration_nights is not None and self.total_guests is not None and self.is_year_ambiguous is False
        
    def get_expanded_windows(self, expanded_days: int) -> Tuple[str, str]:
        """
        Get expanded search windows
        
        Args:
            expanded_days: Number of days to expand the search by
            
        Returns:
            Tuple of (expanded_start_date, expanded_end_date)
        """
        if not expanded_days or expanded_days < 0:
            return self.search_date_start, self.search_date_end
        
        start_dt = self._parse(self.search_date_start)
        end_dt = self._parse(self.search_date_end)
        
        if not start_dt or not end_dt:
            return self.search_date_start, self.search_date_end
        
        start_dt = start_dt - timedelta(days=expanded_days)
        end_dt = end_dt + timedelta(days=expanded_days)

        return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
        
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
