# Research: LangGraph Service Injection & Lifecycle

## Context

Researching the canonical way LangGraph handles dependency injection for services (DB connections, API clients, etc.), especially on LangGraph Platform. The goal is to understand if the current `AgentServiceProvider` pattern in this project aligns with LangGraph's recommended approach, and what changes (if any) are needed.

---

## Key Findings from Official Docs

### 1. The New `context` / `Runtime` API (langgraph >= 1.1.0)

LangGraph now has a **first-class dependency injection system** via `context_schema` + `Runtime` object. This is the canonical approach:

**Graph definition:**
```python
@dataclass
class ContextSchema:
    db_session: AsyncSession
    pms: PmsClient

graph = StateGraph(State, context_schema=ContextSchema)  # <-- declare schema
```

**Node access:**
```python
from langgraph.runtime import Runtime

def my_node(state: State, runtime: Runtime[ContextSchema]):
    db = runtime.context.db_session  # typed access
```

**Tool access:**
```python
from langchain.tools import tool, ToolRuntime

@tool
def search_rooms(query: str, runtime: ToolRuntime[ContextSchema]) -> str:
    svc = runtime.context.room_availability  # typed access
```

**Invocation:**
```python
graph.invoke(inputs, context=ContextSchema(db_session=..., pms=...))
```

### 2. Three Context Types in LangGraph

| Type | Mutability | Lifetime | Access |
|------|-----------|----------|--------|
| **Static runtime context** (context_schema) | Immutable | Single run | `runtime.context` |
| **Dynamic runtime context** (state) | Mutable | Single run | `state["key"]` or `runtime.state` |
| **Cross-conversation context** (store) | Mutable | Persistent | `runtime.store` |

Services like DB connections, API clients = **static runtime context** (they don't change during a run).

### 3. LangGraph Platform Lifecycle

On the Platform:
- Each **run** (invoke/stream call) gets its own `context` values
- The `context` is passed per-run via the SDK: `client.runs.stream(thread_id, assistant_id, input=..., context=...)`
- **Assistants** can store default `context` values, so you don't re-pass them every run
- `runtime.server_info` provides platform-specific metadata (assistant_id, authenticated user)
- `runtime.execution_info` provides thread_id, run_id, attempt number

**Service lifecycle on Platform:**
- Context is scoped to a **single run** (single invoke/stream call)
- The Platform creates a new run for each request, so services in context are per-request
- For **singletons** (like API clients), you instantiate them at module level and reference them in the context schema defaults
- For **per-request resources** (like DB sessions), you create them fresh when building the context for each invoke

### 4. ToolRuntime vs InjectedToolArg

The **new way** (recommended):
```python
@tool
def my_tool(query: str, runtime: ToolRuntime[ContextSchema]) -> str:
    runtime.context      # static context
    runtime.state        # graph state
    runtime.store        # long-term memory
    runtime.stream_writer  # streaming
    runtime.execution_info  # thread_id, run_id
    runtime.server_info    # platform metadata
```

The **old way** (what this project currently uses):
```python
@tool
async def my_tool(
    query: str,
    runtime: Annotated[ToolRuntime, InjectedToolArg],
    config: Annotated[RunnableConfig, InjectedToolArg],
):
    # manual extraction from config
    svc = get_agent_service_provider(config).room_availability
```

Both work, but the new `ToolRuntime[ContextSchema]` is cleaner — no need for `Annotated[..., InjectedToolArg]` or manual config extraction.

---

## How This Project Currently Works

**Current pattern** (`agent/context/agent_service_provider.py`):
- `AgentServiceProvider` dataclass as a manual DI container
- Stuffed into `config["configurable"]["context"]` 
- Extracted in tools via `get_agent_service_provider(config)`
- Tools use both `Annotated[ToolRuntime, InjectedToolArg]` and `Annotated[RunnableConfig, InjectedToolArg]`

**What's good:**
- The DI container concept is sound — it matches LangGraph's `context_schema` pattern
- Singleton PmsClient + scoped services is correct lifecycle thinking

**What could be modernized:**
- Use `StateGraph(State, context_schema=AgentServiceProvider)` instead of manually stuffing into configurable
- Use `runtime: ToolRuntime[AgentServiceProvider]` in tools instead of `Annotated[..., InjectedToolArg]` + manual extraction
- Use `runtime: Runtime[AgentServiceProvider]` in nodes instead of extracting from config
- Invoke with `graph.invoke(inputs, context=AgentServiceProvider(...))` instead of passing through configurable dict

---

## Summary: What LangGraph Recommends

1. **Define a `context_schema` dataclass** with your services
2. **Pass it via `context=` parameter** at invoke time (not buried in `configurable`)
3. **Access via `Runtime[Schema]` in nodes** and `ToolRuntime[Schema]` in tools
4. **Singleton services** (API clients) → module-level instances, referenced as defaults in the dataclass
5. **Per-request services** (DB sessions) → created at invocation time and passed in context
6. **On LangGraph Platform** → context values can be set per-assistant or per-run via SDK
