from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class TicketCreate(BaseModel):
    customer_type: str
    product_area: str
    issue_description: str
    previous_communication: str = ""
    urgency: str = "medium"


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    ai_drafted_response: Optional[str] = None
    ai_draft_status: Optional[str] = None
    ai_action_status: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    customer_type: str
    product_area: str
    issue_description: str
    previous_communication: str
    urgency: str
    status: str

    ai_category: str
    ai_suggested_urgency: str
    ai_classification_raw: str
    ai_retrieved_articles: str
    ai_missing_info: str
    ai_follow_up_questions: str
    ai_drafted_response: str
    ai_draft_status: str
    ai_suggested_action_type: str
    ai_suggested_action_description: str
    ai_suggested_action_citations: str
    ai_action_status: str

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: str = ""


class KnowledgeBaseOut(BaseModel):
    id: int
    title: str
    content: str
    category: str
    tags: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunicationCreate(BaseModel):
    sender: str
    content: str
    communication_type: str = "note"


class CommunicationOut(BaseModel):
    id: int
    ticket_id: int
    sender: str
    content: str
    communication_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogOut(BaseModel):
    id: int
    ticket_id: Optional[int] = None
    action: str
    details: str
    model_used: str
    tokens_used: int
    latency_ms: float
    step_number: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
