"""Photo schemas for room photo management."""

from pydantic import BaseModel


class PhotoResponse(BaseModel):
    """Response model for a photo."""

    id: int
    filename: str
    sort_order: int
    url: str
    thumbnails: dict[
        int, str
    ]  # keyed by width in px: {240: "...", 480: "...", 960: "..."}

    model_config = {"from_attributes": True}


class PhotoReorderItem(BaseModel):
    """Item for reordering photos."""

    id: int
    sort_order: int
