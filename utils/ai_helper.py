"""
EventEase — AI Helper Utility
Uses Google Generative AI (Gemini) for all AI features.
"""
import google.generativeai as genai
from config import Config
from db import query


def initialize_gemini():
    """Initialize Gemini API with configured key."""
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    genai.configure(api_key=Config.GEMINI_API_KEY)


def ask_gemini(prompt, system_prompt=None, max_tokens=1000):
    """Call Gemini API with optional system prompt."""
    try:
        initialize_gemini()
        # Using the newest, lightning-fast flash model
        model = genai.GenerativeModel('gemini-2.5-flash') 

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"[System: {system_prompt}]\n\n{prompt}"

        # FIX 1: Lower the safety thresholds so it stops arbitrarily cutting off descriptions
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        response = model.generate_content(
            full_prompt,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
        )
        
        # FIX 2: Diagnostic print to tell you exactly why it stopped typing
        try:
            # 1 = STOP (Natural ending), 2 = MAX_TOKENS (Hit limit), 3 = SAFETY (Blocked)
            finish_reason = response.candidates[0].finish_reason
            print(f"[AI DIAGNOSTIC] Generation stopped because of code: {finish_reason}")
        except Exception:
            pass

        return response.text if response.text else "AI is currently unavailable. Please try again."
        
    except Exception as e:
        import traceback
        error_msg = f"[AI ERROR - Gemini] {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return "AI is currently unavailable. Please try again."


def log_ai_interaction(user_id, prompt, response_text, model_used='gemini'):
    """Logs the interaction to the ai_logs database table."""
    try:
        query(
            "INSERT INTO ai_logs (user_id, prompt, response, model_used) VALUES (%s, %s, %s, %s)",
            (user_id, prompt, response_text, model_used)
        )
    except Exception as e:
        print(f"[DB ERROR - log_ai_interaction] {e}")