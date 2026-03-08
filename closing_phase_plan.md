# Closing Phase Implementation Plan

## Context

The agent has 3 phases: criteria_discovery → room_searching → closing. The first two are complete. The closing phase is scaffolded (`src/agent/closing/`) but non-functional — empty booking tools, buggy node wrapper, minimal state schema. We need to build the full closing flow: room consultation, comparison, selection with dates, pricing, TOS, payment (bank transfer), staff HITL confirmation via LangGraph interrupt, and booking summary.

**Architecture decision**: Single agent with many tools (not sub-phases), because the user can ask questions at any point in the flow. The system prompt is **dynamic** — it changes focus based on the current `closing_step` so the agent naturally steers the conversation back to the right part of the flow after handling any side question.

---

## Step 1: Fix broken imports & add missing pricing models

### `src/agent/rooms_searching/schema.py`
Add the missing Pydantic models that `pricing.py` already imports:
```python
class PriceBreakdownItem(BaseModel):
    tier: str       # "Weekday" | "Weekend" | "Holiday"
    nights: int
    rate: float
    subtotal: float

class ExtraBedInfo(BaseModel):
    nights: int
    rate_per_night: float = 500.0
    subtotal: float = 0.0  # computed in __init__

class StayPricing(BaseModel):
    total_price: float
    breakdown: List[PriceBreakdownItem]
    extra_bed: Optional[ExtraBedInfo] = None
```

### `src/agent/types.py`
- Change import from `agent.room_evaluation.schema` → `agent.closing.schema`
- Rename `room_evaluation_state` → `closing_state` in GlobalState
- Rename `RoomEvaluationState` → `ClosingState`
- Simplify Phase: `Literal["criteria_discovery", "room_searching", "closing"]`

### `src/agent/root_graph.py`
- Change import from `agent.room_evaluation.node` → `agent.closing.node`
- Rename node to `closing_node`
- Fix phase_map: `"closing"` → `"closing_node"`
- Fix conditional_edges mapping to match
- Add checkpointer for interrupt support: `graph_builder.compile(checkpointer=...)`

---

## Step 2: Expand closing state schema

### `src/agent/closing/schema.py`

Rename `RoomEvaluationState` → `ClosingState`. All references across the codebase update accordingly.

```python
ClosingStep = Literal[
    "consulting",        # Q&A, comparing, recommending — no room selected
    "room_selected",     # room + dates picked, pricing shown
    "tos_accepted",      # user accepted TOS
    "payment_presented", # bank details shown
    "awaiting_staff",    # interrupt fired, waiting for staff
    "booking_confirmed", # staff confirmed, done
]

class SelectedStay(BaseModel):
    room_no: str
    check_in: str   # YYYY-MM-DD
    check_out: str  # YYYY-MM-DD

class PricingSummary(BaseModel):
    total_price: float
    breakdown_text: str
    extra_bed_note: Optional[str] = None

class ClosingState(BaseModel):
    closing_step: ClosingStep = "consulting"
    selected_stay: Optional[SelectedStay] = None
    pricing: Optional[PricingSummary] = None
    tos_accepted: bool = False
    payment_presented: bool = False
    staff_confirmed: bool = False
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
```

---

## Step 3: Build tools

### `src/agent/closing/tools/compare_rooms.py` (NEW)
- `compare_rooms(room_numbers: List[str])` — fetches room metadata via `RoomService`, builds text comparison table (type, size, beds, sea_view, steps_to_beach, privacy, style)
- Returns ToolMessage with comparison text, no state change
- **Shareable**: this tool can also be used by other nodes (e.g. criteria_discovery) since it's a pure Q&A tool

### `src/agent/closing/tools/booking_tools.py` (REWRITE — currently empty)

**`select_room(room_no, check_in, check_out)`**
- Validates room exists in `room_search_result.rooms`
- Validates dates fall within room's `available_dates` windows
- Calls `calculate_stay_pricing()` from `pricing.py`
- Updates `closing_state`: `selected_stay`, `pricing`, `closing_step="room_selected"`
- Resets downstream flags if re-selecting (tos_accepted, payment_presented, staff_confirmed → False)
- Returns ToolMessage with formatted pricing breakdown

**`present_terms_of_service()`**
- Guard: room must be selected
- Returns static TOS text as ToolMessage
- No state change yet (agent handles acceptance conversationally)

**`accept_tos_and_show_payment(guest_name, guest_phone, guest_email?)`**
- Guard: room selected
- Updates `closing_state`: `tos_accepted=True`, `payment_presented=True`, `closing_step="payment_presented"`, guest info
- Returns ToolMessage with bank transfer details + amount

**`submit_for_staff_confirmation()`**
- Guard: tos_accepted and payment_presented
- Updates `closing_state`: `closing_step="awaiting_staff"`
- Returns ToolMessage telling agent to inform guest to wait
- (The actual interrupt happens at node level, not in this tool)

**`create_booking_summary()`**
- Guard: staff_confirmed
- Updates `closing_state`: `closing_step="booking_confirmed"`
- Builds and returns full booking summary text
- (Future: PMS API call goes here)

### `src/agent/closing/tools/revise_crteria.py` (UPDATE)
- Also reset `closing_state` to defaults when routing back

---

## Step 4: Rewrite closer agent with dynamic system prompt

### `src/agent/closing/closer_agent.py`

The system prompt is **composed dynamically** based on `closing_step`. The base prompt (identity, search results, tool rules) stays constant, but a **focus directive** section changes per step to steer the agent's behavior:

```python
def _build_step_directive(closing_state: ClosingState) -> str:
    step = closing_state.closing_step

    if step == "consulting":
        return """[YOUR CURRENT FOCUS: ROOM CONSULTATION]
        Help the user choose a room. Compare options, answer questions, recommend based on preferences.
        When the user decides, use select_room with their chosen room + specific check-in/check-out dates.
        SOFT CLOSE: End responses nudging toward a choice (e.g. "สนใจเป็นห้องไหนดีคะ?")"""

    elif step == "room_selected":
        return f"""[YOUR CURRENT FOCUS: CONFIRM SELECTION & TOS]
        Room {closing_state.selected_stay.room_no} selected. Pricing: {closing_state.pricing.breakdown_text}
        Confirm the user is happy with the price, then use present_terms_of_service.
        If they want a different room, use select_room again.
        SOFT CLOSE: Guide toward TOS acceptance (e.g. "ถ้าราคาโอเคจะให้คูเปอร์ส่งเงื่อนไขการจองให้นะคะ")"""

    elif step == "tos_accepted":
        return """[YOUR CURRENT FOCUS: COLLECT GUEST INFO & PAYMENT]
        TOS accepted. Collect guest name + phone, then use accept_tos_and_show_payment.
        SOFT CLOSE: Ask for guest details (e.g. "ขอชื่อและเบอร์โทรสำหรับการจองค่ะ")"""

    elif step == "payment_presented":
        return f"""[YOUR CURRENT FOCUS: PAYMENT CONFIRMATION]
        Bank transfer details shown. Total: {closing_state.pricing.total_price} THB.
        Wait for user to confirm they've transferred. Then use submit_for_staff_confirmation.
        SOFT CLOSE: Gently ask if they've completed the transfer."""

    elif step == "booking_confirmed":
        return """[YOUR CURRENT FOCUS: BOOKING COMPLETE]
        Staff confirmed payment. Use create_booking_summary to show the final summary.
        Thank the guest warmly."""
```

**Key principle**: The agent can always use Q&A tools and compare_rooms regardless of step. The directive just tells it what to steer back to after handling the side question.

**Register all tools**: qa_tools + compare_rooms, select_room, present_terms_of_service, accept_tos_and_show_payment, submit_for_staff_confirmation, create_booking_summary, revise_criteria

---

## Step 5: Rewrite node wrapper with HITL interrupt

### `src/agent/closing/node.py`

```
async def closing_node(state, config):
    closing = state.get("closing_state") or ClosingState()

    # Run closer sub-graph
    result = await closer_graph.ainvoke(state, config=sub_config)
    updated_closing = extract closing_state from result

    # If agent reached "awaiting_staff", fire interrupt
    if updated_closing.closing_step == "awaiting_staff":
        staff_input = interrupt({booking details payload})

        if staff_input.get("confirmed"):
            updated_closing.staff_confirmed = True
            updated_closing.closing_step = "booking_confirmed"
            # Re-invoke agent to generate final summary
            result = await closer_graph.ainvoke(updated_state, config)
        else:
            updated_closing.closing_step = "payment_presented"
            # Agent will inform guest

    return {"closing_state": updated_closing, "messages": [...]}
```

---

## Naming changes summary

All references across the codebase:
- `room_evaluation_state` → `closing_state`
- `RoomEvaluationState` → `ClosingState`
- `room_evaluation_node` → `closing_node`
- `evaluate_options` phase → `closing` phase
- `room_evaluation_agent` (sub-graph node name) → `closing_agent`

---

## Files to modify

| File | Action |
|------|--------|
| `src/agent/rooms_searching/schema.py` | Add PriceBreakdownItem, ExtraBedInfo, StayPricing |
| `src/agent/types.py` | Fix import, rename to `closing_state: ClosingState`, simplify Phase |
| `src/agent/root_graph.py` | Fix import, rename node, phase_map, add checkpointer |
| `src/agent/closing/schema.py` | Rename to ClosingState, add ClosingStep, SelectedStay, PricingSummary |
| `src/agent/closing/tools/compare_rooms.py` | NEW — room comparison tool |
| `src/agent/closing/tools/booking_tools.py` | REWRITE — 5 booking tools |
| `src/agent/closing/tools/revise_crteria.py` | UPDATE — reset `closing_state` |
| `src/agent/closing/closer_agent.py` | REWRITE — dynamic prompt, register all tools |
| `src/agent/closing/node.py` | REWRITE — interrupt logic, use `closing_state` |
| `src/agent/rooms_searching/node.py` | Update phase value from `"evaluate_options"` → `"closing"` |

## Reuse existing code
- `src/agent/rooms_searching/pricing.py` — `calculate_stay_pricing()` for pricing in select_room tool
- `src/agent/services/room_service.py` — `RoomService.get_room_by_name()` for compare_rooms tool
- `src/agent/shared_tools/` — all Q&A tools (already imported in closer_agent.py)
- Tool pattern from `src/agent/criteria_discovery/tools/update_criteria.py` — `@tool` + `ToolRuntime` + `Command` return

## Verification
1. Run the agent end-to-end: criteria → search → closing
2. Test tool flow: compare rooms → select room → see pricing → TOS → accept + payment → submit for staff → resume with staff confirmation → booking summary
3. Test edge cases: change room after selection, revise criteria from closing, staff rejection
4. Verify interrupt works: graph pauses at `awaiting_staff`, resumes with staff input
5. Verify dynamic prompt: after answering a Q&A question, agent steers back to the current step's focus
