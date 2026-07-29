import json
import time
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        latency = (time.time() - start) * 1000
        raw = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {}
        return {
            "data": parsed,
            "model": response.model or OPENAI_MODEL,
            "tokens": tokens,
            "latency_ms": round(latency, 1),
            "error": None
        }
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            "data": {},
            "model": OPENAI_MODEL,
            "tokens": 0,
            "latency_ms": round(latency, 1),
            "error": str(e)
        }


def classify_issue(issue_description: str, customer_type: str, product_area: str, previous_communication: str = "") -> dict:
    system_prompt = "You are a precise ticket classifier. Always respond with valid JSON only."
    user_prompt = f"""You are a customer support classifier for a SaaS company. Analyze the following support ticket and return a JSON object.

Customer Type: {customer_type}
Product Area: {product_area}
Issue Description: {issue_description}
Previous Communication: {previous_communication or "None"}

Return a JSON object with these exact keys:
- "category": one of ["billing", "technical", "account", "feature_request", "bug_report", "other"]
- "suggested_urgency": one of ["low", "medium", "high", "critical"]
- "classification_reasoning": a short explanation of your classification
"""
    result = _call_llm(system_prompt, user_prompt, temperature=0.2)
    if result["error"]:
        return {"category": "other", "suggested_urgency": "medium", "classification_reasoning": "AI service unavailable", "_error": result["error"], "_model": result["model"], "_tokens": result["tokens"], "_latency_ms": result["latency_ms"]}
    data = result["data"]
    data["category"] = data.get("category", "other")
    data["suggested_urgency"] = data.get("suggested_urgency", "medium")
    data["classification_reasoning"] = data.get("classification_reasoning", "")
    data["_model"] = result["model"]
    data["_tokens"] = result["tokens"]
    data["_latency_ms"] = result["latency_ms"]
    return data


def retrieve_knowledge_articles(issue_description: str, product_area: str, kb_articles: list) -> list:
    system_prompt = "You retrieve relevant knowledge base articles. Return ONLY numeric article IDs. Respond with valid JSON only."
    user_prompt = f"""Given this support issue and the available knowledge base articles, identify which articles are relevant. Only include articles that can help address this issue.

Issue: {issue_description[:500]}
Product Area: {product_area}

Available articles:
{json.dumps([{"id": a["id"], "title": a["title"], "category": a["category"], "tags": a["tags"], "content_preview": a["content"][:300]} for a in kb_articles], indent=2)}

Return a JSON object with:
- "relevant_article_ids": list of integer article IDs (e.g., [2, 5]) that could help address this issue IMPORTANT: use integers not strings
- "relevance_reasoning": brief explanation for each selected article
"""
    result = _call_llm(system_prompt, user_prompt, temperature=0.2)
    if result["error"]:
        return {"relevant_article_ids": [], "relevance_reasoning": "AI service unavailable", "_error": result["error"], "_model": result["model"], "_tokens": result["tokens"], "_latency_ms": result["latency_ms"]}
    data = result["data"]
    ids = data.get("relevant_article_ids", [])
    data["relevant_article_ids"] = [int(i) if isinstance(i, (int, str)) and str(i).isdigit() else i for i in ids]
    data["_model"] = result["model"]
    data["_tokens"] = result["tokens"]
    data["_latency_ms"] = result["latency_ms"]
    return data


def identify_missing_information(issue_description: str, customer_type: str, product_area: str, previous_communication: str = "") -> dict:
    system_prompt = "You are a support agent assistant. Identify what critical information is missing from this ticket. ALWAYS provide at least one missing item or follow-up question. Respond with valid JSON only."
    user_prompt = f"""Given this support ticket, identify what important information is missing that a support agent would need to resolve the issue. You MUST provide at least one item in each list.

Customer Type: {customer_type}
Product Area: {product_area}
Issue Description: {issue_description}
Previous Communication: {previous_communication or "None"}

Think about: account/order IDs, error messages, timestamps, affected users, screenshots, steps to reproduce, environment details, expected vs actual behavior.

Return JSON with:
- "missing_info": list of strings describing missing details needed for resolution (include at least 1 item)
- "follow_up_questions": list of specific, actionable questions to ask the customer (include at least 1 item)
"""
    result = _call_llm(system_prompt, user_prompt, temperature=0.3)
    if result["error"]:
        return {"missing_info": ["Unable to determine - AI service error"], "follow_up_questions": ["Please provide more details about your issue"], "_error": result["error"], "_model": result["model"], "_tokens": result["tokens"], "_latency_ms": result["latency_ms"]}
    data = result["data"]
    data["missing_info"] = data.get("missing_info", []) or ["No specific missing info identified"]
    data["follow_up_questions"] = data.get("follow_up_questions", []) or ["Can you provide additional details about this issue?"]
    data["_model"] = result["model"]
    data["_tokens"] = result["tokens"]
    data["_latency_ms"] = result["latency_ms"]
    return data


def draft_response(issue_description: str, customer_type: str, product_area: str,
                   previous_communication: str, urgency: str, kb_articles: list,
                   missing_info: list, follow_up_questions: list) -> dict:
    articles_text = "\n\n".join([
        f"Article ID {a['id']}: {a['title']}\n{a['content'][:500]}"
        for a in kb_articles
    ])
    article_ids = [a["id"] for a in kb_articles]
    system_prompt = "You draft helpful, professional customer support responses. Use ONLY facts from the provided knowledge articles. Do NOT invent phone numbers, URLs, refund amounts, timelines, or policies not in the articles. Respond with valid JSON only."
    user_prompt = f"""Draft a customer support response for this ticket. Base your response on the provided knowledge base articles. If the articles don't fully answer the issue, be helpful but honest and ask the customer for the missing details listed below.

Customer Type: {customer_type}
Product Area: {product_area}
Issue Description: {issue_description}
Previous Communication: {previous_communication or "None"}
Urgency: {urgency}

Knowledge Base Articles:
{articles_text}

Missing Information to Ask For: {json.dumps(missing_info)}
Follow-up Questions: {json.dumps(follow_up_questions)}

IMPORTANT RULES:
1. ALWAYS write a non-empty, complete response
2. Reference only procedures, policies, and contact details from the articles above
3. Do NOT invent phone numbers, email addresses, URLs, refund guarantees, or timelines
4. Use the follow-up questions when the articles don't provide enough information to resolve the issue directly
5. Citations must be one of these article IDs: {article_ids}

Return a JSON object with:
- "response": the drafted customer response (ALWAYS non-empty, helpful, and grounded in the articles)
- "citations": list of NUMERIC article IDs used from {article_ids} — integers only, e.g., [2, 8]
- "reasoning": brief explanation of how the articles were used
"""
    result = _call_llm(system_prompt, user_prompt, temperature=0.4)
    if result["error"]:
        return {"response": "Unable to draft response. AI service unavailable.", "citations": [], "reasoning": result["error"], "_error": result["error"], "_model": result["model"], "_tokens": result["tokens"], "_latency_ms": result["latency_ms"]}
    data = result["data"]
    response = data.get("response", "").strip()
    if not response:
        response = "Thank you for contacting us. We have received your request and are reviewing the available information. We may need a few additional details from you to proceed."
    data["response"] = response
    citations = data.get("citations", [])
    data["citations"] = [int(c) if isinstance(c, (int, str)) and str(c).isdigit() else c for c in citations]
    data["_model"] = result["model"]
    data["_tokens"] = result["tokens"]
    data["_latency_ms"] = result["latency_ms"]
    return data


def suggest_internal_action(issue_description: str, category: str, urgency: str,
                            product_area: str, kb_articles_used: list) -> dict:
    system_prompt = "You suggest internal actions for support tickets based on analysis. Respond with valid JSON only."
    user_prompt = f"""Based on this support ticket analysis, suggest one internal action for the support team.

Issue: {issue_description[:500]}
Category: {category}
Urgency: {urgency}
Product Area: {product_area}
Knowledge Articles Used: {json.dumps([{"id": a["id"], "title": a["title"]} for a in kb_articles_used])}

Choose from these action types:
- "request_clarification": need more info from customer
- "escalate_technical": hand off to engineering
- "create_bug": file a bug report internally
- "update_documentation": KB articles need updating
- "no_action_needed": response is sufficient

Return JSON with:
- "action_type": one of the above
- "description": detailed description of the suggested action
- "reasoning": why this action is needed, citing relevant knowledge by article ID
"""
    result = _call_llm(system_prompt, user_prompt, temperature=0.3)
    if result["error"]:
        return {"action_type": "no_action_needed", "description": "AI service unavailable", "reasoning": result["error"], "_error": result["error"], "_model": result["model"], "_tokens": result["tokens"], "_latency_ms": result["latency_ms"]}
    data = result["data"]
    data["_model"] = result["model"]
    data["_tokens"] = result["tokens"]
    data["_latency_ms"] = result["latency_ms"]
    return data
