# Migration: Multi-Agent Subgraph → Flat Graph with Dynamic System Prompt

## Goal
Replace the current 3-subgraph architecture with a single agent node that uses
dynamic system prompt + tool switching based on `state["phase"]`. All messages
(including tool calls) stay in one shared history.

## Key Benefits
- **Streaming**: Current subgraph uses `ainvoke()` which blocks until the entire
  subgraph loop finishes — user sees nothing until the end. Flat graph streams
  the agent's LLM response directly to the client on every turn, including
  between tool calls. This is a major UX improvement.
- **Full conversation context**: All messages preserved across phases
- **Simpler code**: No subgraph bridge, no pending_ui buffer, no message extraction

---

## Pre-migration: Understand current flow
- [ ] Current graph: `START → ui_cleanup → language_detection → phase_router → {criteria_discovery | room_searching | closing} → END`
- [ ] `criteria_discovery` is a full subgraph (agent loop + tool node) via `subgraph_caller_node`
- [ ] `room_searching` is a standalone node (no agent loop, just search + LLM summary)
- [ ] `closing` is a stub returning placeholder message

---

## Step 1: Update `GlobalState` (types.py)
- [ ] Remove dependency on `CriteriaDiscoveryState` as a separate type for subgraph
- [ ] Keep `GlobalState` fields as-is (they're already correct for flat graph):
  - `phase`, `criteria`, `criteria_ready`, `room_search_result`, `closing_state`, `user_language`, `ui`, `messages`
- [ ] Note: `CriteriaDiscoveryState.subgraph_messages` and `pending_ui` will no longer be needed

**File:** `agent_api/agent/types.py`

---

## Step 2: Refactor `update_criteria` tool to use `GlobalState` keys
- [ ] Change all `Command(update={...})` to use `messages` instead of `subgraph_messages`
- [ ] Remove all `pending_ui` references (UI will be pushed directly)
- [ ] Change `is_criteria_ready` → `criteria_ready` (match GlobalState key)
- [ ] Tool already uses `runtime.state` to read criteria — this still works

**File:** `agent_api/agent/criteria_discovery/tools/update_criteria.py`

---

## Step 3: Refactor `revise_criteria` tool
- [ ] Already returns `Command(update={"phase": "criteria_discovery", ...})` — mostly correct
- [ ] Verify it uses `messages` key (it does ✓)

**File:** `agent_api/agent/closing/tools/revise_crteria.py`

---

## Step 4: Refactor shared tools that use `subgraph_messages` or `pending_ui`
- [ ] Check each shared tool in `agent_api/agent/shared_tools/` for:
  - References to `subgraph_messages` → change to `messages`
  - References to `pending_ui` → replace with direct `push_ui_message()` calls
- [ ] Files to check:
  - `get_room_info.py`
  - `get_rooms_list.py`
  - `get_room_gallery.py`
  - `find_boat_schedules.py`
  - `get_kohtao_arrival_guide.py`
  - `get_kohtao_current_weather.py`
  - `get_kohtao_general_season.py`
  - `get_gopro_service_info.py`
  - `no_tool_found.py`
  - `out_of_scope.py`
  - `ask_for_clarification.py`

---

## Step 5: Create prompt registry + tool sets per phase
- [ ] Create new file: `agent_api/agent/prompts.py` (or inline in graph)
- [ ] Define `get_prompt_and_tools(state: GlobalState) -> tuple[str, list]`:
  ```
  phase == "criteria_discovery":
    prompt = build_criteria_discovery_prompt(criteria, today, user_language)
    tools = qa_tools + [update_criteria]

  phase == "room_searching":
    (this phase has NO agent loop — it's a standalone node, keep as-is)

  phase == "closing":
    prompt = build_closing_prompt(closing_state, room_search_result, criteria, user_language)
    tools = qa_tools + [revise_criteria] + closing_tools (future)
  ```
- [ ] Move `build_system_prompt()` from `discovery_graph.py` → `prompts.py`
- [ ] Create `build_closing_prompt()` for closing phase

**Key decision:** `room_searching` is NOT an agent loop — it's a procedural node
(search rooms → LLM summarize → return). Keep it as a separate node, not part of
the agent loop. The flat graph agent handles `criteria_discovery` and `closing` phases.

---

## Step 6: Create the single agent node
- [ ] Create new file: `agent_api/agent/agent_node.py`
- [ ] Single `agent_node(state, config)` function:
  1. Read `state["phase"]`
  2. Get (system_prompt, tools) from prompt registry
  3. Bind tools to LLM
  4. Invoke with `[SystemMessage(system_prompt)] + state["messages"]`
  5. Return `{"messages": [response]}`
- [ ] Use `ChatOpenAI(model="openai/gpt-5.1-instant", ...)` (same as current)

**File:** `agent_api/agent/agent_node.py`

---

## Step 7: Rewrite `root_graph.py`
- [ ] New graph structure:
  ```
  START → ui_cleanup → language_detection → phase_router

  phase_router routes to:
    "criteria_discovery" or "closing" → agent_node → tool_router
    "room_searching" → room_searching_node → END

  tool_router:
    has_tool_calls → tools_node → agent_node (loop)
    no_tool_calls → after_agent_router

  after_agent_router:
    criteria_ready changed to True → room_searching_node
    else → END

  room_searching_node → END
  ```
- [ ] Wire `ToolNode` with ALL tools (union of all phase tools)
- [ ] The `agent_node` naturally loops with tool calls via `tools_condition`

**File:** `agent_api/agent/root_graph.py`

---

## Step 8: Handle room_searching as a procedural node (not agent)
- [ ] Keep `room_searching_node` mostly as-is
- [ ] It's called AFTER criteria_discovery sets `criteria_ready=True`
- [ ] After room_searching completes, it sets `phase="closing"` or `phase="criteria_discovery"`
- [ ] Next user message enters the agent loop in the appropriate phase

**File:** `agent_api/agent/rooms_searching/node.py` (minimal changes)

---

## Step 9: Delete obsolete files
- [ ] Delete `agent_api/agent/criteria_discovery/discovery_graph.py` (subgraph)
- [ ] Delete `agent_api/agent/criteria_discovery/subgraph_caller_node.py` (bridge)
- [ ] Delete `agent_api/agent/criteria_discovery/node.py` (old agent, already deleted in git)
- [ ] Clean up `CriteriaDiscoveryState` from `schema.py` (keep `Criteria`, `DateWindow`, `PendingUIItem`)

---

## Step 10: Fix UI message anchoring
- [ ] Currently `subgraph_caller_node` pushes pending_ui after subgraph completes
- [ ] In flat graph: tools should call `push_ui_message()` directly (no pending_ui buffer)
- [ ] Verify shared tools that return UI cards use `push_ui_message()` correctly
- [ ] The agent's AIMessage ID is available at tool execution time via the tool call

---

## Step 11: Test end-to-end flows
- [ ] Happy path: user provides criteria → search → results shown → closing
- [ ] No rooms found: search → back to criteria_discovery → user adjusts → re-search
- [ ] Revise criteria from closing: user says "change dates" → revise_criteria tool → back to discovery
- [ ] Q&A during discovery: user asks about rooms/weather mid-discovery
- [ ] Multi-turn discovery: user provides partial criteria across multiple messages
- [ ] Tool call preservation: verify tool calls visible in message history across phases
- [ ] UI anchoring: verify room cards/search results anchor to correct messages

---

## File Change Summary

| File | Action |
|------|--------|
| `agent_api/agent/root_graph.py` | **Rewrite** — new flat graph |
| `agent_api/agent/agent_node.py` | **New** — single agent node |
| `agent_api/agent/prompts.py` | **New** — prompt registry per phase |
| `agent_api/agent/types.py` | **Minor edit** — may remove unused imports |
| `agent_api/agent/criteria_discovery/tools/update_criteria.py` | **Edit** — subgraph_messages → messages, is_criteria_ready → criteria_ready |
| `agent_api/agent/criteria_discovery/schema.py` | **Edit** — remove CriteriaDiscoveryState |
| `agent_api/agent/shared_tools/*.py` | **Check/Edit** — subgraph_messages → messages, pending_ui → push_ui_message |
| `agent_api/agent/rooms_searching/node.py` | **Minor edit** — adjust routing |
| `agent_api/agent/closing/node.py` | **Rewrite** — integrate into agent_node |
| `agent_api/agent/closing/tools/revise_crteria.py` | **Minor edit** — verify keys |
| `agent_api/agent/criteria_discovery/discovery_graph.py` | **Delete** |
| `agent_api/agent/criteria_discovery/subgraph_caller_node.py` | **Delete** |
