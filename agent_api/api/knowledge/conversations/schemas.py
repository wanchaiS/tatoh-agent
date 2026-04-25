from pydantic import BaseModel


class ConversationItem(BaseModel):
    thread_id: str
    title: str | None
    created_at: str


class ConversationListResponse(BaseModel):
    threads: list[ConversationItem]
    total: int
    page: int
    limit: int
