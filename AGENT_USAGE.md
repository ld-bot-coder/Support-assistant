# Agent Usage Report

## AI Coding Tools Used
- **OpenCode** — primary coding agent for full-stack implementation
- **Ollama Cloud API (gpt-oss:20b)** — LLM for the application's AI workflow (ticket classification, knowledge retrieval, response drafting, action suggestion)

## Work Delegated to OpenCode Agent

### Backend
- `database.py` — SQLAlchemy engine/session setup
- `config.py` — environment configuration with Ollama Cloud API endpoint
- `models.py` — all SQLAlchemy models (Ticket, KnowledgeBase, Communication, ActivityLog with structured fields)
- `schemas.py` — Pydantic request/response schemas including Communication schemas
- `ai_service.py` — Ollama Cloud API integration with centralized `_call_llm` helper, structured return values (model, tokens, latency), full error handling
- `main.py` — FastAPI application with all REST endpoints, communication endpoints, structured activity logging
- `seed_kb.py` — 10 knowledge base seed articles
- `test_main.py` — 33 pytest test cases including mocked AI workflow tests
- `Dockerfile`, `requirements.txt`, `render.yaml`

### Frontend
- Full React SPA with 5 pages (Dashboard, TicketDetail, CreateTicket, KnowledgeBase, ActivityLogs)
- Toast notification component
- CSS styling with loading spinners, progress indicators, communication history styles
- Navigation and state management

### Documentation
- `README.md`, `AGENT_USAGE.md`, `.env.example`

## Representative Prompts

1. "Build a FastAPI backend for a customer support ticket system with SQLite, SQLAlchemy models for Ticket, KnowledgeBase, Communication, and ActivityLog"
2. "Create Ollama Cloud API integration with error handling, structured logging (model, tokens, latency), and graceful fallback"
3. "Build a React frontend with dashboard, ticket detail with edit capability, create ticket with validation, knowledge base, activity logs, and communication history"
4. "Write 33 pytest tests covering all API endpoints including mocked AI workflow tests"
5. "Add Dockerfile for backend deployment and render.yaml configuration"

## Important Agent Mistakes / Rejected Suggestions

1. **OpenAI client vs Ollama API confusion** — agent initially used standard OpenAI endpoint. Corrected to use Ollama Cloud API (`https://ollama.com/v1`) with Bearer token auth.
2. **Mock patching incorrect target** — agent patched `ai_service.client.chat.completions.create` directly, which didn't properly set `response.model` in mocks. Fixed by patching `ai_service._call_llm` instead for cleaner, more reliable mocking.
3. **Activity log test scope too broad** — agent filtered logs by `action.startswith("ai_")` which included the `ai_workflow_completed` summary log (which has empty model_used). Fixed by filtering for specific AI call actions only.
4. **Deprecation warning** — agent used `@app.on_event("startup")` which is deprecated. Migrated to FastAPI `lifespan` pattern.
5. **Test helper functions returning values** — agent wrote test helpers that returned values, causing pytest warnings. Fixed by using private helper functions (`_create_ticket`, `_create_kb_article`).

## Verification of Generated Output

- **Backend**: All 33 tests pass (pytest)
- **Frontend**: Builds successfully (vite build)
- **API validation**: Manual testing with curl/httpie for all CRUD endpoints
- **AI workflow**: Prompt templates reviewed for proper JSON response_format and grounding requirements
- **Error handling**: All AI calls wrapped in try/except with graceful fallback
- **Structured logs**: Verified model_used, tokens_used, latency_ms, status fields in activity logs
- **Communication history**: Endpoints tested for CRUD and listing
- **Edit capability**: PATCH endpoint for draft response tested
