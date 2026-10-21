import os
import chromadb
from chromadb.utils import embedding_functions
from core.database import transactions_db, customers_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")

# 1. Initialize Persistent Chroma Client
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# 2. Setup Local Embedding Function (Runs locally on CPU)
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# 3. Create or Get Collection
collection = chroma_client.get_or_create_collection(
    name="financial_ledger",
    embedding_function=embedding_function
)

def index_transactions_to_vector_store():
    """Converts structured transaction items into semantically rich context text sentences for LLM exploration."""
    
    # Map customer IDs to names for rich phrasing context
    customer_map = {c.id: c.name for c in customers_db}
    
    documents = []
    metadatas = []
    ids = []
    
    for tx in transactions_db:
        customer_name = customer_map.get(tx.customer_id, f"Customer {tx.customer_id}")
        tx_type = "income deposit" if tx.amount > 0 else "expense payment"
        
        # Turn structured transaction details into a natural language sentence
        text_document = (
            f"On {tx.transaction_date}, {customer_name} had a {tx_type} "
            f"titled '{tx.title}' under the '{tx.category}' category "
            f"totaling {abs(tx.amount)} dollars."
        )
        
        documents.append(text_document)
        ids.append(f"tx_{tx.id}")
        metadatas.append({
            "customer_id": tx.customer_id,
            "category": tx.category,
            "amount": tx.amount,
            "date": str(tx.transaction_date)
        })
        
    # Upsert items into Vector Database in batches
    if documents:
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f" Successfully vectorized and indexed {len(documents)} ledger records to ChromaDB.")

def query_financial_history(customer_id: int, user_query: str, n_results: int = 5):
    """Retrieves relevant financial context chunks filtered strictly by individual customer ID."""
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results,
        where={"customer_id": customer_id} # Pre-filtering context ensures security and boundary separation
    )
    # Return flat array of matching strings
    return results['documents'][0] if results['documents'] else []
