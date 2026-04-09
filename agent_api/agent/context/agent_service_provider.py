from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from agent.clients.pms_client import pms_client, PmsClient
from agent.services.room_availability_service import RoomAvailabilityService
from agent.services.room_service import RoomService
from db.database import AsyncSessionLocal

@dataclass
class AgentServiceProvider:
    """The central dependency injection container for all LangGraph tools.

    Used as `context_schema` for StateGraph. When running via `langgraph dev`,
    defaults are used automatically. When running via FastAPI, you can override
    by passing `context=AgentServiceProvider(db_session=...)` to graph.astream().
    """

    # ── Singletons ──
    pms: PmsClient = pms_client

    # ── Scoped Services ──
    db_session: AsyncSession = field(default_factory=AsyncSessionLocal)
    room_availability: RoomAvailabilityService = field(default_factory=RoomAvailabilityService)
    room_service: RoomService = field(init=False)

    def __post_init__(self) -> None:
        self.room_service = RoomService(db=self.db_session)
