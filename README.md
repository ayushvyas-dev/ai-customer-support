# Nexa Mobile — Autonomous Enterprise AI Customer Support Agent

[![Live Frontend](https://img.shields.io/badge/Frontend-Vercel-black?style=for-the-badge&logo=vercel)](https://ai-customer-support-coral-eight.vercel.app)
[![Live Backend](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://ai-customer-support-jp8w.onrender.com)
[![API Docs](https://img.shields.io/badge/FastAPI-Swagger_Docs-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://ai-customer-support-jp8w.onrender.com/docs)

> 🌐 **Live Deployments:**
> - **Frontend Dashboard & Approvals:** [https://ai-customer-support-coral-eight.vercel.app](https://ai-customer-support-coral-eight.vercel.app)
> - **Backend API:** [https://ai-customer-support-jp8w.onrender.com](https://ai-customer-support-jp8w.onrender.com)
> - **API Docs & Health:** [https://ai-customer-support-jp8w.onrender.com/docs](https://ai-customer-support-jp8w.onrender.com/docs) \| [https://ai-customer-support-jp8w.onrender.com/health](https://ai-customer-support-jp8w.onrender.com/health)

An autonomous, enterprise-grade email customer support system for **Nexa Mobile**, built with **FastAPI**, **LangChain**, **LangGraph**, and **Supabase (PostgreSQL + pgvector)**. The system moves beyond passive question answering into an **active system of action**—autonomously looking up orders, checking carrier tracking checkpoints, dispatching warranty replacements, verifying device coverage, generating RMAs, and pausing for human supervisor approval on high-stakes actions.

---

## 🚀 Key Features

* **Autonomous ReAct Agent Reasoning Loop**: A dynamic **LangGraph** tool-calling agent loop (`agent_reason` $\leftrightarrow$ `execute_tools`) with message history retention (`Annotated[list[Any], add_messages]`) that decomposes complex customer inquiries and executes multi-step resolutions.
* **Enterprise Tool Integration**: 7 autonomous tools with input sanitization and audit trails:
  1. `tool_lookup_order`: Queries enterprise database for order status, line items, and delivery history.
  2. `tool_track_package`: Real-time carrier logistics tracking with checkpoint history (FedEx/UPS).
  3. `tool_verify_warranty`: Verifies active 1-year smartphone and 6-month accessory warranty coverage.
  4. `tool_request_rma_return`: Validates 30-day return windows and generates prepaid return labels.
  5. `tool_dispatch_replacement`: Automatically dispatches replacement accessories for damaged or defective items within policy limits.
  6. `tool_request_refund`: Processes store credits or courtesy refunds with tiered governance.
  7. `tool_search_knowledge_base`: Hybrid search across product manuals and support policies.
* **Tiered Human-in-the-Loop (HITL) Governance**:
  * **Tier 1 (Autonomous)**: Immediate execution for low-risk actions (order lookups, tracking inquiries, accessory replacements $\le \$25$).
  * **Tier 2 (Supervisory Approval)**: State machine pauses using LangGraph `interrupt()`, enqueueing high-stakes actions (refunds $> \$50$, warranty exceptions) into the supervisor approval queue for human review and hot resumption.
  * **Tier 3 (Immediate Escalation)**: Safety hazards (swollen batteries, smoke, thermal runaways) and legal threats trigger immediate human routing with compliant customer acknowledgments.
* **PDF Knowledge Base Ingestion**: Operators can upload product manuals and warranty guides (`.pdf`) directly through the dashboard. Pages are parsed via `pypdf` and chunked with `RecursiveCharacterTextSplitter` while preserving page numbers and source metadata.
* **Advanced Hybrid Search (Dense + Sparse) & Reranking**:
  * **Dense Retrieval**: 768-dimensional semantic cosine similarity via `pgvector`.
  * **Sparse Retrieval**: PostgreSQL Full-Text Search (`tsvector` generated column + GIN index) with `plainto_tsquery`.
  * **Reciprocal Rank Fusion (RRF)**: Merges dual candidate sets using $RRF(d) = \sum \frac{1}{60 + r(d)}$.
  * **Cross-Scoring Reranker**: Evaluates fused candidates for direct query relevance before context injection, citing exact page numbers.
* **Multi-Layer Guardrails & Safety Architecture**:
  * **Prompt Injection Defense**: Intercepts jailbreaks, delimiter injection, and instruction overrides deterministically.
  * **Bi-Directional PII Masking**: Redacts credit cards, CVVs, passwords, and API keys inbound and outbound.
  * **Commitment Enforcement**: Prevents unauthorized financial or operational promises before emails are sent.
  * **Output Formatting**: Cleanses raw LLM structured content blocks and internal reasoning traces, enforcing corporate sign-offs.
* **Real-Time Push-Driven Processing**: Low-latency Google Cloud Pub/Sub push webhooks (`/webhook/gmail`) with automatic Gmail watch renewal.
* **Full-Featured Management Dashboard**: **Next.js 16** (React 19, Tailwind CSS 4) web application featuring ticket triage, execution event audits, a knowledge base editor with drag-and-drop PDF upload, and a dedicated **Supervisor Approval Queue** (`/approvals`).
* **105 Automated Unit Tests & 110 Golden Evals**: Rigorous test coverage across all guardrails, enterprise tools, and agent workflows with LLM-as-a-judge benchmarking.

---

## 🏛 Architecture Diagram

```mermaid
flowchart TD
    subgraph Inbound ["1. Inbound Ingestion & Security"]
        User([Customer Email]) -->|Sends email| Gmail[Gmail Inbox]
        Gmail -->|Push Notification| PubSub[GCP Cloud Pub/Sub]
        PubSub -->|POST /webhook/gmail| Webhook[FastAPI Webhook Receiver]
        Webhook --> PII_In[Mask Inbound PII]
        PII_In --> InjectionCheck{Prompt Injection?}
        InjectionCheck -->|Yes: Flagged| AutoEscalate[Safe Escalation Reply]
        InjectionCheck -->|No: Clean| Classify[Classifier Node\nGroq / Gemini / Heuristic]
    end

    subgraph AgentLoop ["2. Autonomous ReAct Agent Loop"]
        Classify --> CheckNeeds{Needs Escalation?}
        CheckNeeds -->|Yes| EscalateNode[Escalate Node]
        CheckNeeds -->|No| ReasonNode[Agent Reason Node\nGemini 2.5 Flash]

        ReasonNode --> HasToolCalls{Calls Tool?}
        HasToolCalls -->|Yes| PolicyCheck{Evaluate Policy Tier}

        PolicyCheck -->|Tier 1: Auto| ExecTools[Execute Tools Node\nLookup, Tracking, RMA, etc.]
        PolicyCheck -->|Tier 2: High-Stakes| Interrupt[LangGraph Interrupt\nSupervisor Approval Queue]
        Interrupt -->|Approved / Rejected| ExecTools
        ExecTools --> ReasonNode

        HasToolCalls -->|No: Final Text| ValidateReply[Validate Output Node\nPII, Commitments, Sign-off]
        ValidateReply -->|Defects Detected & Retries Left| ReasonNode
        ValidateReply -->|Max Retries Exceeded| EscalateNode
        ValidateReply -->|Valid| ApplyRules[Deterministic Business Rules]
    end

    subgraph HybridRAG ["3. Hybrid RAG & Knowledge Base"]
        PDFUpload[Upload PDF / Knowledge Manual] --> PDFParser[pypdf Page Extractor]
        PDFParser --> ChunkSplitter[Recursive Splitter + Page Metadata]
        ChunkSplitter --> VectorDB[(Supabase PostgreSQL)]

        VectorDB --> DenseSearch[pgvector Cosine Distance]
        VectorDB --> SparseSearch[PostgreSQL FTS GIN Index]
        DenseSearch --> RRF[Reciprocal Rank Fusion]
        SparseSearch --> RRF
        RRF --> Reranker[Relevance Reranker]
        Reranker --> ReasonNode
    end

    subgraph Outbound ["4. Outbound Resolution & Observability"]
        ApplyRules -->|Reply Approved| SendGmail[Gmail API: Send Thread Reply]
        EscalateNode -->|Ticket Escalated| SendAck[Gmail API: Send Acknowledgment]
        SendGmail --> AuditDB[(Supabase PostgreSQL)]
        SendAck --> AuditDB
        AuditDB <--> NextDashboard[Next.js 16 Dashboard\nTickets, Events, KB, Approvals]
    end
```

---

## 💻 Tech Stack

### Backend
| Technology | Role |
| :--- | :--- |
| **Python 3.12+** | Runtime environment |
| **FastAPI** | High-performance asynchronous REST API, webhook, and multipart file upload server |
| **LangChain & LangGraph** | ReAct state graph, tool-calling cycles, conditional routing, and `interrupt()` HITL |
| **`pypdf`** | Robust page-aware PDF text extraction and metadata processing |
| **`langchain-text-splitters`** | Semantic and recursive character text chunking |
| **ChatGroq (`openai/gpt-oss-120b`)** | Low-latency structured email classification with multi-tier fallback |
| **Google Gemini (`gemini-2.5-flash`)** | Autonomous reasoning, document reranking, grading, and drafting |
| **Google Gemini Embeddings** | Document vectorization (`models/gemini-embedding-001`, 768-d) |
| **Supabase (PostgreSQL + pgvector)** | Relational tables, vector embeddings, and full-text search (`tsvector` + GIN) |
| **Google API Client** | Gmail OAuth 2.0, thread reading, sending, and push watch renewal |
| **Pydantic v2 / Pydantic Settings** | Strict schemas, state management, and configuration loading |

### Frontend
| Technology | Role |
| :--- | :--- |
| **Next.js 16 (App Router)** | Full-stack React framework |
| **React 19** | Modern concurrent UI components and state management |
| **Tailwind CSS 4** | Clean, responsive design system |
| **Lucide React** | Icons and dashboard visuals |
| **TypeScript** | Static typing and interfaces |

### Infrastructure & CI/CD
| Technology | Role |
| :--- | :--- |
| **Docker** | Multi-stage, non-root lightweight production container |
| **Render** | Containerized backend web service deployment |
| **Vercel** | Edge-deployed Next.js frontend |
| **GitHub Actions** | Automated CI workflow running 105 unit tests, Docker build, and Next.js verification |

---

## 📁 Project Folder Structure

```
ai-customer-support/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI (tests, Docker build, frontend)
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── agent.py               # LangGraph ReAct tool-calling graph & node logic
│   │   │   ├── classifier.py          # 3-tier resilient email classifier (Groq/Gemini/Rule)
│   │   │   ├── decide.py              # Pipeline invocation entry point
│   │   │   ├── policies.py            # Tiered HITL action authorization policies
│   │   │   ├── reranker.py            # Reciprocal Rank Fusion & cross-scoring reranker
│   │   │   ├── rules.py               # Deterministic business policies & SLA rules
│   │   │   ├── schemas.py             # SupportState TypedDict (add_messages) & Pydantic models
│   │   │   └── tools.py               # 7 autonomous LangChain tools with audit logging
│   │   ├── config.py                  # Environment settings loaded via pydantic-settings
│   │   ├── db.py                      # Database connections and CRUD operations (psycopg3)
│   │   ├── gmail.py                   # Gmail API wrapper (messages, threads, watch)
│   │   ├── guards.py                  # Guardrails (PII masking, injection, commitments, content extraction)
│   │   ├── main.py                    # FastAPI application, auth, tickets, approvals, and KB upload APIs
│   │   ├── pipeline.py                # Message execution coordinator & approval resumption flow
│   │   ├── services/
│   │   │   ├── enterprise.py          # Enterprise mock backend (orders, tracking, RMA, warranty, refunds)
│   │   │   └── pdf_parser.py          # Page-aware PDF parsing & chunking service
│   │   ├── vectorstore.py             # Hybrid search (pgvector + FTS), RRF, and embedding indexing
│   │   └── webhook.py                 # Gmail Cloud Pub/Sub webhook endpoint handler
│   ├── evals/                         # Benchmark evaluation suite
│   │   ├── eval_cases.json            # 110 golden test scenarios (including agentic tool cases)
│   │   ├── evaluators.py              # Evaluation metrics, tool accuracy, and assertions
│   │   └── run_evals.py               # Golden evaluation runner (LLM-as-a-judge)
│   ├── knowledge_base/                # Markdown reference documentation
│   │   ├── accessories.md             # Warranty and specs for chargers, cases, audio
│   │   ├── brand-and-tone.md          # Tone guidelines, signature, and formatting
│   │   ├── escalation-rules.md        # Criteria for escalating to human operators
│   │   ├── returns-and-warranty.md    # Return windows, refund rules, replacement policy
│   │   ├── shipping.md                # Delivery timelines, carriers, tracking
│   │   └── smartphone.md              # Nexa One and Nexa One Pro specs & troubleshooting
│   ├── playground/
│   │   └── try_pipeline.py            # Local CLI testing script without Gmail dependencies
│   ├── scripts/
│   │   ├── get_refresh_token.py       # Helper script to generate OAuth refresh tokens
│   │   ├── gmail_check.py             # Utility to inspect Gmail labels and threads
│   │   ├── seed_enterprise_data.py    # Seeds enterprise mock database with customer/order fixtures
│   │   ├── seed_knowledge_base.py     # Parses markdown docs & embeds into Supabase pgvector
│   │   └── setup_gmail_watch.py       # Configures Google Cloud Pub/Sub watch on inbox
│   ├── supabase/
│   │   └── migrations/
│   │       ├── 20261102135742_create_tables.sql            # Core tables (events, tickets, messages, kb)
│   │       ├── 20261107_add_embeddings.sql                 # pgvector extension & embeddings table
│   │       ├── 20261115_add_enterprise_agentic_tables.sql  # Orders, tracking, RMA, approvals tables
│   │       └── 20261115_add_fts_and_pdf_metadata.sql       # Full-Text Search tsvector & PDF metadata
│   ├── tests/                         # 105 automated unit tests across all systems
│   ├── Dockerfile                     # Production container definition for Render
│   ├── pyproject.toml                 # Package configuration
│   ├── requirements.txt               # Pinned Python dependencies
│   └── .env.example                   # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── approvals/page.tsx     # Supervisor approval queue for Tier 2 actions
│   │   │   ├── events/page.tsx        # Event audit logs and execution traces
│   │   │   ├── knowledge-base/page.tsx# Knowledge base editor, PDF upload, & live re-indexing
│   │   │   ├── login/page.tsx         # Dashboard authentication
│   │   │   ├── tickets/page.tsx       # Customer thread triage view
│   │   │   └── page.tsx               # Analytics overview
│   │   ├── components/
│   │   │   ├── ApprovalQueue.tsx      # Real-time action review & hot-resumption component
│   │   │   ├── UploadPdfDialog.tsx    # Drag-and-drop PDF upload and indexing modal
│   │   │   └── ui/                    # Reusable UI primitives (dialogs, buttons, cards, badges)
│   │   ├── context/                   # React auth and state providers
│   │   └── lib/                       # API clients, approvals helper, and formatting utilities
│   ├── package.json
│   └── .env.example                   # Frontend environment template
├── spec.md                            # Complete architecture specification (Phases 1-12)
└── README.md
```

---

## 🔑 Required Environment Variables

### Backend (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Supabase / PostgreSQL connection URI (pgvector enabled) | `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres` |
| `GROQ_API_KEY` | Groq API Key for low-latency classification | `gsk_...` |
| `GEMINI_API_KEY` | Google Gemini API Key for agent reasoning, embeddings, & reranking | `AIzaSy...` |
| `CLASSIFIER_MODEL` | Classification model name on Groq | `openai/gpt-oss-120b` |
| `AGENT_MODEL` | Primary generative agent model | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Google GenAI embedding model | `models/gemini-embedding-001` |
| `GOOGLE_CLIENT_ID` | Google Cloud OAuth 2.0 Client ID | `xxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google Cloud OAuth 2.0 Client Secret | `GOCSPX-xxxx` |
| `GOOGLE_REFRESH_TOKEN` | OAuth Refresh Token with Gmail read/send scopes | `1//04xxxx` |
| `GCP_PROJECT_ID` | Google Cloud Project ID | `nexa-mobile-support` |
| `PUBSUB_TOPIC` | Pub/Sub Topic receiving Gmail notifications | `projects/nexa-mobile-support/topics/gmail-notifications` |
| `WEBHOOK_URL` | Public webhook URL receiving push requests | `https://ai-customer-support-jp8w.onrender.com/webhook/gmail` |
| `DASHBOARD_USERNAME` | Username for accessing the frontend dashboard | `admin` |
| `DASHBOARD_PASSWORD` | Password for dashboard session tokens | `your-secure-password` |

### Frontend (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:

```bash
cp frontend/.env.example frontend/.env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Base URL of the backend FastAPI service | `http://localhost:8000` |

---

## 🛠 Setup & Run Instructions

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+** and `npm`
- A **Supabase** project with the `pgvector` extension enabled
- A **Google Cloud Platform** project with Gmail API and Cloud Pub/Sub enabled

---

### 2. Database Migration & Seeding

1. In your Supabase SQL Editor, execute the migrations in [`backend/supabase/migrations/`](file:///run/media/ayush/DriveD/ai-projects/ai-customer-support/backend/supabase/migrations/):
   - `20261102135742_create_tables.sql` (Creates `events`, `tickets`, `messages`, `knowledge_base`)
   - `20261107_add_embeddings.sql` (Enables `pgvector`, creates `knowledge_base_embeddings` & `gmail_watch_state`)
   - `20261115_add_enterprise_agentic_tables.sql` (Creates `customers`, `orders`, `rma_requests`, `approvals`)
   - `20261115_add_fts_and_pdf_metadata.sql` (Adds `fts` tsvector GIN index & PDF source columns)

2. Install dependencies and seed fixtures:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   # Seed markdown documents & generate vector embeddings
   python scripts/seed_knowledge_base.py

   # Seed enterprise mock database (orders, tracking, customers)
   python scripts/seed_enterprise_data.py
   ```

---

### 3. Running the Backend Server

```bash
cd backend
source .venv/bin/activate

# Run FastAPI with live reloading
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)
* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 4. Running the Frontend Dashboard

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to log in with `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`.
- **Tickets**: Review incoming emails and automated resolutions.
- **Approvals** (`/approvals`): Review and approve/reject Tier 2 agent actions.
- **Knowledge Base** (`/knowledge-base`): Add text policies or upload PDF documentation with automated hybrid indexing.
- **Events**: Inspect live trace execution logs.

---

### 5. Configuring Gmail Live Push Webhooks

1. **Expose your local backend** (for local development):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   # or: ngrok http 8000
   ```
2. **Configure Cloud Pub/Sub**:
   - Create a topic named `gmail-notifications`.
   - Grant `gmail-api-push@system.gserviceaccount.com` the **Pub/Sub Publisher** role on the topic.
   - Create a **Push Subscription** with your endpoint URL: `https://<public-url>/webhook/gmail`.
3. **Register the Gmail Watch**:
   ```bash
   cd backend
   python scripts/setup_gmail_watch.py
   ```

---

## 🧪 Testing & Verification

### 1. Automated Unit Tests (105 Tests)
Execute the complete test suite covering prompt injection, PII masking, commitment interception, autonomous tools, tiered approvals, PDF parsing, and hybrid RAG:

```bash
cd backend
python -m unittest discover -s tests -v
```

### 2. Offline Pipeline Simulation
Test how the agent reasons, executes tools, and generates responses locally without sending live emails:

```bash
cd backend
python playground/try_pipeline.py
```

### 3. Golden Evaluation Benchmark Suite (110 Scenarios)
Run the golden evaluation benchmark testing intent classification, tool accuracy, safety compliance, and groundedness:

```bash
cd backend
python evals/run_evals.py --mock
```

---

## 🚢 Deployment (Render & Docker)

To deploy the backend to [Render](https://render.com) as a Docker Web Service:

1. Create a new **Web Service** connected to your repository.
2. Configure service settings:
   * **Environment**: `Docker`
   * **Root Directory**: `backend`
   * **Dockerfile Path**: `Dockerfile`
   * **Health Check Path**: `/health`
3. In the **Environment** tab, fill in the required environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.).
4. Click **Deploy Web Service**. Render will automatically build the container and manage zero-downtime rollouts.
