from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from core.vector_db import query_financial_history

router = APIRouter(prefix="/advisor", tags=["AI Financial Advisor"])

# Initializes seamlessly by pulling the key straight out of operational memory
try:
    client = genai.Client()
except Exception:
    client = None

class AdviceRequest(BaseModel):
    query: str

@router.post("/customer/{customer_id}")
def get_financial_advice(customer_id: int, request: AdviceRequest):
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="Gemini Client is uninitialized. Ensure GEMINI_API_KEY is present in your .env file."
        )

    relevant_context = query_financial_history(customer_id=customer_id, user_query=request.query)
    
    if not relevant_context:
        raise HTTPException(status_code=404, detail="No historical transaction records found matching context.")
        
    context_str = "\n".join([f"- {doc}" for doc in relevant_context])
    
    llm_prompt = (
        f"You are a helpful, professional fintech AI advisor. Below is a subset of the customer's real ledger logs "
        f"retrieved from their profile relevant to their question.\n\n"
        f"--- RELEVANT TRANSACTION CONTEXT ---\n{context_str}\n\n"
        f"--- USER QUESTION ---\n{request.query}\n\n"
        f"Instructions: Answer the user query using only the provided context facts truthfully and concisely."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=llm_prompt,
        )
        
        return {
            "customer_id": customer_id,
            "query": request.query,
            "advice": response.text
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate advice from Gemini engine: {str(e)}"
        )
