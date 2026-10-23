import logging
from fastapi import APIRouter, HTTPException, Depends
from google import genai
from google.genai import types
import ollama

from core.schemas import AdviceRequest, Customer
from core.auth import get_current_user
from core.vector_db import query_financial_history

logger = logging.getLogger("api_advisor")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/advisor", tags=["AI Financial Advisor"])

try:
    gemini_client = genai.Client()
except Exception:
    gemini_client = None

# --- IN-MEMORY CONVERSATION STATE DATABASE ---
# Structure: { f"{customer_id}_{session_id}": [ {"role": "user/model", "text": "..."} ] }
chat_history_db = {}


def get_formatted_history(history_key: str) -> list:
    """Returns the chat session log formatted for Gemini Content structures."""
    formatted = []
    if history_key in chat_history_db:
        for msg in chat_history_db[history_key]:
            role = "user" if msg["role"] == "user" else "model"
            formatted.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["text"])]
                )
            )
    return formatted


# --- SECURED POST ROUTE: MULTI-TURN AI CHAT ADVISOR ---
@router.post("/customer/{customer_id}")
def get_financial_advice(customer_id: int, request: AdviceRequest, current_user: Customer = Depends(get_current_user)):
    # 🔒 CROSS-TENANT SECURITY GATECHECK
    if current_user.id != customer_id:
        raise HTTPException(status_code=403, detail="Forbidden: Unauthorized profile access attempt.")

    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini client uninitialized. Check your .env setup.")

    # 1. Generate unique cache key for this user conversation thread session
    history_key = f"{customer_id}_{request.session_id}"
    
    # 2. Retrieve relevant historical text snippets from ChromaDB vector store
    relevant_context = query_financial_history(customer_id=customer_id, user_query=request.query)
    context_str = "\n".join([f"- {doc}" for doc in relevant_context]) if relevant_context else "No baseline context found."

    # 3. Pull previous chat conversation log logs
    past_turns = get_formatted_history(history_key)

    # 4. Formulate the system instruction with precise text formatting constraints
    system_instruction = (
        "You are a helpful, professional fintech AI personal banking advisor. "
        "Answer the user queries truthfully, politely, and concisely using only factual records.\n\n"
        "CRITICAL TEXT SPACING & FORMATTING RULES:\n"
        "- NEVER output a raw single '$' character as it breaks the frontend layout engine.\n"
        "- ALWAYS display money figures by writing out 'USD' after the numeric amount separated by a clear space (e.g., write '54.63 USD' or '28.51 USD').\n"
        "- Ensure explicit whitespace separation between values, operators, and words (e.g., say '54.63 USD on Movie Tickets', NOT '54.63onMovieTickets').\n"
        "- Always space sub-items cleanly when breaking down components inside brackets (e.g., write '(28.51 USD and 26.12 USD)')."
    )
    
    current_turn_prompt = (
        f"--- RELEVANT TRANSACTION LEDGER CONTEXT ---\n{context_str}\n\n"
        f"--- USER QUESTION ---\n{request.query}\n\n"
        f"Instructions: Use the transaction ledger context above to inform your answer if relevant to the question. "
        f"Remember previous turns if the user asks a follow-up question."
    )

    # 5. Append current user query context to the persistent history log dict BEFORE generation
    if history_key not in chat_history_db:
        chat_history_db[history_key] = []
    chat_history_db[history_key].append({"role": "user", "text": request.query})

    # --- EXECUTION ENGINE: PRIMARY GEMINI 3.5 FLASH LITE ---
    try:
        logger.info(f"Executing stateful multi-turn text generation for session thread: {history_key}")
        
        full_contents = past_turns + [
            types.Content(role="user", parts=[types.Part.from_text(text=current_turn_prompt)])
        ]

        response = gemini_client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=full_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )

        ai_response_text = response.text.strip()
        chat_history_db[history_key].append({"role": "model", "text": ai_response_text})

        return {
            "customer_id": customer_id,
            "session_id": request.session_id,
            "advice": ai_response_text,
            "engine_used": "gemini-3.5-flash-lite (stateful multi-turn)"
        }

    except Exception as gemini_err:
        logger.warning(f"Stateful Gemini call failed: {str(gemini_err)}. Falling back to local stateless Ollama query...")
        
        # --- OLLAMA FALLBACK ROUTE ---
        try:
            ollama_response = ollama.generate(
                model="llama3",
                prompt=f"{system_instruction}\n\nContext:\n{context_str}\n\nQuestion: {request.query}"
            )
            ai_response_text = ollama_response['response'].strip()
            chat_history_db[history_key].append({"role": "model", "text": ai_response_text})
            
            return {
                "customer_id": customer_id,
                "session_id": request.session_id,
                "advice": ai_response_text,
                "engine_used": "ollama-llama3 (local fallback)"
            }
        except Exception as ollama_err:
            raise HTTPException(status_code=503, detail=f"All generation channels failed: {str(ollama_err)}")
