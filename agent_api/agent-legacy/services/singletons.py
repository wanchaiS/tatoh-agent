"""App-lifetime services.

One instance per process. Lazy-created on first access, closed on app shutdown.
Used by both FastAPI (explicit lifespan shutdown) and langgraph dev (process exit).
"""

import httpx

from agent.utils.pms_client import PmsClient

_http_client: httpx.AsyncClient | None = None
_pms_client: PmsClient | None = None


def get_pms_client() -> PmsClient:
    global _http_client, _pms_client
    if _pms_client is None:
        _http_client = httpx.AsyncClient()
        _pms_client = PmsClient(_http_client)
    return _pms_client


async def close_singletons() -> None:
    """Close singleton resources. Called by FastAPI lifespan on shutdown."""
    global _http_client, _pms_client
    if _http_client is not None:
        await _http_client.aclose()
    _http_client = None
    _pms_client = None
