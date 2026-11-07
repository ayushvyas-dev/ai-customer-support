# AI Customer Support Agent — Refactoring Spec

## Goal

Refactor the AI Customer Support project from **pydantic-ai + polling** to **LangChain/LangGraph + Gmail Pub/Sub webhooks**, implementing a production-grade agentic RAG pipeline for automated email customer support for **Nexa Mobile**.

---

## Architecture Overview

### Current Flow
```
Gmail Inbox → Poller (30s loop) → Guards → Classifier (pydantic-ai) → Agent (pydantic-ai + tool calls) → Rules → Send Reply
```

### Target Flow
```
Gmail Inbox → Cloud Pub/Sub → Webhook POST → Guards → LangGraph Pipeline [Classify → Route → RAG Retrieve → Grade Docs → Generate Reply → Validate → Apply Rules] → Send Reply
```

---

## Current State vs. Target State

| Aspect | Current (pydantic-ai + Poller) | Target (LangChain/LangGraph + Webhook) |
|---|---|---|
| **LLM Framework** | `pydantic-ai` (Agent, ModelRetry, RunContext) | `langchain` + `langgraph` |
| **Email Trigger** | `poller.py` — `time.sleep()` loop every 30s | Gmail Pub/Sub → webhook `POST /webhook/gmail` |
| **Classifier** | `pydantic-ai.Agent` with structured output | LangChain `ChatGroq` with `with_structured_output()` |
| **Support Agent** | `pydantic-ai.Agent` with tool calls (`get_section`, `list_sections`) | LangGraph `StateGraph` with RAG retriever node |
| **RAG** | Manual: agent calls `get_section()` tool → full section text | Vector embeddings in pgvector, semantic similarity search |
| **Decision Logic** | `decide.py` — Python if/else tree | LangGraph conditional edges + rule engine node |
| **Output Validation** | `@support_agent.output_validator` decorator | LangGraph validator node with retry edge |
| **Knowledge Base** | Plain DB rows, agent fetches entire sections | Embedded into vector store, semantic retrieval |
| **Watch Renewal** | N/A (polling) | Background task to re-call `users.watch()` every 6 days |
| **Database** | `psycopg` raw SQL | `psycopg` raw SQL (unchanged) |
| **Dashboard** | Next.js 16 + Tailwind | Unchanged |

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|---|---|---|
| Web Framework | **FastAPI** | REST API + webhook receiver |
| LLM Orchestration | **LangChain** + **LangGraph** | Agent pipeline, state machine |
| Classifier LLM | **ChatGroq** (`gpt-oss-120b`) | Email classification with structured output |
| Agent LLM | **ChatGoogleGenerativeAI** (`gemini-3.6-flash`) | Response generation |
| Embeddings | **GoogleGenerativeAIEmbeddings** (`models/text-embedding-004`) | KB vectorization |
| Vector Store | **Supabase pgvector** | Semantic document retrieval |
| Database | **PostgreSQL** (Supabase) + `psycopg` | Events, tickets, messages, knowledge_base |
| Gmail Integration | **google-api-python-client** | Read/send emails, webhook watch |
| Gmail Trigger | **Google Cloud Pub/Sub** push subscription | Real-time email notifications |
| Background Tasks | **FastAPI BackgroundTasks** / `asyncio` | Async email processing, watch renewal |
| Config | **pydantic-settings** | Environment variable management |

### Frontend (unchanged)
| Component | Technology |
|---|---|
| Framework | **Next.js 16** (App Router) |
| Styling | **Tailwind CSS 4** |
| UI Components | Custom (shadcn-style) |
| Icons | **lucide-react** |

---

## Database Schema

### Existing Tables (no changes)

#### `events`
| Column | Type | Constraints |
|---|---|---|
| `id` | `bigint` | PK, auto-generated identity |
| `gmail_message_id` | `text` | NOT NULL, UNIQUE |
| `status` | `text` | NOT NULL, default `'processing'`, CHECK (`processing`, `processed`, `skipped`, `failed`) |
| `attempts` | `int` | NOT NULL, default `1` |
| `error` | `text` | nullable |
| `result` | `jsonb` | nullable |
| `created_at` | `timestamptz` | NOT NULL, default `now()` |
| `processed_at` | `timestamptz` | nullable |

#### `tickets`
| Column | Type | Constraints |
|---|---|---|
| `id` | `bigint` | PK, auto-generated identity |
| `gmail_thread_id` | `text` | NOT NULL, UNIQUE |
| `customer_email` | `text` | NOT NULL |
| `subject` | `text` | NOT NULL, default `''` |
| `category` | `text` | nullable |
| `status` | `text` | NOT NULL, default `'open'`, CHECK (`open`, `answered`, `escalated`) |
| `proposed_action` | `text` | nullable |
| `created_at` | `timestamptz` | NOT NULL, default `now()` |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` |

#### `messages`
| Column | Type | Constraints |
|---|---|---|
| `id` | `bigint` | PK, auto-generated identity |
| `ticket_id` | `bigint` | NOT NULL, FK → `tickets(id)` ON DELETE CASCADE |
| `gmail_message_id` | `text` | NOT NULL, UNIQUE |
| `direction` | `text` | NOT NULL, CHECK (`in`, `out`) |
| `from_address` | `text` | NOT NULL |
| `body` | `text` | NOT NULL |
| `created_at` | `timestamptz` | NOT NULL, default `now()` |

#### `knowledge_base`
| Column | Type | Constraints |
|---|---|---|
| `id` | `bigint` | PK, auto-generated identity |
| `section` | `text` | NOT NULL |
| `title` | `text` | NOT NULL |
| `content` | `text` | NOT NULL |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` |
| | | UNIQUE(`section`, `title`) |

### New Tables

#### `knowledge_base_embeddings`
| Column | Type | Constraints |
|---|---|---|
| `id` | `bigint` | PK, auto-generated identity |
| `knowledge_base_id` | `bigint` | NOT NULL, FK → `knowledge_base(id)` ON DELETE CASCADE |
| `chunk_index` | `int` | NOT NULL, default `0` |
| `chunk_text` | `text` | NOT NULL |
| `embedding` | `vector(768)` | NOT NULL |
| `metadata` | `jsonb` | default `'{}'` |
| `created_at` | `timestamptz` | NOT NULL, default `now()` |

#### `gmail_watch_state`
| Column | Type | Constraints |
|---|---|---|
| `id` | `int` | PK, default `1` (singleton row) |
| `history_id` | `bigint` | NOT NULL |
| `expiration` | `bigint` | NOT NULL |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` |

---

## API Endpoints

### Existing Endpoints (unchanged)

| Method | Path | Auth | Request Body | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/health` | None | — | `{ "status": "ok" }` | Health check |
| `POST` | `/api/auth/login` | None | `{ "username": str, "password": str }` | `{ "token": str, "username": str, "authenticated": true }` | Dashboard login |
| `GET` | `/api/auth/me` | Bearer | — | `{ "username": str, "authenticated": true }` | Verify session |
| `GET` | `/api/events` | Bearer | Query: `limit`, `offset`, `status`, `search` | `{ "items": [...], "total": int, "stats": {...} }` | List events |
| `GET` | `/api/events/{event_id}` | Bearer | — | Event object | Get single event |
| `GET` | `/api/tickets` | Bearer | Query: `limit`, `offset`, `status`, `search` | `{ "items": [...], "total": int, "stats": {...} }` | List tickets |
| `GET` | `/api/tickets/{ticket_id}` | Bearer | — | `{ "ticket": {...}, "messages": [...] }` | Get ticket + messages |
| `PATCH` | `/api/tickets/{ticket_id}` | Bearer | `{ "status": str, "category"?: str, "proposed_action"?: str }` | `{ "status": "ok", "id": int, "ticket_status": str }` | Update ticket status |
| `GET` | `/api/knowledge-base` | Bearer | Query: `section`, `search` | `{ "items": [...], "sections": [...] }` | List KB entries |
| `GET` | `/api/knowledge-base/sections` | Bearer | — | `["section1", ...]` | List sections |
| `POST` | `/api/knowledge-base` | Bearer | `{ "section": str, "title": str, "content": str }` | `{ "id": int, "status": "saved" }` | Create KB entry |
| `PUT` | `/api/knowledge-base/{entry_id}` | Bearer | `{ "section": str, "title": str, "content": str }` | `{ "id": int, "status": "updated" }` | Update KB entry |
| `DELETE` | `/api/knowledge-base/{entry_id}` | Bearer | — | `{ "status": "deleted", "id": int }` | Delete KB entry |

### New Endpoints

| Method | Path | Auth | Request Body | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/webhook/gmail` | Pub/Sub verification | `{ "message": { "data": str (base64), "messageId": str }, "subscription": str }` | `200 OK` (empty) | Receives Gmail push notifications |
| `POST` | `/api/gmail/watch` | Bearer | — | `{ "historyId": str, "expiration": str }` | Manually trigger Gmail watch setup |
| `GET` | `/api/gmail/watch/status` | Bearer | — | `{ "history_id": int, "expiration": int, "is_active": bool, "updated_at": str }` | Check watch status |
| `POST` | `/api/knowledge-base/reindex` | Bearer | — | `{ "status": "reindexing", "count": int }` | Re-embed all KB entries into vector store |

---

## LangGraph Agent Pipeline

### State Schema

```python
from typing import TypedDict, Literal

class SupportState(TypedDict):
    # Input
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

    # RAG
    retrieved_docs: list[str]
    docs_relevant: bool

    # Agent
    reply: str
    reasoning: str
    enough_information: bool
    promises_an_action: bool
    issue: dict | None

    # Decision
    action: Literal["reply", "escalate"]
    escalation_reason: str | None
    proposed_action: str | None

    # Control
    retry_count: int
    max_retries: int
```

### Node Descriptions

| Node | Purpose | LLM |
|---|---|---|
| `classify` | Classify email into section, detect language, check escalation triggers | ChatGroq with structured output |
| `check_attachments` | Check `has_attachments` flag | None (Python) |
| `check_needs_human` | Check `needs_human` from classifier | None (Python) |
| `retrieve_docs` | Semantic search against KB vector store | Embeddings only |
| `grade_docs` | Evaluate if retrieved docs answer the query | ChatGoogleGenerativeAI |
| `rewrite_and_retrieve` | Rewrite query for better retrieval | ChatGoogleGenerativeAI + Embeddings |
| `generate_reply` | Generate support reply using context | ChatGoogleGenerativeAI structured output |
| `validate_reply` | Check for empty text, AI mentions, promises | None (Python regex) |
| `apply_rules` | Run issue resolution rules | None (Python) |
| `send_reply` | Terminal — marks action as "reply" | None |
| `escalate` | Terminal — marks action as "escalate" | None |

---

## File Structure (after refactor)

```
ai-customer-support/
├── app/
│   ├── __init__.py
│   ├── main.py                    # MODIFIED — add webhook + watch endpoints
│   ├── config.py                  # MODIFIED — add GCP vars, remove poll_interval
│   ├── db.py                      # MODIFIED — add vector store + watch state functions
│   ├── gmail.py                   # MODIFIED — add watch(), history_list()
│   ├── guards.py                  # UNCHANGED
│   ├── pipeline.py                # MODIFIED — use new decide() interface
│   ├── webhook.py                 # NEW — Pub/Sub webhook handler
│   ├── vectorstore.py             # NEW — Vector store management
│   └── ai/
│       ├── __init__.py
│       ├── schemas.py             # MODIFIED — add SupportState TypedDict
│       ├── classifier.py          # REWRITTEN — LangChain ChatGroq
│       ├── agent.py               # REWRITTEN — LangGraph StateGraph
│       ├── decide.py              # REWRITTEN — invoke LangGraph
│       └── rules.py               # UNCHANGED
├── scripts/
│   ├── get_refresh_token.py       # UNCHANGED
│   ├── gmail_check.py             # UNCHANGED
│   ├── seed_knowledge_base.py     # MODIFIED — also embed into vector store
│   └── setup_gmail_watch.py       # NEW
├── evals/                         # MINOR UPDATES to import paths
├── playground/                    # MINOR UPDATES to import paths
├── knowledge_base/                # UNCHANGED
├── supabase/
│   └── migrations/
│       ├── 20261102135742_create_tables.sql     # UNCHANGED
│       └── 20261107_add_embeddings.sql          # NEW
├── dashboard/                     # ENTIRELY UNCHANGED
├── pyproject.toml                 # MODIFIED — swap deps
└── .env                           # MODIFIED — add GCP vars
```

---

## Environment Variables

### Keep
| Variable | Description |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `GOOGLE_REFRESH_TOKEN` | Gmail OAuth refresh token |
| `DATABASE_URL` | PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key for classifier |
| `GEMINI_API_KEY` | Google Gemini API key for agent |
| `CLASSIFIER_MODEL` | Model name for classifier |
| `AGENT_MODEL` | Model name for agent |
| `DASHBOARD_USERNAME` | Dashboard login username |
| `DASHBOARD_PASSWORD` | Dashboard login password |

### Add
| Variable | Description |
|---|---|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `PUBSUB_TOPIC` | Pub/Sub topic name |
| `WEBHOOK_URL` | Public webhook URL |
| `EMBEDDING_MODEL` | Embedding model (default: `models/text-embedding-004`) |

### Remove
| Variable | Description |
|---|---|
| `POLL_INTERVAL_SECONDS` | Replaced by webhook |
| `PYDANTIC_AI_NO_BANNER` | pydantic-ai specific |

---

## Dependencies

### Remove
```
pydantic-ai-slim[anthropic,google,groq]
```

### Add
```
langchain>=0.3
langchain-google-genai>=2.0
langchain-groq>=0.2
langgraph>=0.2
langchain-community>=0.3
```

---

## Implementation Tasks

### Phase 1: Foundation — Dependencies & Config
| # | Task | Files |
|---|---|---|
| 1.1 | Update `pyproject.toml` — swap deps | `pyproject.toml` |
| 1.2 | Update `config.py` — add GCP fields, remove `poll_interval_seconds` | `app/config.py` |
| 1.3 | Update `.env` / `.env.example` | `.env`, `.env.example` |
| 1.4 | Run `uv sync` | — |

### Phase 2: Schemas
| # | Task | Files |
|---|---|---|
| 2.1 | Add `SupportState` TypedDict, keep existing models | `app/ai/schemas.py` |

### Phase 3: LLM Layer — LangChain/LangGraph
| # | Task | Files |
|---|---|---|
| 3.1 | Rewrite classifier with `ChatGroq.with_structured_output()` | `app/ai/classifier.py` |
| 3.2 | Create vector store module | `app/vectorstore.py` |
| 3.3 | Build LangGraph `StateGraph` pipeline | `app/ai/agent.py` |
| 3.4 | Rewrite `decide()` to invoke LangGraph | `app/ai/decide.py` |
| 3.5 | Keep `rules.py` unchanged | `app/ai/rules.py` |

### Phase 4: Gmail Webhook
| # | Task | Files |
|---|---|---|
| 4.1 | Add `watch()` and `history_list()` to Gmail class | `app/gmail.py` |
| 4.2 | Create webhook handler module | `app/webhook.py` |
| 4.3 | Add DB functions for watch state + embeddings | `app/db.py` |
| 4.4 | Create new migration | `supabase/migrations/20261107_add_embeddings.sql` |
| 4.5 | Add new endpoints to `main.py` | `app/main.py` |
| 4.6 | Add watch renewal background task | `app/main.py` / `app/webhook.py` |
| 4.7 | Update `pipeline.py` for new interface | `app/pipeline.py` |
| 4.8 | Create `scripts/setup_gmail_watch.py` | `scripts/setup_gmail_watch.py` |
| 4.9 | Delete `poller.py` | `app/poller.py` |

### Phase 5: Knowledge Base Embedding
| # | Task | Files |
|---|---|---|
| 5.1 | Update seed script to also embed | `scripts/seed_knowledge_base.py` |
| 5.2 | Hook KB CRUD to re-embed on changes | `app/main.py` / `app/db.py` |

### Phase 6: Testing & Verification
| # | Task | Files |
|---|---|---|
| 6.1 | Update `playground/try_pipeline.py` | `playground/try_pipeline.py` |
| 6.2 | Update `evals/run_evals.py` | `evals/run_evals.py` |
| 6.3 | Test webhook locally with ngrok | — |
| 6.4 | Test watch renewal | — |
| 6.5 | Test KB reindexing | — |
| 6.6 | Run golden email evals | — |

---

## GCP Setup Prerequisites

1. Enable Gmail API + Cloud Pub/Sub API in GCP Console
2. Create Pub/Sub topic (e.g., `projects/YOUR_PROJECT/topics/gmail-notifications`)
3. Grant `gmail-api-push@system.gserviceaccount.com` as Pub/Sub Publisher on the topic
4. Create Push Subscription pointing to `https://yourdomain.com/webhook/gmail`
5. Set `GCP_PROJECT_ID`, `PUBSUB_TOPIC`, `WEBHOOK_URL` in `.env`
6. Run `python scripts/setup_gmail_watch.py`

---

## Key Design Decisions

1. **Vector Store: pgvector in Supabase** — keeps stack simple, one database
2. **Embedding Strategy** — chunk KB entries by `## heading`, embed independently, top-k retrieval
3. **Webhook Idempotency** — historyId comparison + events table UNIQUE constraint prevent double-processing
4. **Watch Renewal** — background task checks every 6 hours, renews if within 1 day of expiry
5. **Keep `rules.py` as-is** — pure Python logic, works perfectly, no LLM dependency
6. **Schemas Compatibility** — LangChain's `with_structured_output()` works natively with existing Pydantic models

