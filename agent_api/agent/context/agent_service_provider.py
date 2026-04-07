from dataclasses import dataclass
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
    room_availability: RoomAvailabilityService | None = None
    db_session: AsyncSession | None = None
    room_service: RoomService | None = None

    def __post_init__(self) -> None:
        if self.db_session is None:
            self.db_session = AsyncSessionLocal()
        
        if self.room_availability is None:
            self.room_availability = RoomAvailabilityService()
            
        if self.room_service is None:
            self.room_service = RoomService(db=self.db_session)
    

def get_agent_service_provider(config: RunnableConfig) -> AgentServiceProvider:
    """Helper to safely extract the AgentServiceProvider from the incoming LangGraph config."""
    configurable = config.get("configurable", {})
    return configurable.get("context", AgentServiceProvider())
