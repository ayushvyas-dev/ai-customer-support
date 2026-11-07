# Nexa Mobile — AI Customer Support Agent

An automated customer support agent for **Nexa Mobile** powered by **LangChain**, **LangGraph**, and **Supabase pgvector RAG**, triggered in real-time via **Gmail Cloud Pub/Sub webhooks**.

---

## Architecture

```
Gmail Inbox ──(push)──> Google Cloud Pub/Sub ──(HTTP POST)──> FastAPI /webhook/gmail
                                                                      │
                                                     ┌────────────────┴───────────────┐
                                                     ▼                                ▼
                                              Guards & Filters            Async Background Task
                                                                                      │
                                                                                      ▼
                                                                        LangGraph Agentic RAG
                                                                        ├─ Classifier (Groq)
                                                                        ├─ Retriever (pgvector)
                                                                        ├─ Grader & Rewriter
                                                                        ├─ Generator (Gemini)
                                                                        ├─ Safety Validator
                                                                        └─ Deterministic Rules
                                                                                      │
                                                                                      ▼
                                                                             Gmail API Send Reply
```

---

## Prerequisites

- **Python 3.14** (or 3.13+)
- **Node.js 18+** & npm (for dashboard)
- **Supabase PostgreSQL** with `pgvector` enabled
- **Google Cloud Console**:
  - Gmail API enabled
  - Cloud Pub/Sub API enabled
  - OAuth 2.0 Credentials with `https://www.googleapis.com/auth/gmail.modify` scope
- **Groq API Key** (`GROQ_API_KEY`)
- **Google Gemini API Key** (`GEMINI_API_KEY`)

---

## Getting Started

### 1. Environment Configuration

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Key variables in `.env`:
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- `DATABASE_URL` (Supabase PostgreSQL pooler/direct connection string)
- `GROQ_API_KEY`, `GEMINI_API_KEY`
- `GCP_PROJECT_ID`, `PUBSUB_TOPIC` (e.g., `projects/your-project-id/topics/gmail-notifications`)
- `DASHBOARD_USERNAME`, `DASHBOARD_PASSWORD`

### 2. Seed & Vectorize Knowledge Base

Before running, populate the PostgreSQL tables and generate vector embeddings:

```bash
.venv/bin/python scripts/seed_knowledge_base.py
```

### 3. Start the FastAPI Backend

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check**: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Start the Next.js Dashboard

In a separate terminal:

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view:
- **Events**: Real-time pipeline execution audit log.
- **Tickets**: Customer threads, statuses, and message history.
- **Knowledge Base**: Policy documents with automatic re-embedding on edit.

---

## Gmail Webhook Setup (Live Push Mode)

1. **Expose local port for development**:
   ```bash
   ngrok http 8000
   ```
2. **Configure Cloud Pub/Sub**:
   - Create topic `gmail-notifications`.
   - Grant `gmail-api-push@system.gserviceaccount.com` the **Pub/Sub Publisher** role on the topic.
   - Create a **Push Subscription** with endpoint URL: `https://<your-ngrok-domain>/webhook/gmail`.
3. **Register Gmail Watch**:
   ```bash
   .venv/bin/python scripts/setup_gmail_watch.py
   ```

---

## Offline Testing & Evaluations

Test the complete agentic pipeline without sending emails:

```bash
# Single sample query
.venv/bin/python playground/try_pipeline.py

# 20-email golden test suite
.venv/bin/python -m evals.run_evals
```

