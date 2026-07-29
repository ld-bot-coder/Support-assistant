# Knowledge-Grounded Customer Support Assistant

An internal customer-support workspace with AI-powered ticket classification, knowledge retrieval, response drafting, and human review workflow.

## Architecture

```
frontend/  →  React + Vite SPA
backend/   →  FastAPI Python REST API
database/  →  SQLite via SQLAlchemy ORM
AI/        →  Ollama Cloud API (gpt-oss:20b) via OpenAI-compatible client
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama Cloud API key (from https://ollama.com/settings/keys)

### Backend

```bash
cd backend
cp .env.example .env   # add your OPENAI_API_KEY
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:5173

### Tests

```bash
cd backend
python3 -m pytest test_main.py -v
```

## Features

### Core Workflow
1. **Create Ticket** — support agent enters customer type, product area, issue description, optional previous communication, and urgency
2. **Run AI Workflow** — on demand, the AI agent:
   - Classifies issue category and suggests urgency
   - Retrieves relevant knowledge base articles
   - Identifies missing information
   - Generates follow-up questions
   - Drafts a customer response grounded in retrieved knowledge
   - Suggests one internal action (escalate, request clarification, create bug, etc.)
   - Cites all knowledge sources used
3. **Human Review** — agent inspects sources, edits/approves/rejects the drafted response, approves/rejects internal action, updates ticket status
4. **Communication History** — threaded history of agent/customer/system communications per ticket
5. **Audit Trail** — every action is logged with timestamps, model used, tokens consumed, latency, and status

### Pages
- **Dashboard** — ticket list with status filters, empty state handling
- **Ticket Detail** — full ticket view with AI workflow panel, source inspection, approval actions, edit response, communication history
- **Knowledge Base** — manage KB articles (add, view, delete) with validation
- **Activity Logs** — structured audit trail with model, tokens, latency, and status per AI step

### AI Safety
- AI never sends responses or executes actions automatically
- All AI outputs are drafts requiring human approval
- Sources are cited and inspectable
- Activity logs track every AI call with model, tokens, latency
- Graceful error handling: API failures return fallback responses, never crash

## Completed Scope
- Full CRUD for tickets, knowledge base, and communications
- Ollama Cloud API integration (gpt-oss:20b) via OpenAI-compatible client
- Error handling with try/except on all AI calls — graceful fallback on API failures
- Edit capability for AI-drafted response before approval
- Communication history (add/view threaded history per ticket)
- Structured AI workflow logs (model used, tokens, latency, step number, status)
- Human review/approve/reject for draft response and internal action
- 33 backend tests including mocked AI workflow tests
- Knowledge base auto-seeded with 10 sample articles
- SQLite persistence
- Dockerfile and Render deployment config
- Toast notifications, validation errors, loading spinners, progress indicators
- Empty state handling for all views

## Intentionally Excluded
- Authentication/authorization (single-user workspace)
- Real-time updates / WebSocket (polling-based refresh)
- Email integration
- Advanced search/full-text indexing
- Pagination for large ticket volumes
- File attachments
- Rate limiting

## Deployment

### Backend (Render — Docker)
1. Push to GitHub
2. Create a new Web Service on Render
3. Point to `backend/` directory
4. Render uses the `Dockerfile` automatically
5. Add `OPENAI_API_KEY` as environment variable

### Frontend (Vercel)
1. Push to GitHub
2. Import project on Vercel
3. Set root directory to `frontend/`
4. Add env variable `VITE_API_URL` pointing to backend URL
5. Deploy

## Known Limitations
- SQLite is not suitable for production concurrency; migrate to PostgreSQL for multi-user usage
- AI calls have no caching; repeated workflow runs on the same ticket cost tokens
- No authentication — add API key middleware for production
- UI is desktop-first; basic mobile support
