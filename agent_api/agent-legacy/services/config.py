"""RunnableConfig assembly and graph wrapping.

Central place that wires services into LangGraph's RunnableConfig. Two paths:

- `singleton_config()` + `wrap_with_scoped_filler()` are applied at graph
  compile time (used by both root_graph.py and main.py).
- `build_runnable_config()` is called per request by the FastAPI route and
  produces the full configurable dict for that invocation.
"""

from typing import TYPE_CHECKING

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from agent.services.scoped import build_room_availability_svc

if TYPE_CHECKING:
    pass


def singleton_config() -> dict:
    """Singleton services baked into the graph at compile time.

    Shared by root_graph.py (langgraph dev export) and main.py (FastAPI's
    checkpointed graph) so the bake is identical in both entrypoints.
    """
    from agent.services.singletons import get_pms_client
    return {"pms_client": get_pms_client()}


def build_runnable_config(
    *, thread_id: str, overrides: dict | None = None
) -> RunnableConfig:
    """Per-invocation config assembled by the FastAPI route.

    One call per graph run (one user turn). Scoped services are created
    fresh here; singletons are already baked into the graph via
    singleton_config(), so LangChain merges the two at invocation time.
    """
    configurable: dict = {
        "thread_id": thread_id,
        # --- scoped services (fresh per turn) ---
        "room_availability_svc": build_room_availability_svc(),
    }
    if overrides:
        configurable.update(overrides)  # test seam
    return {"configurable": configurable}


def enrich_scoped(config: RunnableConfig | None) -> RunnableConfig:
    """Idempotent filler used by the graph wrapper (langgraph dev path).

    FastAPI path already populates scoped services via build_runnable_config(),
    so existing keys are preserved. Lazy — scoped factories only run when a
    key is missing.
    """
    cfg = dict(config or {})
    configurable = dict(cfg.get("configurable", {}))
    if "room_availability_svc" not in configurable:
        configurable["room_availability_svc"] = build_room_availability_svc()
    # Future scoped services: add another `if key not in configurable` block.
    cfg["configurable"] = configurable
    return cfg


class _ScopedCompiledGraph(CompiledStateGraph):
    """CompiledStateGraph subclass that fills scoped services per invocation.

    Uses __class__ reassignment (method dispatch via normal Python MRO) so
    LangGraph's internal tracing and event-loop paths are not interfered with.
    """

    async def ainvoke(self, input, config=None, **kwargs):  # type: ignore[override]
        return await super().ainvoke(input, enrich_scoped(config), **kwargs)

    async def astream(self, input, config=None, **kwargs):  # type: ignore[override]
        async for chunk in super().astream(input, enrich_scoped(config), **kwargs):
            yield chunk


def wrap_with_scoped_filler(compiled: CompiledStateGraph) -> CompiledStateGraph:
    """Rewrap a compiled graph so each invocation runs enrich_scoped() first.

    Called by both root_graph.py and main.py after compiling + baking
    singletons so scoped services are guaranteed present in config.
    """
    compiled.__class__ = _ScopedCompiledGraph
    return compiled
