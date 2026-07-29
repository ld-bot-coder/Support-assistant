from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_type = Column(String(100), nullable=False)
    product_area = Column(String(100), nullable=False)
    issue_description = Column(Text, nullable=False)
    previous_communication = Column(Text, default="")
    urgency = Column(String(20), default="medium")
    status = Column(String(50), default="open")

    ai_category = Column(String(100), default="")
    ai_suggested_urgency = Column(String(20), default="")
    ai_classification_raw = Column(Text, default="")
    ai_retrieved_articles = Column(Text, default="[]")
    ai_missing_info = Column(Text, default="[]")
    ai_follow_up_questions = Column(Text, default="[]")
    ai_drafted_response = Column(Text, default="")
    ai_draft_status = Column(String(20), default="pending")
    ai_suggested_action_type = Column(String(100), default="")
    ai_suggested_action_description = Column(Text, default="")
    ai_suggested_action_citations = Column(Text, default="[]")
    ai_action_status = Column(String(20), default="pending")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), default="general")
    tags = Column(String(500), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    sender = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    communication_type = Column(String(50), default="note")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    action = Column(String(200), nullable=False)
    details = Column(Text, default="")
    model_used = Column(String(100), default="")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    step_number = Column(Integer, default=0)
    status = Column(String(20), default="success")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
