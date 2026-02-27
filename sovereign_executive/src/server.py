import os
import json
import time # <--- Added
import random # <--- Added
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI

from navigator import select_best_agent, format_specialist_input, get_all_registered_agents
from a2a_client import call_specialist_agent
from ingest import build_memory

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(dotenv_path=ROOT_DIR / ".env")
DB_DIR = str(BASE_DIR / "chroma_db")
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "ExecutiveNFT.sol" / "ExecutiveNFT.json"

CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL") 
LLM_URL = "http://127.0.0.1:8090/v1" 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open(ABI_PATH) as f:
    abi = json.load(f)["abi"]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

app = FastAPI(title="AISAAS Sovereign Executive")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

def is_authorized(user_wallet_address: str):
    try:
        addr = w3.to_checksum_address(user_wallet_address)
        return contract.functions.hasActiveTwin(addr).call()
    except: 
        return False

def refresh_vector_db():
    global vector_db
    build_memory()
    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

@app.post("/ask")
async def ask_twin(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")

    print(f"\n Executive Brain: Evaluating task: '{request.prompt[:50]}...'")
    specialist = select_best_agent(request.prompt)

    if specialist:
        print(f" Specialist Found: {specialist['name']}. Delegating task...")
        
        #  THE DRAMATIC PAUSE
        sleep_time = random.uniform(1.5, 3.0)
        print(f" Simulating A2A Handshake Protocol... ({sleep_time:.1f}s delay)")
        time.sleep(sleep_time)
        
        payload = format_specialist_input(request.prompt, specialist['card'])
        worker_result = call_specialist_agent(specialist['card'], payload)
        
        if worker_result:
            raw_val = (
                worker_result.get("result") or 
                worker_result.get("message") or 
                worker_result.get("rewritten_text")
            )
            final_answer = str(raw_val).split("<|")[0].strip()

            return {
                "answer": final_answer,
                "source": f"VERIFIED: {specialist['name']}",
                "data": worker_result,
                "authorized_wallet": request.wallet_address
            }
        
    print(" No specialist used. Consulting internal RAG memory...")
    docs = vector_db.similarity_search(request.prompt, k=3)
    context = "\n---\n".join([doc.page_content for doc in docs])
    
    response = client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": f"You are the 'Sovereign Executive'. Use this context:\n{context}"},
            {"role": "user", "content": request.prompt}
        ],
        temperature=0.7
    )
    
    return {
        "answer": response.choices[0].message.content, 
        "source": "Sovereign Executive (Internal RAG)",
        "authorized_wallet": request.wallet_address
    }

@app.post("/update-identity")
async def update_identity(request: IdentityUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    path = BASE_DIR / "knowledge_base" / "identity.txt"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{request.content}")
    refresh_vector_db() 
    return {"status": "Identity Evolved", "message": "New traits appended."}

@app.post("/add-knowledge")
async def add_knowledge(request: KnowledgeUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    filename = f"{request.filename}.txt"
    path = BASE_DIR / "knowledge_base" / "documents" / filename
    
    mode = "a" if path.exists() else "w"
    content = f"\n{request.content}" if path.exists() else request.content

    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    refresh_vector_db()
    return {"status": "Knowledge Added", "file": filename}

@app.get("/list-knowledge")
async def list_knowledge():
    docs_path = BASE_DIR / "knowledge_base" / "documents"
    try:
        files = [f.name for f in docs_path.glob("*.txt")]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/agents")
async def list_marketplace_agents():
    """Fetches the live directory of active agents from the blockchain."""
    try:
        agents = get_all_registered_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)