# 🔍 ArgusCX — The Support System That Investigates, Not Just Answers

> **Hackathon 2026 — Track 2: Customer Support — Autonomous AI Customer Support System**

ArgusCX is a multi-agent AI system that **investigates before resolving** — catching fraud humans miss and handing humans only the cases that truly need them.

---

## 🏗️ Architecture

```
Customer Channels (Web / Mobile / WhatsApp / Email / Voice / Social)
        ↓
  API Gateway + Load Balancer + Auth & Identity
        ↓
  Request Preprocessor (Format, Language Detection, PII Redaction)
        ↓
  Agent Orchestrator (LangGraph)
    ├── Information Retrieval Agent     → RAG over policies, FAQs, past tickets
    ├── Data Investigation Agent        → Fetches order data, payment logs, user history
    ├── Evidence Verification Agent     → AI forensics, EXIF, C2PA, claim history
    ├── Resolution Agent                → Policy engine + refund decision
    └── Escalation Agent                → Full case-file human handoff
        ↓
  Confidence & Risk Scorer → Auto-resolve | Human Handoff | Escalate
        ↓
  Human-in-the-Loop Layer (Agent Workspace / Collaboration / Override / Feedback)
        ↓
  Analytics Engine + Feedback Loop
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, Next.js 14, Tailwind CSS |
| **Backend** | Python 3.11, FastAPI, Nginx |
| **Agent Framework** | LangGraph (multi-agent), LangChain |
| **LLM** | OpenAI GPT-4o / Azure OpenAI / Ollama (local) |
| **VLM** | Azure AI Vision / GPT-4V (evidence analysis) |
| **Embeddings** | text-embedding-3-small |
| **Vector DB** | Pinecone / ChromaDB (local) / Azure AI Search |
| **Primary DB** | PostgreSQL |
| **Conversations/Logs** | MongoDB |
| **Cache/Queue** | Redis + Celery |
| **File Storage** | AWS S3 / MinIO (local) |
| **Integrations** | Shopify, Stripe, Razorpay, Slack, Zendesk, Twilio |
| **Monitoring** | Grafana, Prometheus, Sentry |
| **Deployment** | Docker, Kubernetes, AWS, GitHub Actions |

---

## 🚀 Quick Start

## 🔌 Production Integrations & API Docs

The canonical partner setup is documented in [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md). The running OpenAPI contract is available at `http://localhost:8000/docs` and the machine-readable schema at `http://localhost:8000/openapi.json`.

ArgusCX needs one platform API key for each company integration. Provider credentials are optional per capability and must remain server-side:

| Capability | Credentials | Status in this project |
|---|---|---|
| AI reasoning | `GROQ_API_KEY` | Live Groq path; heuristic fallback without it |
| E-commerce orders/customers | `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_SHOP_DOMAIN` | Live Shopify REST connector |
| Stripe payments | `STRIPE_SECRET_KEY` | Live read connector |
| Razorpay payments | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Live read connector |
| Slack escalation alerts | `SLACK_WEBHOOK_URL` | Live outbound notification |
| Browser/API access | `ARGUSCX_MASTER_KEY` or a generated `acx_live_...` key | Required for protected API routes |
| Evidence storage | none for local demo; S3/MinIO credentials for production storage | Local filesystem currently active |

Zendesk, Intercom, Salesforce, HubSpot, WhatsApp, email, voice, and arbitrary company websites need dedicated adapters or webhooks; they are not automatically supported just by adding a key.

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/arguscx.git
cd arguscx
cp .env.example .env
# Fill in your .env values
```

### 2. Run with Docker Compose (Recommended)
```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

### 3. Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
ArgusCX/
├── frontend/                  # Next.js 14 dashboard
│   ├── src/app/               # App router pages
│   ├── src/components/        # UI components
│   └── src/lib/               # API clients, utils
│
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── agents/            # LangGraph multi-agent system
│   │   ├── api/               # REST routes + WebSockets
│   │   ├── rag/               # RAG pipeline
│   │   ├── services/          # Business logic
│   │   ├── shared/            # Policy engine, prompt manager
│   │   ├── models/            # Pydantic schemas
│   │   └── db/                # Database connections
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example               # All env variables documented
└── README.md
```

---

## 🎯 Demo Scenarios (Hackathon)

1. **Damaged Item + Manipulated Photo** — Fraud detection flags edited image → auto-close with explanation
2. **Payment Dispute** — Cross-checks payment logs → escalates with full case file
3. **Account Takeover Attempt** — High risk score → immediate human handoff with alerts

---

## 👥 Team

*Team Name / College — Hackathon 2026*

---

## 📄 License

MIT
