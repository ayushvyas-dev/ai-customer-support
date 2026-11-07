"""Deterministic guardrail functions for the AI Customer Support Agent.

Implements:
1. Hallucination Prevention & Context Grounding Verification
2. Prompt Injection & Jailbreak Protection
3. PII (Personally Identifiable Information) Detection & Redaction
4. Business Rule & Unauthorized Commitment Enforcement
5. Output Validation & Escalation Standards
"""

import re
from email.utils import parseaddr
from typing import Any

# =====================================================================
# Constants & Defaults
# =====================================================================

DEFAULT_ESCALATION_ACKNOWLEDGEMENT = (
    "Thank you for contacting Nexa Mobile. We've received your message and forwarded "
    "it to our support team. A colleague will review your request and get back to "
    "you within one business day.\n\nNexa Mobile Support"
)

# Canonical company models & limits
VALID_MODELS = {"nexa one", "nexa one pro", "nexa lite"}
INVALID_MODELS = {"nexa ultra", "nexa max", "nexa fold", "nexa two", "nexa plus"}

# Common stopwords for document grading
STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "and", "or",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does",
    "did", "can", "could", "would", "should", "will", "i", "my", "you", "your",
    "we", "our", "it", "its", "this", "that", "what", "which", "how", "when",
    "where", "who", "hi", "hello", "please", "help", "thanks", "thank",
}


# =====================================================================
# 1. Skip Reason Guard (Pre-existing email filtering)
# =====================================================================

def skip_reason(message: dict, headers: dict[str, str], own_address: str) -> str | None:
    """Return why the bot must not answer this message, or None when it may."""
    if "SENT" in message.get("labelIds", []):
        return "sent by us"
    sender = parseaddr(headers.get("from", ""))[1].lower()
    if sender == own_address.lower():
        return "from our own address"
    if "noreply" in sender or "no-reply" in sender:
        return "noreply address"
    auto_submitted = headers.get("auto-submitted", "no").strip().lower()
    if auto_submitted != "no":
        return f"auto-submitted: {auto_submitted}"
    if headers.get("precedence", "").strip().lower() in {"bulk", "list", "junk"}:
        return "bulk or list mail"
    return None


# =====================================================================
# 2. PII Protection (Personally Identifiable Information)
# =====================================================================

def _luhn_checksum(card_number: str) -> bool:
    """Verify Luhn checksum for payment card numbers."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


# Matches standard card formatting (13-19 digits, possibly with spaces or dashes)
CARD_PATTERN = re.compile(
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12}|(?:[0-9]{4}[ -]?){3,4}[0-9]{1,4})\b"
)

# Amazon order number: 3 digits - 7 digits - 7 digits (MUST NOT be redacted as credit card)
AMAZON_ORDER_PATTERN = re.compile(r"\b\d{3}-\d{7}-\d{7}\b")

# CVV/CVC pattern
CVV_PATTERN = re.compile(
    r"(?i)\b(?:cvv|cvc|security\s*code|card\s*verification)\s*[:=]?\s*([0-9]{3,4})\b"
)

# Passwords & Secrets
PASSWORD_PATTERN = re.compile(
    r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"
)

# OTP / Verification Codes
OTP_PATTERN = re.compile(
    r"(?i)\b(?:otp|one-time\s*password|verification\s*code|auth\s*code)\s*[:=]?\s*([0-9]{4,8})\b"
)

# US SSN
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# API Keys / Tokens
API_KEY_PATTERN = re.compile(
    r"\b(?:gsk_[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z-_]{35}|sk-[a-zA-Z0-9]{20,})\b"
)


def _is_payment_card(raw: str, amazon_orders: set[str]) -> bool:
    """Check if number string is a payment card (excluding Amazon order IDs)."""
    if raw in amazon_orders:
        return False
    digits = re.sub(r"\D", "", raw)
    if not (13 <= len(digits) <= 19):
        return False
    # Match major card prefixes or valid Luhn checksum
    return digits[0] in "3456" or _luhn_checksum(digits)


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Detect presence of sensitive PII in text (cards, CVVs, passwords, OTPs, SSNs, API keys)."""
    findings = []

    # API Keys
    for m in API_KEY_PATTERN.finditer(text):
        findings.append({"type": "api_key", "value": m.group(0), "start": m.start(), "end": m.end()})

    # Passwords
    for m in PASSWORD_PATTERN.finditer(text):
        findings.append({"type": "password", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    # OTPs
    for m in OTP_PATTERN.finditer(text):
        findings.append({"type": "otp", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    # CVVs
    for m in CVV_PATTERN.finditer(text):
        findings.append({"type": "cvv", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    # SSNs
    for m in SSN_PATTERN.finditer(text):
        findings.append({"type": "ssn", "value": m.group(0), "start": m.start(), "end": m.end()})

    # Credit Cards (protect Amazon order IDs from being treated as cards)
    amazon_orders = set(AMAZON_ORDER_PATTERN.findall(text))
    for m in CARD_PATTERN.finditer(text):
        raw = m.group(0)
        if _is_payment_card(raw, amazon_orders):
            findings.append({"type": "credit_card", "value": raw, "start": m.start(), "end": m.end()})

    return findings


def mask_pii(text: str) -> str:
    """Mask sensitive PII in incoming emails or outbound replies to protect privacy."""
    if not text:
        return text

    # Mask API keys
    text = API_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)

    # Mask CVVs
    text = CVV_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_CVV]"), text)

    # Mask OTPs
    text = OTP_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_OTP]"), text)

    # Mask Passwords
    text = PASSWORD_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_PASSWORD]"), text)

    # Mask SSNs
    text = SSN_PATTERN.sub("[REDACTED_SSN]", text)

    # Mask Credit Cards (excluding Amazon order numbers)
    amazon_orders = set(AMAZON_ORDER_PATTERN.findall(text))

    def _replace_card(match: re.Match) -> str:
        raw = match.group(0)
        if _is_payment_card(raw, amazon_orders):
            return "[REDACTED_CREDIT_CARD]"
        return raw

    text = CARD_PATTERN.sub(_replace_card, text)
    return text


# =====================================================================
# 3. Prompt Injection Protection
# =====================================================================

INJECTION_PATTERNS = [
    # Direct instruction overrides
    re.compile(r"(?i)\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|prior|above|system)?\s*(?:instructions|prompts|rules|guidelines|directives)"),
    re.compile(r"(?i)\b(?:new\s+instructions?|system\s+override|admin\s+override)\s*[:=]"),
    re.compile(r"(?i)\b(?:you\s+are\s+now\s+(?:in\s+)?(?:developer\s+mode|dan|unrestricted|jailbreak)|act\s+as\s+(?:dan|an?\s+unrestricted|an?\s+evil)|\bdan\b.*do\s+anything\s+now|developer\s+mode|jailbreak\s+mode)\b"),
    # Tag injections and breakout attempts
    re.compile(r"(?i)<\/?(?:system|instruction|prompt|untrusted_customer_thread|knowledge_base_context)>"),
    re.compile(r"(?i)(?:\[INST\]|\[\/INST\]|<<SYS>>|<\/s>|<\|im_start\|>|<\|im_end\|>)"),
    # Role hijacking & fake dialog continuations
    re.compile(r"(?i)\n\s*(?:system|assistant|admin)\s*:\s*"),
    # Instruction extraction & prompt exfiltration
    re.compile(r"(?i)\b(?:print|repeat|reveal|display|output|echo)\s+(?:the\s+|your\s+)?(?:text\s+above|words\s+above|everything\s+above|system\s+prompt|initial\s+instructions|system\s+instructions|secret\s+prompt)\b"),
    re.compile(r"(?i)\bwhat\s+(?:are|were)\s+your\s+(?:exact\s+)?(?:instructions|prompts|rules|initial\s+prompt)"),
    # Policy override attempts
    re.compile(r"(?i)\b(?:bypass|ignore)\s+(?:company\s+)?(?:policy|policies|rules|guardrails|safeguards)"),
]


def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """Deterministically detect prompt injection, jailbreak, or system override attempts."""
    if not text:
        return False, ""

    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Prompt injection pattern detected: '{match.group(0)}'"

    return False, ""


def sanitize_for_prompt(text: str) -> str:
    """Sanitize customer input by stripping fake boundary tags and neutralizing injection tokens."""
    if not text:
        return ""
    # Strip potential XML/boundary tag injection
    sanitized = re.sub(
        r"(?i)<\/?(?:system|untrusted_customer_thread|knowledge_base_context|instruction)>",
        "",
        text,
    )
    # Strip special chat template tokens
    sanitized = re.sub(
        r"(?:\[INST\]|\[\/INST\]|<<SYS>>|<\/s>|<\|im_start\|>|<\|im_end\|>)",
        "",
        sanitized,
    )
    return sanitized.strip()


# =====================================================================
# 4. Hallucination Prevention & Context Grounding
# =====================================================================

def grade_documents(query: str, docs: list[str]) -> bool:
    """Grade whether retrieved documents contain relevant terms matching customer query."""
    if not docs:
        return False

    total_text = "\n".join(docs).lower()
    if len(total_text.strip()) < 50:
        return False

    # Extract meaningful keywords from query (length > 2, not in stopwords)
    query_words = re.findall(r"\b[a-z0-9_-]{3,}\b", query.lower())
    content_words = [w for w in query_words if w not in STOPWORDS]

    if not content_words:
        # If no significant content words, check if docs have reasonable body
        return len(total_text) > 100

    # Check for keyword overlap
    matches = sum(1 for w in content_words if w in total_text)
    match_ratio = matches / len(content_words)

    # If at least 25% of significant query words match, or >= 2 words match
    return matches >= 2 or match_ratio >= 0.25


def verify_grounding(reply: str, retrieved_docs: list[str], section: str) -> tuple[bool, str]:
    """Verify that generated reply does not contain factual hallucinations or invented policies."""
    reply_lower = reply.lower()
    docs_text = "\n".join(retrieved_docs).lower()

    # 1. Check for invented warranty periods
    # Factual: 1-year on smartphones, 6-month on accessories
    fake_warranties = [
        "2 year warranty", "2-year warranty", "two year warranty", "two-year warranty",
        "3 year warranty", "3-year warranty", "three year warranty",
        "lifetime warranty", "5 year warranty", "5-year warranty"
    ]
    for fw in fake_warranties:
        if fw in reply_lower:
            return False, f"Hallucinated warranty duration: '{fw}'"

    # 2. Check for false coverage claims
    # Factual: Liquid damage, accidental drops, cracked screens are excluded
    false_coverages = [
        "water damage is covered", "liquid damage is covered",
        "cracked screen is covered", "screen crack is covered",
        "accidental damage is covered", "drop damage is covered",
    ]
    for fc in false_coverages:
        if fc in reply_lower:
            return False, f"False warranty coverage assertion: '{fc}'"

    # 3. Check for invented return periods
    # Factual: Amazon 30-day return window
    fake_return_windows = [
        "60 day return", "60-day return", "90 day return", "90-day return",
        "45 day return", "45-day return", "14 day return for phones",
    ]
    for fr in fake_return_windows:
        if fr in reply_lower:
            return False, f"Hallucinated return window: '{fr}'"

    # 4. Check for invented phone models
    for im in INVALID_MODELS:
        if im in reply_lower:
            return False, f"Hallucinated product model: '{im}'"

    return True, ""


# =====================================================================
# 5. Business Rule Enforcement (Unauthorized Commitments)
# =====================================================================

UNAUTHORIZED_COMMITMENT_PATTERNS = [
    # Refund commitments
    (
        re.compile(
            r"(?i)\b(?:refund\s+(?:has\s+been|is|will\s+be)\s+(?:issued|processed|approved|initiated|granted|sent)|"
            r"(?:i|we)\s+(?:will|have|shall)\s+(?:issue|issued|process|processed|approve|approved|send|sent|grant|granted|refund(?:ed)?)\s+(?:a\s+|your\s+|the\s+)?(?:full\s+|partial\s+)?refund|"
            r"(?:i|we)\s+(?:will|have|shall)\s+refund\s+(?:the\s+amount|your\s+money|everything)|"
            r"(?:i|we)\s+(?:will|have)\s+credit(?:ed)?\s+(?:your\s+card|your\s+account|the\s+amount)|"
            r"(?:full\s+|partial\s+)?refund\s+(?:is\s+on\s+its\s+way|will\s+be\s+credited))\b"
        ),
        "Unauthorized refund promise",
    ),
    # Discount / Promo / Coupon commitments
    (
        re.compile(
            r"(?i)\b(?:discount\s+code|coupon\s+code|promo\s+code|voucher\s+code)\s*[:=]?\s*[\"']?[A-Z0-9_-]{3,}[\"']?|"
            r"(?:here\s+is|use\s+code|apply\s+code)\s*[:=]?\s*[\"']?[A-Z0-9_-]{4,}[\"']?|"
            r"(?:100%|50%|25%|[0-9]+%)\s*(?:off|discount|voucher)|"
            r"free\s+credit\s+of\b"
        ),
        "Unauthorized discount or promotional code promise",
    ),
    # Order cancellation commitments
    (
        re.compile(
            r"(?i)\b(?:(?:i|we)\s+(?:have|will|shall)\s+cancel(?:led)?\s+(?:your|the)\s+order|"
            r"order\s+(?:has\s+been|is)\s+cancel(?:led)?|"
            r"cancellation\s+(?:has\s+been|is)\s+confirmed)\b"
        ),
        "Unauthorized order cancellation commitment",
    ),
    # Replacement / Free hardware commitments
    (
        re.compile(
            r"(?i)\b(?:(?:i|we)\s+(?:will|have|shall)\s+send(?:ing)?\s+(?:you\s+)?(?:a\s+)?free\s+replacement|"
            r"replacement\s+(?:phone|device|unit|accessory)\s+(?:is\s+on\s+the\s+way|has\s+been\s+dispatched|will\s+be\s+shipped)|"
            r"(?:dispatching|shipping)\s+(?:you\s+)?a\s+(?:new|free)\s+(?:phone|device|charger|replacement))\b"
        ),
        "Unauthorized replacement hardware commitment",
    ),
    # Callback / Telephone commitments
    (
        re.compile(
            r"(?i)\b(?:(?:i|we|a\s+colleague|someone|our\s+(?:support\s+)?team|a\s+manager)\s+(?:will|shall|can)\s+call\s+you|"
            r"calling\s+you\s+(?:at|on|tomorrow|shortly)|"
            r"arrange\s+a\s+(?:phone\s+)?call|"
            r"reach\s+out\s+by\s+phone)\b"
        ),
        "Unauthorized telephone callback commitment",
    ),
    # Repair approval commitments without inspection
    (
        re.compile(
            r"(?i)\b(?:warranty\s+claim\s+(?:is|has\s+been)\s+approved|"
            r"(?:we|i)\s+will\s+repair\s+your\s+device\s+for\s+free|"
            r"free\s+repair\s+is\s+approved)\b"
        ),
        "Unauthorized warranty repair approval commitment",
    ),
]


def detect_unauthorized_commitments(reply: str) -> tuple[bool, str]:
    """Deterministically check if a reply makes unauthorized business commitments."""
    if not reply:
        return False, ""

    for pattern, description in UNAUTHORIZED_COMMITMENT_PATTERNS:
        match = pattern.search(reply)
        if match:
            return True, f"{description}: '{match.group(0)}'"

    return False, ""


# =====================================================================
# 6. Output Validation & Quality
# =====================================================================

FORBIDDEN_TERMS_PATTERN = re.compile(
    r"(?i)\b(AI|artificial\s+intelligence|ChatGPT|OpenAI|Anthropic|LLM|language\s+model|system\s+prompt|knowledge\s+base)\b"
)

PLACEHOLDER_PATTERN = re.compile(
    r"(?:\[(?:Insert|Your|Customer|Order|Phone|Date|Name|Here)[^\]]*\]|\{(?:name|customer|order|date)\}|\bTODO\b|\bTBD\b)"
)


def validate_output(reply: str) -> tuple[bool, str]:
    """Validate that the generated response satisfies quality, formatting, and safety standards."""
    if not reply or len(reply.strip()) < 15:
        return False, "Reply is too short or empty"

    # Check for unresolved template placeholders
    placeholder_match = PLACEHOLDER_PATTERN.search(reply)
    if placeholder_match:
        return False, f"Unresolved placeholder detected: '{placeholder_match.group(0)}'"

    # Check for sensitive PII leaks in outbound reply
    detected_pii = detect_pii(reply)
    if detected_pii:
        return False, f"Outbound reply contains sensitive PII: {[d['type'] for d in detected_pii]}"

    return True, ""


def sanitize_output(reply: str) -> str:
    """Sanitize reply to remove forbidden internal mentions and ensure corporate sign-off."""
    if not reply:
        return reply

    # Replace forbidden terms like "AI" or "knowledge base"
    cleaned = FORBIDDEN_TERMS_PATTERN.sub("support team", reply)

    # Ensure clean sign-off
    required_signoff = "Nexa Mobile Support"
    if required_signoff not in cleaned:
        cleaned = cleaned.rstrip() + f"\n\n{required_signoff}"

    return cleaned
