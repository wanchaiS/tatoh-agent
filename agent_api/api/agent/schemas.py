from typing import Any

from pydantic import BaseModel


class CreateThreadResponse(BaseModel):
    thread_id: str


class ThreadResponse(BaseModel):
    thread_id: str
    title: str | None
    created_at: str


class ThreadStateResponse(BaseModel):
    values: dict[str, Any]
    next: tuple
    checkpoint: dict[str, Any]
    created_at: str | None
    parent_checkpoint: dict[str, Any] | None
