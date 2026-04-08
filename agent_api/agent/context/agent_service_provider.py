from dataclasses import dataclass, field
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from agent.clients.pms_client import pms_client, PmsClient
from agent.services.room_availability_service import RoomAvailabilityService
from agent.services.room_service import RoomService
from db.database import AsyncSessionLocal

@dataclass
class AgentServiceProvider:
    """The central dependency injection container for all LangGraph tools."""

    # ── Singletons ──
    pms: PmsClient = pms_client

    # ── Scoped Services ──
    db_session: AsyncSession = field(default_factory=AsyncSessionLocal)
    room_availability: RoomAvailabilityService = field(default_factory=RoomAvailabilityService)
    room_service: RoomService = field(init=False)

    def __post_init__(self) -> None:
        self.room_service = RoomService(db=self.db_session)
    

def get_agent_service_provider(config: RunnableConfig) -> AgentServiceProvider:
    """Helper to safely extract the AgentServiceProvider from the incoming LangGraph config."""
    configurable = config.get("configurable", {})
    return configurable.get("context", AgentServiceProvider())
