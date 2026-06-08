"""
EventEase — AI Routes
Endpoints for interacting with Gemini API
"""
import json
from flask import Blueprint, request, jsonify, session
from utils.decorators import role_required, login_required
from utils.ai_helper import ask_gemini, log_ai_interaction
from db import query

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message', '')
    user_id = session['user_id']
    role = session.get('role', 'user')

    sys_prompt = f"You are EventEase AI, a helpful platform assistant. The user you are talking to is a {role}. Be concise, helpful, and friendly."

    response = ask_gemini(message, system_prompt=sys_prompt, max_tokens=500)
    log_ai_interaction(user_id, message, response, 'gemini')

    return jsonify({"reply": response})


@ai_bp.route('/generate-description', methods=['POST'])
@role_required('creator')
def generate_description():
    data = request.get_json()
    title = data.get('title', 'Unknown Event')
    type_ = data.get('type', 'event')
    venue = data.get('venue', 'TBD')
    date_start = data.get('date_start', 'TBD')

    sys_prompt = "You are an expert event copywriter. Write an engaging 150-word event description based on these details. Be enthusiastic, professional, and include key highlights."
    prompt = f"Title: {title}\nType: {type_}\nVenue: {venue}\nDate: {date_start}"

    response = ask_gemini(prompt, system_prompt=sys_prompt, max_tokens=300)
    log_ai_interaction(session['user_id'], f"Generate description for: {title}", response, 'gemini')

    return jsonify({"description": response})


@ai_bp.route('/suggest-pricing', methods=['POST'])
@role_required('creator')
def suggest_pricing():
    data = request.get_json()
    type_ = data.get('type', 'event')
    city = data.get('city', 'Unknown City')
    capacity = data.get('capacity', 100)

    sys_prompt = "You are a pricing expert for events in India. Suggest a fair ticket price in Indian Rupees. Always respond with ONLY valid JSON format: {\"price\": 499, \"reason\": \"...\"}"
    prompt = f"Suggest a fair ticket price for a {type_} event in {city} with {capacity} capacity."

    raw_response = ask_gemini(prompt, system_prompt=sys_prompt, max_tokens=150)

    # JSON extraction with fallback
    try:
        import re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            price = parsed.get("price", 499)
            reason = parsed.get("reason", "Based on market research.")
        else:
            price = 499
            reason = raw_response
    except Exception:
        price = 499
        reason = "Using default pricing suggestion."

    log_ai_interaction(session['user_id'], f"Suggest pricing for {type_} in {city}", f"Price: {price}. Reason: {reason}", 'gemini')
    return jsonify({"price": price, "reason": reason})


@ai_bp.route('/write-promo', methods=['POST'])
@role_required('creator')
def write_promo():
    data = request.get_json()
    title = data.get('title', 'Event')
    type_ = data.get('type', 'Event')
    city = data.get('city', 'City')

    sys_prompt = "You are a social media manager. Write a punchy 3-sentence WhatsApp/social media promotional message with emojis and a call-to-action."
    prompt = f"Event: {title}\nType: {type_}\nCity: {city}"

    response = ask_gemini(prompt, system_prompt=sys_prompt, max_tokens=150)
    log_ai_interaction(session['user_id'], f"Promo for {title}", response, 'gemini')

    return jsonify({"promo_text": response})


@ai_bp.route('/smart-search', methods=['POST'])
def smart_search():
    data = request.get_json()
    query_text = data.get('query', '')
    user_id = session.get('user_id', None)

    sys_prompt = "Extract search filters from the user query and return ONLY valid JSON: {\"type\": \"...\", \"city\": \"...\", \"price_range\": \"...\"}. Use empty strings for unknown fields."
    prompt = f"User search query: \"{query_text}\""

    raw_response = ask_gemini(prompt, system_prompt=sys_prompt, max_tokens=100)

    try:
        import re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        filters = json.loads(json_match.group(0)) if json_match else {}
    except Exception:
        filters = {}

    if user_id:
        log_ai_interaction(user_id, f"Smart search: {query_text}", json.dumps(filters), 'gemini')

    return jsonify(filters)


@ai_bp.route('/moderate-event', methods=['POST'])
@role_required('admin')
def moderate_event():
    data = request.get_json()
    event_id = data.get('event_id')

    event = query("SELECT title, description, venue FROM events WHERE id=%s", (event_id,), fetchone=True)
    if not event:
        return jsonify({"status": "Warning", "reason": "Event not found."}), 404

    sys_prompt = "Review this event for policy violations, scams, or inappropriate content. Rate as Safe, Warning, or Flagged. Return ONLY JSON: {\"status\": \"Safe/Warning/Flagged\", \"reason\": \"...\"}"
    prompt = f"Title: {event['title']}\nDesc: {event['description']}\nVenue: {event['venue']}"

    raw_response = ask_gemini(prompt, system_prompt=sys_prompt, max_tokens=150)

    try:
        import re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            status = parsed.get("status", "Warning")
            reason = parsed.get("reason", raw_response)
        else:
            status = "Warning"
            reason = "Could not parse AI response."
    except Exception:
        status = "Warning"
        reason = "AI review failed."

    log_ai_interaction(session['user_id'], f"Moderate event {event_id}", f"Status: {status}. Reason: {reason}", 'gemini')
    return jsonify({"status": status, "reason": reason})

