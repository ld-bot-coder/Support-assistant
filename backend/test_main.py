import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from seed_kb import seed_knowledge_base

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_db():
    seed_knowledge_base()


def _create_ticket():
    res = client.post("/api/tickets", json={
        "customer_type": "customer",
        "product_area": "billing",
        "issue_description": "I was charged twice for my subscription this month.",
        "previous_communication": "Customer emailed billing@company.com",
        "urgency": "high"
    })
    assert res.status_code == 200
    return res.json()


def _create_kb_article():
    res = client.post("/api/knowledge-base", json={
        "title": "Test Article",
        "content": "This is a test article for testing purposes.",
        "category": "general",
        "tags": "test,sample"
    })
    assert res.status_code == 200
    return res.json()


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_ticket():
    data = _create_ticket()
    assert data["customer_type"] == "customer"
    assert data["product_area"] == "billing"
    assert data["status"] == "open"
    assert data["id"] > 0
    assert "created_at" in data


def test_create_ticket_requires_product_area():
    res = client.post("/api/tickets", json={
        "customer_type": "customer",
        "product_area": "",
        "issue_description": "Test issue"
    })
    assert res.status_code == 200


def test_list_tickets():
    _create_ticket()
    res = client.get("/api/tickets")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_tickets_with_status_filter():
    res = client.get("/api/tickets?status=open")
    assert res.status_code == 200
    for t in res.json():
        assert t["status"] == "open"


def test_get_ticket():
    created = _create_ticket()
    res = client.get(f"/api/tickets/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_ticket_not_found():
    res = client.get("/api/tickets/99999")
    assert res.status_code == 404


def test_update_ticket_status():
    created = _create_ticket()
    res = client.patch(f"/api/tickets/{created['id']}", json={"status": "in_progress"})
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"


def test_update_ticket_draft_response():
    created = _create_ticket()
    new_response = "Thank you for contacting us about your billing issue."
    res = client.patch(f"/api/tickets/{created['id']}", json={
        "ai_drafted_response": new_response,
        "ai_draft_status": "approved"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ai_drafted_response"] == new_response
    assert data["ai_draft_status"] == "approved"


def test_update_ticket_action_status():
    created = _create_ticket()
    res = client.patch(f"/api/tickets/{created['id']}", json={"ai_action_status": "approved"})
    assert res.status_code == 200
    assert res.json()["ai_action_status"] == "approved"


def test_knowledge_base_seeded():
    res = client.get("/api/knowledge-base")
    assert res.status_code == 200
    articles = res.json()
    assert len(articles) > 0
    assert articles[0]["title"]


def test_create_kb_article():
    data = _create_kb_article()
    assert data["title"] == "Test Article"
    assert data["id"] > 0


def test_get_kb_article():
    created = _create_kb_article()
    res = client.get(f"/api/knowledge-base/{created['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == "Test Article"


def test_get_kb_article_not_found():
    res = client.get("/api/knowledge-base/99999")
    assert res.status_code == 404


def test_delete_kb_article():
    created = _create_kb_article()
    res = client.delete(f"/api/knowledge-base/{created['id']}")
    assert res.status_code == 200
    res = client.get(f"/api/knowledge-base/{created['id']}")
    assert res.status_code == 404


def test_list_kb_by_category():
    res = client.get("/api/knowledge-base?category=billing")
    assert res.status_code == 200
    for a in res.json():
        assert a["category"] == "billing"


def test_activity_logs():
    res = client.get("/api/logs")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_activity_logs_by_ticket():
    created = _create_ticket()
    res = client.get(f"/api/logs?ticket_id={created['id']}")
    assert res.status_code == 200
    for log in res.json():
        assert log["ticket_id"] == created["id"]


def test_ticket_update_logs_activity():
    created = _create_ticket()
    client.patch(f"/api/tickets/{created['id']}", json={"status": "resolved"})
    res = client.get(f"/api/logs?ticket_id={created['id']}")
    actions = [log["action"] for log in res.json()]
    assert "ticket_updated" in actions


# === NEW TESTS: Communication endpoints ===

def test_add_communication():
    created = _create_ticket()
    res = client.post(f"/api/tickets/{created['id']}/communications", json={
        "sender": "agent",
        "content": "We have received your complaint and are investigating.",
        "communication_type": "email"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["sender"] == "agent"
    assert data["content"] == "We have received your complaint and are investigating."
    assert data["communication_type"] == "email"
    assert data["ticket_id"] == created["id"]
    assert data["id"] > 0


def test_list_communications():
    created = _create_ticket()
    client.post(f"/api/tickets/{created['id']}/communications", json={
        "sender": "agent", "content": "First message", "communication_type": "note"
    })
    client.post(f"/api/tickets/{created['id']}/communications", json={
        "sender": "customer", "content": "Second message", "communication_type": "email"
    })
    res = client.get(f"/api/tickets/{created['id']}/communications")
    assert res.status_code == 200
    comms = res.json()
    assert len(comms) == 2
    assert comms[0]["sender"] == "agent"
    assert comms[1]["sender"] == "customer"


def test_communications_ticket_not_found():
    res = client.post("/api/tickets/99999/communications", json={
        "sender": "agent", "content": "test"
    })
    assert res.status_code == 404


def test_communications_list_ticket_not_found():
    res = client.get("/api/tickets/99999/communications")
    assert res.status_code == 404


def test_add_communication_logs_activity():
    created = _create_ticket()
    client.post(f"/api/tickets/{created['id']}/communications", json={
        "sender": "agent", "content": "Test communication"
    })
    res = client.get(f"/api/logs?ticket_id={created['id']}")
    actions = [log["action"] for log in res.json()]
    assert "communication_added" in actions


# === NEW TESTS: Edit draft response (PATCH) ===

def test_edit_draft_response():
    created = _create_ticket()
    edited = "Edited response: Thank you for your patience."
    res = client.patch(f"/api/tickets/{created['id']}", json={
        "ai_drafted_response": edited
    })
    assert res.status_code == 200
    assert res.json()["ai_drafted_response"] == edited


# === NEW TESTS: AI Workflow with mocks ===

def _llm_ok(parsed, model="gpt-oss:20b", tokens=150, latency_ms=120.0):
    return {"data": parsed, "model": model, "tokens": tokens, "latency_ms": latency_ms, "error": None}


def _llm_err(error="API rate limit exceeded"):
    return {"data": {}, "model": "gpt-oss:20b", "tokens": 0, "latency_ms": 50.0, "error": error}


@patch("ai_service._call_llm")
def test_ai_workflow_success(mock_llm):
    mock_llm.side_effect = [
        _llm_ok({"category": "billing", "suggested_urgency": "high", "classification_reasoning": "Double charge"}),
        _llm_ok({"relevant_article_ids": [1], "relevance_reasoning": "Article 1 covers billing"}),
        _llm_ok({"missing_info": ["Transaction ID"], "follow_up_questions": ["Can you provide the transaction ID?"]}),
        _llm_ok({"response": "We apologize for the double charge.", "citations": [1], "reasoning": "Used billing article"}),
        _llm_ok({"action_type": "no_action_needed", "description": "Response is sufficient", "reasoning": "Standard billing issue"}),
    ]
    created = _create_ticket()
    res = client.post(f"/api/tickets/{created['id']}/run-ai-workflow")
    assert res.status_code == 200
    data = res.json()
    assert data["ai_category"] == "billing"
    assert data["ai_suggested_urgency"] == "high"
    assert data["ai_drafted_response"] == "We apologize for the double charge."
    assert data["ai_suggested_action_type"] == "no_action_needed"
    assert data["ai_draft_status"] == "pending"


@patch("ai_service._call_llm")
def test_ai_workflow_logs_structured(mock_llm):
    mock_llm.side_effect = [
        _llm_ok({"category": "billing", "suggested_urgency": "high", "classification_reasoning": "Double charge"}),
        _llm_ok({"relevant_article_ids": [1], "relevance_reasoning": "Article 1 covers billing"}),
        _llm_ok({"missing_info": ["Transaction ID"], "follow_up_questions": ["Can you provide the transaction ID?"]}),
        _llm_ok({"response": "We apologize for the double charge.", "citations": [1], "reasoning": "Used billing article"}),
        _llm_ok({"action_type": "no_action_needed", "description": "Response is sufficient", "reasoning": "Standard billing issue"}),
    ]
    created = _create_ticket()
    client.post(f"/api/tickets/{created['id']}/run-ai-workflow")
    res = client.get(f"/api/logs?ticket_id={created['id']}")
    logs = res.json()
    ai_call_logs = [l for l in logs if l["action"] in ("ai_classification", "ai_retrieval", "ai_missing_info", "ai_draft", "ai_action_suggestion")]
    assert len(ai_call_logs) == 5
    for log in ai_call_logs:
        assert log["model_used"] == "gpt-oss:20b"
        assert log["tokens_used"] > 0
        assert log["latency_ms"] >= 0
        assert log["status"] == "success"


@patch("ai_service._call_llm")
def test_ai_workflow_api_error(mock_llm):
    mock_llm.side_effect = [_llm_err("API rate limit exceeded") for _ in range(5)]
    created = _create_ticket()
    res = client.post(f"/api/tickets/{created['id']}/run-ai-workflow")
    assert res.status_code == 200
    data = res.json()
    assert data["ai_category"] == "other"
    assert data["ai_suggested_urgency"] == "medium"
    res_logs = client.get(f"/api/logs?ticket_id={created['id']}")
    error_logs = [l for l in res_logs.json() if l["status"] == "error"]
    assert len(error_logs) > 0


@patch("ai_service._call_llm")
def test_ai_workflow_returns_model_info(mock_llm):
    mock_llm.side_effect = [
        _llm_ok({"category": "billing", "suggested_urgency": "high", "classification_reasoning": "Double charge"}),
        _llm_ok({"relevant_article_ids": [1], "relevance_reasoning": "Article 1 covers billing"}),
        _llm_ok({"missing_info": ["Transaction ID"], "follow_up_questions": ["Can you provide the transaction ID?"]}),
        _llm_ok({"response": "We apologize for the double charge.", "citations": [1], "reasoning": "Used billing article"}),
        _llm_ok({"action_type": "no_action_needed", "description": "Response is sufficient", "reasoning": "Standard billing issue"}),
    ]
    created = _create_ticket()
    res = client.post(f"/api/tickets/{created['id']}/run-ai-workflow")
    data = res.json()
    raw = data.get("ai_classification_raw", "{}")
    import json
    parsed = json.loads(raw)
    assert "_model" in parsed
    assert "_tokens" in parsed
    assert "_latency_ms" in parsed


def test_ai_workflow_ticket_not_found():
    res = client.post("/api/tickets/99999/run-ai-workflow")
    assert res.status_code == 404


def test_activity_logs_structured_fields():
    created = _create_ticket()
    client.patch(f"/api/tickets/{created['id']}", json={"status": "resolved"})
    res = client.get(f"/api/logs?ticket_id={created['id']}")
    logs = res.json()
    assert len(logs) > 0
    log = logs[0]
    assert "model_used" in log
    assert "tokens_used" in log
    assert "latency_ms" in log
    assert "step_number" in log
    assert "status" in log


def test_kb_article_not_found():
    res = client.get("/api/knowledge-base/99999")
    assert res.status_code == 404


def test_update_nonexistent_ticket():
    res = client.patch("/api/tickets/99999", json={"status": "resolved"})
    assert res.status_code == 404
