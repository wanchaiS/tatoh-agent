"""Per-turn (per-invocation) service factories.

Each factory produces a fresh instance per graph invocation. Scoped services
must NOT be shared across turns — they typically hold request-specific state
or caches of live data that would become stale.
"""

from agent.services.room_availability import RoomAvailabilityService
from agent.services.singletons import get_pms_client


def build_room_availability_svc() -> RoomAvailabilityService:
    """Per-turn availability service.

    Holds a cache of PMS windows already fetched within a single graph
    invocation (one user turn). PMS availability is live data, so the
    cache must not leak across turns.
    """
    return RoomAvailabilityService(get_pms_client())
