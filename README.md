# Nexa Mobile — AI Customer Support Agent

An automated customer support agent for **Nexa Mobile** powered by **LangChain**, **LangGraph**, and **Supabase pgvector RAG**, triggered in real-time via **Gmail Cloud Pub/Sub webhooks**.

The project is cleanly separated into two independent folders:
- **`backend/`**: FastAPI API server, LangGraph agentic RAG pipeline, pgvector similarity store, Gmail integration, and scripts. Ready for Docker / Render deployment.
- **`frontend/`**: Next.js 16 dashboard for auditing pipeline events, viewing tickets, and managing knowledge base articles. Ready for Vercel / Render deployment.

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

## Project Structure

```
ai-customer-support/
├── backend/
│   ├── app/                     # FastAPI app, AI pipeline, DB, vectorstore, Gmail webhook
│   ├── evals/                   # Golden email evaluation benchmark suite
│   ├── knowledge_base/          # Markdown reference policies and product specs
│   ├── playground/              # Interactive CLI testing scripts
│   ├── scripts/                 # Watch setup, OAuth helpers, KB seeder
│   ├── supabase/                # SQL migrations (pgvector, tables)
│   ├── Dockerfile               # Production Docker container definition for backend
│   ├── .dockerignore
│   ├── requirements.txt         # Pinned python dependencies
│   └── .env.example
├── frontend/                    # Next.js 16 App Router dashboard
│   ├── src/
│   ├── package.json
│   └── .env.example
├── spec.md                      # Architecture and endpoint specifications
└── README.md
```

---

## Getting Started

### 1. Backend Setup & Run

```bash
cd backend

# Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Google OAuth, Supabase, Groq, and Gemini keys

# (First-Time Only) Seed and vectorize knowledge base into Supabase pgvector
python scripts/seed_knowledge_base.py

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check**: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend Dashboard Setup & Run

In another terminal:

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Default points to NEXT_PUBLIC_API_URL=http://localhost:8000

# Start Next.js development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view:
- **Events**: Real-time pipeline execution audit log.
- **Tickets**: Customer threads, statuses, and message history.
- **Knowledge Base**: Policy documents with automatic re-embedding on edit.

---

## Gmail Webhook Setup (Live Push Mode)

1. **Expose backend port for local development**:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   # or: ngrok http 8000
   ```
2. **Configure Cloud Pub/Sub in GCP Console**:
   - Create topic `gmail-notifications`.
   - Grant `gmail-api-push@system.gserviceaccount.com` the **Pub/Sub Publisher** role on the topic.
   - Create a **Push Subscription** with endpoint URL: `https://<your-public-url>/webhook/gmail`.
3. **Register Gmail Watch**:
   ```bash
   cd backend
   python scripts/setup_gmail_watch.py
   ```

---

## Offline Testing & Evaluations

Test the complete agentic pipeline without sending emails:

```bash
cd backend

# Single sample query
python playground/try_pipeline.py

# 20-email golden test benchmark suite
python -m evals.run_evals
```
