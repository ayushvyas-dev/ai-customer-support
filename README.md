# Nexa Mobile — AI Customer Support Agent

[![Live Frontend](https://img.shields.io/badge/Frontend-Vercel-black?style=for-the-badge&logo=vercel)](https://ai-customer-support-coral-eight.vercel.app)
[![Live Backend](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://ai-customer-support-jp8w.onrender.com)
[![API Docs](https://img.shields.io/badge/FastAPI-Swagger_Docs-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://ai-customer-support-jp8w.onrender.com/docs)

> 🌐 **Live Deployments:**
> - **Frontend Dashboard:** [https://ai-customer-support-coral-eight.vercel.app](https://ai-customer-support-coral-eight.vercel.app)
> - **Backend API:** [https://ai-customer-support-jp8w.onrender.com](https://ai-customer-support-jp8w.onrender.com)
> - **API Docs & Health:** [https://ai-customer-support-jp8w.onrender.com/docs](https://ai-customer-support-jp8w.onrender.com/docs) \| [https://ai-customer-support-jp8w.onrender.com/health](https://ai-customer-support-jp8w.onrender.com/health)

An enterprise-ready, automated email customer support system for **Nexa Mobile**, built with **FastAPI**, **LangChain**, **LangGraph**, and **Supabase (PostgreSQL + pgvector)**. Incoming customer queries received in Gmail trigger real-time Google Cloud Pub/Sub push webhooks, routing threads through an agentic RAG workflow with rigorous safety guardrails and policy enforcement.

---

## 🚀 Key Features

* **Real-Time Push-Driven Processing**: Eliminates slow polling via **Google Cloud Pub/Sub** push notifications to a secure FastAPI webhook (`/webhook/gmail`) with automatic Gmail watch renewal.
* **Agentic RAG with Self-Correction**: Implements a cyclic **LangGraph** state machine that retrieves context from vector storage, grades document relevance, rewrites low-quality queries, and synthesizes answers.
* **Multi-Layer Safety & Defense-in-Depth Guardrails**:
  * **Inbound Prompt Injection Defense**: Intercepts jailbreak templates, tag breakouts, and instruction override attempts before they reach the model.
  * **Dual PII Protection**: Automatically redacts payment cards, CVVs, passwords, OTPs, and API keys on both inbound customer messages and outbound draft replies.
  * **Business Rule & Commitment Interception**: Strictly blocks unauthorized agent commitments (e.g., promising refunds, discounts, order cancellations, or callbacks).
  * **Groundedness & Anti-Hallucination Verification**: Verifies claims against official warranty, return window, and product catalog policies.
  * **Output Validation**: Enforces professional tone, sign-offs, and placeholder sanitization (`[Customer Name]`, `TODO`).
* **Supabase pgvector Knowledge Base**: Automatically chunks and vectorizes markdown reference policies into 768-dimensional embeddings using `models/gemini-embedding-001`.
* **Model Resilience & Fallbacks**: Fast classification powered by Groq (`openai/gpt-oss-120b`) and grounded generation with Gemini (`gemini-2.5-flash`), featuring multi-model fallback redundancy.
* **Full-Featured Management Dashboard**: **Next.js 16** (React 19, Tailwind CSS 4) web application for inspecting pipeline execution traces, triaging customer tickets, and editing knowledge base articles with automatic re-embedding.
* **Production-Ready & CI/CD**: Dockerized for zero-downtime deployment on **Render**, backed by a full **GitHub Actions CI** suite for unit tests, container builds, and frontend compilation.

---

## 🏛 Architecture Diagram

```mermaid
flowchart TD
    subgraph Inbound ["1. Inbound Ingestion"]
        User([Customer Email]) -->|Sends email| Gmail[Gmail Inbox]
        Gmail -->|Push Notification| PubSub[GCP Cloud Pub/Sub]
        PubSub -->|POST /webhook/gmail| Webhook[FastAPI Webhook Receiver]
    end

    subgraph Guards ["2. Ingress Guardrails"]
        Webhook --> PII_In[Mask Inbound PII]
        PII_In --> InjectionCheck{Prompt Injection?}
        InjectionCheck -->|Yes: Flagged| AutoEscalate[Safe Escalation Reply]
        InjectionCheck -->|No: Clean| LangGraph[LangGraph StateGraph]
    end

    subgraph AgenticRAG ["3. LangGraph Agentic Pipeline"]
        LangGraph --> Classify[Classifier Node\nGroq gpt-oss-120b]
        Classify --> CheckNeeds{Needs Human?}
        CheckNeeds -->|Yes| EscalateNode[Escalate Node]
        CheckNeeds -->|No| Retrieve[Retrieve Docs Node\nSupabase pgvector]

        Retrieve --> GradeDocs[Grade Documents Node\nGemini]
        GradeDocs -->|Irrelevant| Rewrite[Rewrite Query & Retrieve]
        Rewrite --> GradeDocs
        GradeDocs -->|Relevant| Generate[Generate Reply Node\nGemini 2.5 Flash]

        Generate --> ValidateReply[Validate Output Node\nPII, Commitments, Sign-off]
        ValidateReply -->|Defects Detected & Retries Left| Generate
        ValidateReply -->|Max Retries Exceeded| EscalateNode
        ValidateReply -->|Valid| ApplyRules[Deterministic Business Rules]
    end

    subgraph Outbound ["4. Outbound Resolution & Observability"]
        ApplyRules -->|Reply Approved| SendGmail[Gmail API: Send Thread Reply]
        EscalateNode -->|Ticket Escalated| SendAck[Gmail API: Send Acknowledgment]
        SendGmail --> AuditDB[(Supabase PostgreSQL\nEvents, Tickets, Messages)]
        SendAck --> AuditDB
        AuditDB <--> NextDashboard[Next.js 16 Dashboard]
    end
```

---

## 💻 Tech Stack

### Backend
| Technology | Role |
| :--- | :--- |
| **Python 3.12+** | Runtime environment |
| **FastAPI** | High-performance asynchronous REST API and webhook server |
| **LangChain & LangGraph** | Agent state machine, cycles, conditional routing, and RAG orchestration |
| **ChatGroq (`openai/gpt-oss-120b`)** | Low-latency structured email classification |
| **Google Gemini (`gemini-2.5-flash`)** | Grounded drafting, document grading, and query rewriting |
| **Google Gemini Embeddings** | Document vectorization (`models/gemini-embedding-001`) |
| **Supabase (PostgreSQL + pgvector)** | Relational storage for tickets/events and vector similarity search |
| **Google API Client** | Gmail OAuth 2.0, thread reading, sending, and push watch renewal |
| **Pydantic v2 / Pydantic Settings** | Strict schemas, state management, and configuration loading |

### Frontend
| Technology | Role |
| :--- | :--- |
| **Next.js 16 (App Router)** | Modern full-stack React framework |
| **React 19** | Concurrent UI components and state management |
| **Tailwind CSS 4** | Responsive design system |
| **Lucide React** | Icons and dashboard visuals |
| **TypeScript** | Static typing and interfaces |

### Infrastructure & CI/CD
| Technology | Role |
| :--- | :--- |
| **Docker** | Multi-stage, non-root lightweight production container |
| **Render** | Containerized backend web service deployment |
| **GitHub Actions** | Automated CI workflow running unit tests, Docker build, and Next.js verification |

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
│   │   │   ├── agent.py               # LangGraph StateGraph pipeline definition
│   │   │   ├── classifier.py          # Groq structured email classifier
│   │   │   ├── decide.py              # Pipeline invocation entry point
│   │   │   ├── rules.py               # Deterministic business policies & SLA rules
│   │   │   └── schemas.py             # SupportState TypedDict & Pydantic models
│   │   ├── config.py                  # Environment settings loaded via pydantic-settings
│   │   ├── db.py                      # Database connection and CRUD operations (psycopg3)
│   │   ├── gmail.py                   # Gmail API wrapper (messages, threads, watch)
│   │   ├── guards.py                  # Guardrails (PII masking, injection, commitments)
│   │   ├── main.py                    # FastAPI application, auth, tickets, and KB APIs
│   │   ├── pipeline.py                # End-to-end background message execution coordinator
│   │   ├── vectorstore.py             # pgvector embedding indexing and cosine retrieval
│   │   └── webhook.py                 # Gmail Cloud Pub/Sub webhook endpoint handler
│   ├── evals/                         # Benchmark evaluation suite
│   │   ├── eval_cases.json            # 20 golden test email scenarios
│   │   ├── evaluators.py              # Evaluation metrics and assertions
│   │   └── run_evals.py               # Golden evaluation runner
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
│   │   ├── seed_knowledge_base.py     # Parses markdown docs & embeds into Supabase pgvector
│   │   └── setup_gmail_watch.py       # Configures Google Cloud Pub/Sub watch on inbox
│   ├── supabase/
│   │   └── migrations/                # PostgreSQL schemas (events, tickets, pgvector tables)
│   ├── tests/                         # Automated unit test suite (42 tests)
│   ├── Dockerfile                     # Production container definition for Render
│   ├── .dockerignore
│   ├── requirements.txt               # Pinned Python dependencies
│   └── .env.example                   # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── events/page.tsx        # Event audit logs and execution traces
│   │   │   ├── knowledge-base/page.tsx# Knowledge base editor & live re-indexing
│   │   │   ├── login/page.tsx         # Dashboard authentication
│   │   │   ├── tickets/page.tsx       # Customer thread triage view
│   │   │   └── page.tsx               # Analytics overview
│   │   ├── components/                # UI components (cards, badges, modals)
│   │   ├── context/                   # React auth and state providers
│   │   └── lib/                       # API clients and utilities
│   ├── package.json
│   └── .env.example                   # Frontend environment template
├── .dockerignore                      # Root Docker ignore preventing node_modules upload
├── .gitignore
├── spec.md                            # Complete architecture specification
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
| `DATABASE_URL` | Supabase / PostgreSQL connection URI (requires pgvector enabled) | `postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres` |
| `GROQ_API_KEY` | Groq API Key for low-latency classification | `gsk_...` |
| `GEMINI_API_KEY` | Google Gemini API Key for generation and embeddings | `AIzaSy...` |
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

### 2. Database Migration & Knowledge Base Seeding

1. In your Supabase SQL Editor, execute the migration files located in [`backend/supabase/migrations/`](file:///run/media/ayush/DriveD/ai-projects/ai-customer-support/backend/supabase/migrations/):
   - `20261102135742_create_tables.sql` (Creates `events`, `tickets`, `messages`, `knowledge_base`)
   - `20261107_add_embeddings.sql` (Enables `pgvector` and creates `knowledge_base_embeddings` & `gmail_watch_state`)

2. Seed the markdown policies and generate vector embeddings:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   # Seed markdown documents & index vectors
   python scripts/seed_knowledge_base.py
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

### 1. Automated Unit Tests (Guardrails & Business Rules)
Execute the comprehensive 42-test unit suite covering prompt injection interception, PII masking, commitment detection, and LangGraph integration:

```bash
cd backend
python -m unittest discover -s tests -v
```

### 2. Offline Pipeline Simulation
Test how the LangGraph agent classifies and resolves customer queries locally without sending actual emails:

```bash
cd backend
python playground/try_pipeline.py
```

### 3. Golden Evaluation Benchmark Suite
Run the 20-scenario golden evaluation benchmark evaluating accuracy, safety compliance, and grounding:

```bash
cd backend
python -m evals.run_evals
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
3. In the **Environment** tab, fill in the required environment variables (e.g. `DATABASE_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.).
4. Click **Deploy Web Service**. Render will automatically build the container and manage zero-downtime rollouts.
