from typing import Literal, TypedDict

from pydantic import BaseModel, Field

Section = Literal["smartphone", "accessories", "returns-and-warranty", "shipping", "other"]


class Classification(BaseModel):
    section: Section
    language: str = Field(description="Language of the latest customer message, e.g. English")
    needs_human: bool = Field(description="True when an always-escalate rule applies")
    reason: str = Field(description="One sentence explaining the classification")
    acknowledgement: str = Field(
        description="Short note to the customer, in their language, that a colleague replies"
    )


class Issue(BaseModel):
    product: Literal["smartphone", "accessories"]
    problem: Literal[
        "slow-charging",
        "battery-drain",
        "safety-hazard",
        "display-issue",
        "camera-issue",
        "performance-lag",
        "connectivity-issue",
        "physical-damage",
        "not-turning-on",
        "missing-accessory",
        "damaged-accessory",
        "incompatible-accessory",
    ]
    model: str | None = None
    order_number: str | None = None
    purchase_date: str | None = None
    days_since_delivery: int | None = None
    troubleshooting_attempted: bool = Field(default=False)
    safety_risk: bool = Field(default=False)


class AgentReply(BaseModel):
    action: Literal["reply", "escalate"]
    reply: str = Field(description="The email to the customer, plain text")
    reasoning: str = Field(description="Which knowledge base entries you used, and why")
    enough_information: bool = Field(description="True when the knowledge base answers the question")
    promises_an_action: bool = Field(
        description="True when the reply promises a refund, shipment, replacement, date, or call"
    )
    issue: Issue | None = Field(
        default=None, description="Fill in when the customer reports a problem with a product"
    )


class Decision(BaseModel):
    action: Literal["reply", "escalate"]
    section: str
    reply: str
    reason: str
    proposed_action: str | None = None


class SupportState(TypedDict, total=False):
    # Inputs
    thread_text: str
    has_attachments: bool
    message_id: str
    thread_id: str
    sender_email: str
    subject: str

    # Classification
    section: str
    language: str
    needs_human: bool
    classification_reason: str
    acknowledgement: str

    # RAG / Retrieval
    customer_query: str
    retrieved_docs: list[str]
    docs_relevant: bool

    # Agent Generation
    reply: str
    reasoning: str
    enough_information: bool
    promises_an_action: bool
    issue: dict | None

    # Decision Output
    action: Literal["reply", "escalate"]
    escalation_reason: str | None
    proposed_action: str | None

    # Control Flow
    retry_count: int
    max_retries: int
