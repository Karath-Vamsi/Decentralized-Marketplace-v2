import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3

# AI & RAG Imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI

# Import the build_memory function from your ingest.py
from ingest import build_memory

# --- 1. PATH RESOLUTION ---
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(dotenv_path=ROOT_DIR / ".env")
DB_DIR = str(BASE_DIR / "chroma_db")
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "ExecutiveNFT.sol" / "ExecutiveNFT.json"

# --- 2. CONFIGURATION & INITIALIZATION ---
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL") 
LLM_URL = "http://127.0.0.1:8081/v1" 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    abi = json.load(f)["abi"]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# Global vector_db variable so we can refresh it
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

app = FastAPI(title="AISAAS Sovereign Executive")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- 3. SCHEMAS ---
class QueryRequest(BaseModel):
    prompt: str
    wallet_address: str

class IdentityUpdate(BaseModel):
    content: str
    wallet_address: str

class KnowledgeUpdate(BaseModel):
    filename: str
    content: str
    wallet_address: str

# --- 4. HELPERS ---
def is_authorized(user_wallet_address: str):
    try:
        addr = w3.to_checksum_address(user_wallet_address)
        return contract.functions.hasActiveTwin(addr).call()
    except: return False

def refresh_vector_db():
    """Triggers ingest.py logic and reloads the local vector store."""
    global vector_db
    build_memory() # Run ingest logic
    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# --- 5. ROUTES ---
@app.post("/ask")
async def ask_twin(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")
    
    docs = vector_db.similarity_search(request.prompt, k=3)
    context = "\n---\n".join([doc.page_content for doc in docs])
    
    response = client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": f"You are the 'Sovereign Executive'. Context:\n{context}"},
            {"role": "user", "content": request.prompt}
        ],
        temperature=0.7
    )
    return {"answer": response.choices[0].message.content, "authorized_wallet": request.wallet_address}

# --- UPDATED ROUTES IN server.py ---

@app.post("/update-identity")
async def update_identity(request: IdentityUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    path = BASE_DIR / "knowledge_base" / "identity.txt"
    
    # CHANGED TO "a" (Append) mode
    # Added a newline \n to ensure the new info starts on a fresh line
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{request.content}")
    
    refresh_vector_db() 
    return {"status": "Identity Evolved", "message": "New traits appended."}

@app.post("/add-knowledge")
async def add_knowledge(request: KnowledgeUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # We use a unique filename check to prevent overwriting
    filename = f"{request.filename}.txt"
    path = BASE_DIR / "knowledge_base" / "documents" / filename
    
    if path.exists():
        # If the file exists, we append to it instead of overwriting
        mode = "a"
        content = f"\n{request.content}"
    else:
        # If it's a brand new file, we create it
        mode = "w"
        content = request.content

    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    
    refresh_vector_db()
    return {"status": "Knowledge Added", "file": filename}

@app.get("/list-knowledge")
async def list_knowledge():
    # Path to the documents folder
    docs_path = BASE_DIR / "knowledge_base" / "documents"
    
    # List all .txt files
    try:
        files = [f.name for f in docs_path.glob("*.txt")]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)