from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from sqlalchemy import select

from agent.schemas import ClosingState
from db.database import AsyncSessionLocal
from db.models import KnowledgeDocument


@tool
async def get_booking_terms_and_payment(
    runtime: ToolRuntime = None,
) -> Command:
    """Retrieve booking terms and conditions along with bank payment details.
    Call this immediately after a room has been selected and confirmed.
    """
    closing_state: ClosingState = runtime.state.get("closing_state") or ClosingState()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.key.in_(["booking_terms", "bank_payment_info"])
            )
        )
        docs = {doc.key: doc for doc in result.scalars().all()}

    parts = []

    terms_doc = docs.get("booking_terms")
    if terms_doc:
        parts.append(f"=== Booking Terms ===\n{terms_doc.content}")
    else:
        parts.append("=== Booking Terms ===\nBooking terms not available.")

    payment_doc = docs.get("bank_payment_info")
    if payment_doc:
        parts.append(f"=== Bank Payment Info ===\n{payment_doc.content}")
    else:
        parts.append("=== Bank Payment Info ===\nBank payment info not available.")

    # Update closing state with terms_and_payment_shown
    updated_state = closing_state.model_copy(update={"terms_and_payment_shown": True})

    return Command(
        update={
            "closing_state": updated_state,
            "messages": [
                ToolMessage(
                    content="\n\n".join(parts),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
