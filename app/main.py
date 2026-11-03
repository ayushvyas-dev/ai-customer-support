import base64
import hashlib
import hmac
import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import db
from app.config import settings

app = FastAPI(title="AI customer support")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Token Auth helpers
def get_secret() -> bytes:
    return (settings.dashboard_password or "support-automation-default-secret").encode()


def create_token(username: str) -> str:
    ts = str(int(time.time()))
    payload = f"{username}:{ts}".encode()
    sig = hmac.new(get_secret(), payload, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{username}:{ts}:{sig}".encode()).decode()


def verify_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    parts = authorization.split(" ")
    token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization

    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        username, ts_str, sig = decoded.split(":", 2)
        ts = int(ts_str)
        # expire in 7 days
        if time.time() - ts > 7 * 86400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired, please login again",
            )
        expected = hmac.new(get_secret(), f"{username}:{ts_str}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token",
            )
        return username
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


class LoginRequest(BaseModel):
    username: str
    password: str


class TicketStatusUpdate(BaseModel):
    status: str
    category: str | None = None
    proposed_action: str | None = None


class KnowledgeBaseEntryRequest(BaseModel):
    section: str
    title: str
    content: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Auth endpoints
@app.post("/api/auth/login")
def login(req: LoginRequest) -> dict:
    valid_user = settings.dashboard_username or "admin"
    valid_pass = settings.dashboard_password or ""

    # allow matching password or blank if not set
    if req.username != valid_user or (valid_pass and req.password != valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_token(req.username)
    return {
        "token": token,
        "username": req.username,
        "authenticated": True,
    }


@app.get("/api/auth/me")
def me(username: Annotated[str, Depends(verify_token)]) -> dict:
    return {"username": username, "authenticated": True}


# Events endpoints
@app.get("/api/events")
def list_events(
    username: Annotated[str, Depends(verify_token)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    search: str | None = None,
) -> dict:
    items, total = db.get_events(limit=limit, offset=offset, status=status, search=search)
    stats = db.get_events_stats()
    return {"items": items, "total": total, "stats": stats}


@app.get("/api/events/{event_id}")
def get_event(
    event_id: int,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# Tickets endpoints
@app.get("/api/tickets")
def list_tickets(
    username: Annotated[str, Depends(verify_token)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    search: str | None = None,
) -> dict:
    items, total = db.get_tickets(limit=limit, offset=offset, status=status, search=search)
    stats = db.get_tickets_stats()
    return {"items": items, "total": total, "stats": stats}


@app.get("/api/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = db.get_ticket_messages(ticket_id)
    return {"ticket": ticket, "messages": messages}


@app.patch("/api/tickets/{ticket_id}")
def update_ticket(
    ticket_id: int,
    update: TicketStatusUpdate,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if update.status not in ["open", "answered", "escalated"]:
        raise HTTPException(status_code=400, detail="Invalid ticket status")

    db.update_ticket(
        ticket_id=ticket_id,
        status=update.status,
        category=update.category,
        proposed_action=update.proposed_action,
    )
    return {"status": "ok", "id": ticket_id, "ticket_status": update.status}


# Knowledge base endpoints
@app.get("/api/knowledge-base")
def list_knowledge_base(
    username: Annotated[str, Depends(verify_token)],
    section: str | None = None,
    search: str | None = None,
) -> dict:
    items = db.get_knowledge_base_entries(section=section, search=search)
    sections = db.list_sections()
    return {"items": items, "sections": sections}


@app.get("/api/knowledge-base/sections")
def list_sections(
    username: Annotated[str, Depends(verify_token)],
) -> list[str]:
    return db.list_sections()


@app.post("/api/knowledge-base")
def create_or_update_knowledge_base_entry(
    entry: KnowledgeBaseEntryRequest,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    entry_id = db.upsert_knowledge_base_entry(
        section=entry.section.strip(),
        title=entry.title.strip(),
        content=entry.content.strip(),
    )
    return {"id": entry_id, "status": "saved"}


@app.put("/api/knowledge-base/{entry_id}")
def update_knowledge_base_entry(
    entry_id: int,
    entry: KnowledgeBaseEntryRequest,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    existing = db.get_knowledge_base_entry(entry_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    saved_id = db.upsert_knowledge_base_entry(
        section=entry.section.strip(),
        title=entry.title.strip(),
        content=entry.content.strip(),
        entry_id=entry_id,
    )
    return {"id": saved_id, "status": "updated"}


@app.delete("/api/knowledge-base/{entry_id}")
def delete_knowledge_base_entry(
    entry_id: int,
    username: Annotated[str, Depends(verify_token)],
) -> dict:
    success = db.delete_knowledge_base_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted", "id": entry_id}
