import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
import ollama
from core.vector_db import query_financial_history

logger = logging.getLogger("api_advisor")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/advisor", tags=["AI Financial Advisor"])

# Initialize primary Gemini client
try:
    gemini_client = genai.Client()
except Exception:
    gemini_client = None

class AdviceRequest(BaseModel):
    query: str

@router.post("/customer/{customer_id}")
def get_financial_advice(customer_id: int, request: AdviceRequest):
    # 1. Gather context from Vector DB (ChromaDB)
    relevant_context = query_financial_history(customer_id=customer_id, user_query=request.query)
    
    if not relevant_context:
        raise HTTPException(status_code=404, detail="No historical transaction records found matching context.")
        
    # 2. Build the unified prompt context
    context_str = "\n".join([f"- {doc}" for doc in relevant_context])
    llm_prompt = (
        f"You are a helpful, professional fintech AI advisor. Below is a subset of the customer's real ledger logs "
        f"retrieved from their profile relevant to their question.\n\n"
        f"--- RELEVANT TRANSACTION CONTEXT ---\n{context_str}\n\n"
        f"--- USER QUESTION ---\n{request.query}\n\n"
        f"Instructions: Answer the user query using only the provided context facts truthfully and concisely."
    )
    
    # --- STRATEGY: TRY GEMINI 3.5 FLASH LITE FIRST ---
    if gemini_client is not None:
        try:
            logger.info("Attempting advice generation via primary engine: Gemini 3.5 Flash-Lite...")
            response = gemini_client.models.generate_content(
                model='gemini-3.5-flash-lite',  # Updated model string
                contents=llm_prompt,
            )
            return {
                "customer_id": customer_id,
                "query": request.query,
                "advice": response.text,
                "engine_used": "gemini-3.5-flash-lite"
            }
        except Exception as gemini_err:
            logger.warning(f"Primary Gemini engine failed: {str(gemini_err)}. Dropping to local fallback container...")

    else:
        logger.warning("Gemini Client uninitialized. Activating immediate local route...")

    # --- FALLBACK: TRY LOCAL OLLAMA CONTAINER ---
    try:
        logger.info("Generating advice via local fallback engine: Ollama (llama3)...")
        ollama_response = ollama.generate(
            model="llama3",
            prompt=llm_prompt
        )
        return {
            "customer_id": customer_id,
            "query": request.query,
            "advice": ollama_response['response'],
            "engine_used": "ollama-llama3 (local fallback)"
        }
    except Exception as ollama_err:
        logger.error(f"Both primary and fallback AI engines failed execution: {str(ollama_err)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Financial Advisor Service temporarily unavailable. System Error: {str(ollama_err)}"
        )
