import json
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from contextlib import asynccontextmanager
from database import engine, get_db, Base
from models import Ticket, KnowledgeBase, ActivityLog, Communication
from schemas import (
    TicketCreate, TicketUpdate, TicketOut,
    KnowledgeBaseCreate, KnowledgeBaseOut,
    ActivityLogOut, CommunicationCreate, CommunicationOut
)
from ai_service import classify_issue, retrieve_knowledge_articles, identify_missing_information, draft_response, suggest_internal_action
from seed_kb import seed_knowledge_base

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_knowledge_base()
    yield


app = FastAPI(title="Support Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def log_activity(db: Session, ticket_id: int | None, action: str, details: str = "",
                 model_used: str = "", tokens_used: int = 0, latency_ms: float = 0.0,
                 step_number: int = 0, status: str = "success"):
    log = ActivityLog(
        ticket_id=ticket_id, action=action, details=details,
        model_used=model_used, tokens_used=tokens_used, latency_ms=latency_ms,
        step_number=step_number, status=status
    )
    db.add(log)
    db.commit()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/tickets", response_model=TicketOut)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    db_ticket = Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    log_activity(db, db_ticket.id, "ticket_created", f"Ticket created by {ticket.customer_type}")
    return db_ticket


@app.get("/api/tickets", response_model=list[TicketOut])
def list_tickets(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).all()


@app.get("/api/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/api/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, update: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    log_activity(db, ticket_id, "ticket_updated", json.dumps(update_data))
    return ticket


@app.post("/api/tickets/{ticket_id}/run-ai-workflow", response_model=TicketOut)
def run_ai_workflow(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status in ("resolved", "closed"):
        raise HTTPException(status_code=400, detail="Cannot run AI workflow on resolved or closed tickets")

    is_rerun = ticket.ai_category != ""
    draft_protected = ticket.ai_draft_status == "approved"
    action_protected = ticket.ai_action_status == "approved"

    if is_rerun:
        ticket.ai_draft_status = "pending"
        ticket.ai_action_status = "pending"

    step = 0

    classification = classify_issue(ticket.issue_description, ticket.customer_type, ticket.product_area, ticket.previous_communication)
    ticket.ai_category = classification.get("category", "")
    ticket.ai_suggested_urgency = classification.get("suggested_urgency", "")
    ticket.ai_classification_raw = json.dumps(classification)
    step += 1
    log_activity(db, ticket_id, "ai_classification", json.dumps(classification),
                 model_used=classification.get("_model", ""), tokens_used=classification.get("_tokens", 0),
                 latency_ms=classification.get("_latency_ms", 0), step_number=step,
                 status="error" if classification.get("_error") else "success")

    all_articles = db.query(KnowledgeBase).all()
    kb_list = [{"id": a.id, "title": a.title, "content": a.content, "category": a.category, "tags": a.tags} for a in all_articles]
    retrieval_result = retrieve_knowledge_articles(ticket.issue_description, ticket.product_area, kb_list)
    relevant_ids = retrieval_result.get("relevant_article_ids", [])
    relevant_articles = [a for a in all_articles if a.id in relevant_ids]
    ticket.ai_retrieved_articles = json.dumps([{"id": a.id, "title": a.title, "content": a.content, "category": a.category} for a in relevant_articles])
    step += 1
    log_activity(db, ticket_id, "ai_retrieval", json.dumps(retrieval_result),
                 model_used=retrieval_result.get("_model", ""), tokens_used=retrieval_result.get("_tokens", 0),
                 latency_ms=retrieval_result.get("_latency_ms", 0), step_number=step,
                 status="error" if retrieval_result.get("_error") else "success")

    info_result = identify_missing_information(ticket.issue_description, ticket.customer_type, ticket.product_area, ticket.previous_communication)
    ticket.ai_missing_info = json.dumps(info_result.get("missing_info", []))
    ticket.ai_follow_up_questions = json.dumps(info_result.get("follow_up_questions", []))
    step += 1
    log_activity(db, ticket_id, "ai_missing_info", json.dumps(info_result),
                 model_used=info_result.get("_model", ""), tokens_used=info_result.get("_tokens", 0),
                 latency_ms=info_result.get("_latency_ms", 0), step_number=step,
                 status="error" if info_result.get("_error") else "success")

    if relevant_articles:
        if not draft_protected:
            draft_result = draft_response(
                ticket.issue_description, ticket.customer_type, ticket.product_area,
                ticket.previous_communication, ticket.urgency,
                [{"id": a.id, "title": a.title, "content": a.content} for a in relevant_articles],
                info_result.get("missing_info", []), info_result.get("follow_up_questions", [])
            )
            ticket.ai_drafted_response = draft_result.get("response", "")
            citations = draft_result.get("citations", [])
            step += 1
            log_activity(db, ticket_id, "ai_draft", json.dumps(draft_result),
                         model_used=draft_result.get("_model", ""), tokens_used=draft_result.get("_tokens", 0),
                         latency_ms=draft_result.get("_latency_ms", 0), step_number=step,
                         status="error" if draft_result.get("_error") else "success")
        else:
            citations = [a.id for a in relevant_articles]
            step += 1
            log_activity(db, ticket_id, "ai_draft", "Draft preserved - previously approved", step_number=step, status="skipped")

        if not action_protected:
            action_result = suggest_internal_action(
                ticket.issue_description, classification.get("category", ""),
                classification.get("suggested_urgency", ""), ticket.product_area,
                [{"id": a.id, "title": a.title} for a in relevant_articles]
            )
            ticket.ai_suggested_action_type = action_result.get("action_type", "")
            ticket.ai_suggested_action_description = action_result.get("description", "")
            ticket.ai_suggested_action_citations = json.dumps({"citations": citations, "action_reasoning": action_result.get("reasoning", "")})
            step += 1
            log_activity(db, ticket_id, "ai_action_suggestion", json.dumps(action_result),
                         model_used=action_result.get("_model", ""), tokens_used=action_result.get("_tokens", 0),
                         latency_ms=action_result.get("_latency_ms", 0), step_number=step,
                         status="error" if action_result.get("_error") else "success")
        else:
            step += 1
            log_activity(db, ticket_id, "ai_action_suggestion", "Action preserved - previously approved", step_number=step, status="skipped")
    else:
        if not draft_protected:
            ticket.ai_drafted_response = "No relevant knowledge articles found to base a response on. Please review manually."
        ticket.ai_suggested_action_type = "request_clarification"
        ticket.ai_suggested_action_description = "No relevant KB articles found. Manual review needed."

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    log_activity(db, ticket_id, "ai_workflow_completed", "Full AI workflow executed", step_number=step)
    return ticket


def safe_parse_citations(raw: str):
    try:
        return json.loads(raw).get("citations", []) if raw else []
    except (json.JSONDecodeError, AttributeError):
        return []


@app.post("/api/knowledge-base", response_model=KnowledgeBaseOut)
def create_kb_article(article: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    db_article = KnowledgeBase(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    log_activity(db, None, "kb_article_created", f"Article '{article.title}' added")
    return db_article


@app.get("/api/knowledge-base", response_model=list[KnowledgeBaseOut])
def list_kb_articles(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgeBase)
    if category:
        query = query.filter(KnowledgeBase.category == category)
    return query.all()


@app.get("/api/knowledge-base/{article_id}", response_model=KnowledgeBaseOut)
def get_kb_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.delete("/api/knowledge-base/{article_id}")
def delete_kb_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    log_activity(db, None, "kb_article_deleted", f"Article '{article.title}' deleted")
    return {"ok": True}


@app.post("/api/tickets/{ticket_id}/communications", response_model=CommunicationOut)
def add_communication(ticket_id: int, comm: CommunicationCreate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db_comm = Communication(ticket_id=ticket_id, **comm.model_dump())
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)
    log_activity(db, ticket_id, "communication_added", f"{comm.sender}: {comm.content[:100]}")
    return db_comm


@app.get("/api/tickets/{ticket_id}/communications", response_model=list[CommunicationOut])
def list_communications(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db.query(Communication).filter(Communication.ticket_id == ticket_id).order_by(Communication.created_at.asc()).all()


@app.get("/api/logs", response_model=list[ActivityLogOut])
def list_logs(ticket_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(ActivityLog)
    if ticket_id:
        query = query.filter(ActivityLog.ticket_id == ticket_id)
    return query.order_by(ActivityLog.created_at.desc()).limit(200).all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
