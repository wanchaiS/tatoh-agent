"""Photo schemas for room photo management."""

from pydantic import BaseModel


class PhotoResponse(BaseModel):
    """Response model for a photo."""

    id: int
    filename: str
    sort_order: int
    url: str
    thumbnail_url: str

    model_config = {"from_attributes": True}


class PhotoReorderItem(BaseModel):
    """Item for reordering photos."""

    id: int
    sort_order: int
