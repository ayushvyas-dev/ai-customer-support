from app.ai.agent import support_graph
from app.ai.schemas import Decision, SupportState
from app.guards import DEFAULT_ESCALATION_ACKNOWLEDGEMENT


def decide(thread: str, has_attachments: bool = False, thread_id: str | None = None) -> Decision:
    """Run the LangGraph Agentic RAG pipeline for one email thread."""
    t_id = thread_id or "default_thread"
    initial_state: SupportState = {
        "thread_text": thread,
        "has_attachments": has_attachments,
        "thread_id": t_id,
        "retry_count": 0,
        "max_retries": 2,
    }

    config = {"configurable": {"thread_id": t_id}}
    final_state = support_graph.invoke(initial_state, config=config)

    action = final_state.get("action", "reply")
    section = final_state.get("section", "other")
    reply = final_state.get("reply", "")
    if action == "escalate" and not reply.strip():
        reply = DEFAULT_ESCALATION_ACKNOWLEDGEMENT
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
        executed_tools=final_state.get("executed_tools", []),
    )
