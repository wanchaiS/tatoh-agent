"""Typed reads from RunnableConfig['configurable'].

Tools and nodes access services through these accessors so there's a single
typed boundary between the config dict and consuming code.
"""

from typing_extensions import TypedDict

from langchain_core.runnables import RunnableConfig

from agent.services.room_availability import RoomAvailabilityService
from agent.utils.pms_client import PmsClient


class Configurable(TypedDict, total=False):
    """Typed shape of RunnableConfig['configurable']. Extend as services grow."""

    thread_id: str
    pms_client: PmsClient  # singleton
    room_availability_svc: RoomAvailabilityService  # scoped (per turn)


def _cfg(config: RunnableConfig) -> Configurable:
    return config.get("configurable", {})  # type: ignore[return-value]


def pms_client_from(config: RunnableConfig) -> PmsClient:
    return _cfg(config)["pms_client"]


def room_availability_svc_from(config: RunnableConfig) -> RoomAvailabilityService:
    return _cfg(config)["room_availability_svc"]
