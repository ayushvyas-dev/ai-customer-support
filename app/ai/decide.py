from app.ai.agent import support_graph
from app.ai.schemas import Decision, SupportState


def decide(thread: str, has_attachments: bool = False) -> Decision:
    """Run the LangGraph Agentic RAG pipeline for one email thread."""
    initial_state: SupportState = {
        "thread_text": thread,
        "has_attachments": has_attachments,
        "retry_count": 0,
        "max_retries": 2,
    }

    final_state = support_graph.invoke(initial_state)

    action = final_state.get("action", "reply")
    section = final_state.get("section", "other")
    reply = final_state.get("reply", "")
    reason = (
        final_state.get("escalation_reason")
        or final_state.get("reasoning")
        or final_state.get("classification_reason")
        or ""
    )
    proposed_action = final_state.get("proposed_action")

    return Decision(
        action=action,
        section=section,
        reply=reply,
        reason=reason,
        proposed_action=proposed_action,
    )
