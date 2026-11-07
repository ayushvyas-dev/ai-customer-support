import logging
import os
import re
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.ai.classifier import classify
from app.ai.rules import CUSTOMER_STEPS, resolve_issue
from app.ai.schemas import AgentReply, Issue, SupportState
from app.config import settings
from app.vectorstore import search_similar

logger = logging.getLogger(__name__)

INSTRUCTIONS = """
You are the customer support agent for Nexa Mobile, a customer-focused smartphone brand that sells on Amazon.
You write the answer to the latest customer message in the email thread using the provided Knowledge Base context.

Guidelines:
1. Answer only using verified facts from the Knowledge Base context. If the provided context does not contain enough information to answer the inquiry, set enough_information to false.
2. When the customer reports a problem with a smartphone or an accessory, fill in issue.
   - Ask for the model, order number, and purchase date when missing.
   - For safety issues (swelling, smoke, burning, dangerous overheating), immediately tell them to disconnect and stop using the device safely, and set action to escalate.
   - Guide basic troubleshooting (cable checks, restart, 30-min charge test for unresponsiveness) unless the customer already attempted it.
3. Never promise a refund, a shipment, a replacement, a repair date, or a call. A colleague arranges those.
   Set promises_an_action to true if your reply promises one anyway.
4. Set action to escalate when an escalation rule applies or when information is insufficient.

Reply formatting rules:
- Write in the language of the customer's latest message.
- Plain text only, no Markdown formatting.
- Follow the brand-and-tone guidance (friendly, calm, clear, under 150 words).
- Sign off with:
Nexa Mobile Support
- Never mention AI, bots, tools, prompts, or the knowledge base.
"""


def get_agent_llm():
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    return ChatGoogleGenerativeAI(
        model=settings.agent_model,
        temperature=0.1,
        google_api_key=api_key,
        api_version="v1beta",
    )


# --- Node Definitions ---


def classify_node(state: SupportState) -> dict:
    thread = state.get("thread_text", "")
    classification = classify(thread)
    return {
        "section": classification.section,
        "language": classification.language,
        "needs_human": classification.needs_human,
        "classification_reason": classification.reason,
        "acknowledgement": classification.acknowledgement,
        "customer_query": thread,
    }


def retrieve_docs_node(state: SupportState) -> dict:
    query = state.get("customer_query") or state.get("thread_text", "")
    section = state.get("section", "other")
    retrieved = search_similar(query=query, section=section, top_k=4)
    return {"retrieved_docs": retrieved}


def grade_docs_node(state: SupportState) -> dict:
    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"docs_relevant": False}
    # Check if retrieved docs contain substantial information
    total_text = "\n".join(docs)
    return {"docs_relevant": len(total_text) > 100}


def rewrite_and_retrieve_node(state: SupportState) -> dict:
    llm = get_agent_llm()
    query = state.get("customer_query") or state.get("thread_text", "")
    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Extract the core technical or policy question from this customer email for knowledge base search. Keep it concise.",
            ),
            ("human", "{query}"),
        ]
    )
    chain = rewrite_prompt | llm
    rewritten = chain.invoke({"query": query}).content
    section = state.get("section", "other")
    retrieved = search_similar(query=str(rewritten), section=section, top_k=4)
    return {
        "customer_query": str(rewritten),
        "retrieved_docs": retrieved,
        "docs_relevant": True,
    }


def generate_reply_node(state: SupportState) -> dict:
    llm = get_agent_llm()
    structured_llm = llm.with_structured_output(AgentReply)
    docs_text = "\n\n".join(state.get("retrieved_docs", []))
    thread = state.get("thread_text", "")
    section = state.get("section", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INSTRUCTIONS),
            (
                "human",
                "Section: {section}\n\nKnowledge Base Context:\n{context}\n\nCustomer Thread:\n{thread}",
            ),
        ]
    )
    chain = prompt | structured_llm
    output: AgentReply = chain.invoke(
        {"section": section, "context": docs_text, "thread": thread}
    )

    issue_dict = output.issue.model_dump() if output.issue else None
    return {
        "reply": output.reply,
        "reasoning": output.reasoning,
        "enough_information": output.enough_information,
        "promises_an_action": output.promises_an_action,
        "issue": issue_dict,
        "action": output.action,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def validate_reply_node(state: SupportState) -> dict:
    reply = state.get("reply", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    # Empty reply check
    if state.get("action") == "reply" and not reply.strip():
        if retry_count < max_retries:
            return {"action": "reply"}
        return {
            "action": "escalate",
            "escalation_reason": "Reply was empty after max retries",
        }

    # Forbidden mention check
    if re.search(r"\b(AI|artificial intelligence|knowledge base)\b", reply, re.IGNORECASE):
        cleaned_reply = re.sub(
            r"\b(AI|artificial intelligence|knowledge base)\b",
            "support team",
            reply,
            flags=re.IGNORECASE,
        )
        return {"reply": cleaned_reply}

    return {}


def apply_rules_node(state: SupportState) -> dict:
    # 1. Attachment escalation
    if state.get("has_attachments"):
        return {
            "action": "escalate",
            "escalation_reason": "The email has attachments",
            "reply": state.get("acknowledgement") or state.get("reply", ""),
        }

    # 2. Classifier needs human
    if state.get("needs_human"):
        return {
            "action": "escalate",
            "escalation_reason": state.get("classification_reason", "Needs human assistance"),
            "reply": state.get("acknowledgement") or state.get("reply", ""),
        }

    # 3. Agent action escalation
    if state.get("action") == "escalate":
        return {
            "action": "escalate",
            "escalation_reason": state.get("reasoning", "Agent escalated"),
            "reply": state.get("acknowledgement") or state.get("reply", ""),
        }

    # 4. Insufficient information
    if not state.get("enough_information", True):
        return {
            "action": "escalate",
            "escalation_reason": "The knowledge base does not answer this",
            "reply": state.get("acknowledgement") or state.get("reply", ""),
        }

    # 5. Promises an action
    if state.get("promises_an_action"):
        return {
            "action": "escalate",
            "escalation_reason": "The reply promises an action",
            "reply": state.get("acknowledgement") or state.get("reply", ""),
        }

    # 6. Issue resolution rule engine
    issue_dict = state.get("issue")
    if issue_dict:
        try:
            issue_obj = Issue.model_validate(issue_dict)
            step = resolve_issue(issue_obj)
            if step not in CUSTOMER_STEPS:
                return {
                    "action": "escalate",
                    "escalation_reason": f"Next step: {step}",
                    "proposed_action": step,
                    "reply": state.get("acknowledgement") or state.get("reply", ""),
                }
        except Exception as e:
            logger.warning("Error evaluating issue rules: %s", e)

    return {"action": "reply"}


def send_reply_node(state: SupportState) -> dict:
    return {"action": "reply"}


def escalate_node(state: SupportState) -> dict:
    return {
        "action": "escalate",
        "reply": state.get("acknowledgement") or state.get("reply", ""),
    }


# --- Conditional Routing ---


def route_after_classify(state: SupportState) -> Literal["escalate", "retrieve_docs"]:
    if state.get("has_attachments") or state.get("needs_human"):
        return "escalate"
    return "retrieve_docs"


def route_after_grade(state: SupportState) -> Literal["generate_reply", "rewrite_and_retrieve"]:
    if state.get("docs_relevant"):
        return "generate_reply"
    return "rewrite_and_retrieve"


def route_after_validate(state: SupportState) -> Literal["apply_rules", "generate_reply", "escalate"]:
    reply = state.get("reply", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if not reply.strip():
        if retry_count < max_retries:
            return "generate_reply"
        return "escalate"

    return "apply_rules"


def route_after_rules(state: SupportState) -> Literal["send_reply", "escalate"]:
    if state.get("action") == "escalate":
        return "escalate"
    return "send_reply"


# --- Build LangGraph Pipeline ---


def build_support_graph():
    workflow = StateGraph(SupportState)

    workflow.add_node("classify", classify_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("grade_docs", grade_docs_node)
    workflow.add_node("rewrite_and_retrieve", rewrite_and_retrieve_node)
    workflow.add_node("generate_reply", generate_reply_node)
    workflow.add_node("validate_reply", validate_reply_node)
    workflow.add_node("apply_rules", apply_rules_node)
    workflow.add_node("send_reply", send_reply_node)
    workflow.add_node("escalate", escalate_node)

    workflow.set_entry_point("classify")

    workflow.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "escalate": "escalate",
            "retrieve_docs": "retrieve_docs",
        },
    )

    workflow.add_edge("retrieve_docs", "grade_docs")

    workflow.add_conditional_edges(
        "grade_docs",
        route_after_grade,
        {
            "generate_reply": "generate_reply",
            "rewrite_and_retrieve": "rewrite_and_retrieve",
        },
    )

    workflow.add_edge("rewrite_and_retrieve", "generate_reply")
    workflow.add_edge("generate_reply", "validate_reply")

    workflow.add_conditional_edges(
        "validate_reply",
        route_after_validate,
        {
            "apply_rules": "apply_rules",
            "generate_reply": "generate_reply",
            "escalate": "escalate",
        },
    )

    workflow.add_conditional_edges(
        "apply_rules",
        route_after_rules,
        {
            "send_reply": "send_reply",
            "escalate": "escalate",
        },
    )

    workflow.add_edge("send_reply", END)
    workflow.add_edge("escalate", END)

    return workflow.compile()


support_graph = build_support_graph()
