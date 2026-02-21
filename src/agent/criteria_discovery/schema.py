from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

SearchMode = Literal["exact", "flexible"]

class Criteria(BaseModel):
    search_mode: Optional[SearchMode] = Field(None, description="The mode of search 'exact', 'flexible'.")
    check_in_date: Optional[str] = Field(None, description="Check-in date in YYYY-MM-DD format.")
    check_out_date: Optional[str] = Field(None, description="Check-out date in YYYY-MM-DD format.")
    search_date_start: Optional[str] = Field(None, description="Start date for availability window (YYYY-MM-DD).")
    search_date_end: Optional[str] = Field(None, description="End date for availability window (YYYY-MM-DD).")
    duration_nights: Optional[int] = Field(None, description="Duration of stay in number of nights.")
    total_guests: Optional[int] = Field(None, description="Total number of guests.")
    preferred_rooms: Optional[List[str]] = Field(None, description="Specific room numbers preferred by the user.")
    is_year_ambiguous: Optional[bool] = Field(None, description="Set to true if a date/month is mentioned but it's unclear if it's for the current year or next year.")
    is_duration_confirmed: Optional[bool] = Field(None, description="Set to true ONLY when the user explicitly confirms the duration/check-out date, OR if they originally provided the exact number of nights explicitly.")

    def _parse(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str: return None
        try: return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError): return None

    @property
    def check_in(self): return self._parse(self.check_in_date)
    @property
    def check_out(self): return self._parse(self.check_out_date)
    @property
    def start_win(self): return self._parse(self.search_date_start)
    @property
    def end_win(self): return self._parse(self.search_date_end)

    def auto_fill(self):
        """Derive missing fields based on provided data."""
        if self.search_mode == "exact":
            if self.check_in and self.duration_nights and self.duration_nights > 0 and not self.check_out_date:
                cout = self.check_in + timedelta(days=self.duration_nights)
                self.check_out_date = cout.strftime("%Y-%m-%d")
            elif self.check_in and self.check_out:
                diff = (self.check_out - self.check_in).days
                if diff > 0:
                    self.duration_nights = diff

            # In exact mode, search window = check-in/out dates
            if self.check_in_date and not self.search_date_start:
                self.search_date_start = self.check_in_date
            if self.check_out_date and not self.search_date_end:
                self.search_date_end = self.check_out_date

    def get_missing_fields(self) -> List[str]:
        """Determine missing fields based on the search mode."""
        required_fields = {
            "exact": ["total_guests", "check_in_date", "check_out_date", "duration_nights"],
            "flexible": ["search_date_start", "search_date_end", "total_guests", "duration_nights"],
        }
        mode = self.search_mode or "exact"
        return [f for f in required_fields.get(mode, ["total_guests"]) if not getattr(self, f)]

    def validate_data(self) -> Optional[str]:
        """Validate state and return error message if invalid."""
        errors = []
        if self.total_guests is not None and self.total_guests < 1:
            errors.append("Number of guests must be at least 1")

        if self.search_mode == "exact":
            if self.check_in and self.check_out and (self.check_out - self.check_in).days <= 0:
                errors.append("Check-out must be after check-in")
            elif self.check_in and self.duration_nights and self.duration_nights < 1:
                errors.append("Duration must be at least 1 night")
        
        elif self.search_mode == "flexible":
            if self.start_win and self.end_win:
                win_days = (self.end_win - self.start_win).days
                if win_days < 0:
                    errors.append("Search end date must be after start date")
                elif self.duration_nights and self.duration_nights > win_days and win_days > 0:
                    errors.append(f"Requested stay ({self.duration_nights} nights) is longer than the search window ({win_days} nights)")

        return ". ".join(errors) if errors else None

    def get_criteria_id(self) -> str:
        return f"{self.search_mode}_{self.search_date_start}_{self.search_date_end}_{self.total_guests}_{self.duration_nights}"
