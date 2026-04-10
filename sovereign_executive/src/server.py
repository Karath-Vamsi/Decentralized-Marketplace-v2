import os
import json
import time 
import random 
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from openai import OpenAI

# Updated imports: pulling retrieval and reload logic from navigator
from navigator import select_best_agent, format_specialist_input, get_all_registered_agents, retrieve_internal_memory, reload_memory
from a2a_client import call_specialist_agent
from ingest import build_memory

# --- Unified Path Configuration ---
SRC_DIR = Path(__file__).resolve().parent          # .../sovereign_executive/src
SOVEREIGN_DIR = SRC_DIR.parent                     # .../sovereign_executive
ROOT_DIR = SOVEREIGN_DIR.parent                    # .../Decentralized-Marketplace-v2

# Load .env from the root of the entire project
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Core Directories (Clean & Single Source of Truth)
KB_DIR = SOVEREIGN_DIR / "knowledge_base"
DOCS_DIR = KB_DIR / "documents"
LOGS_DIR = KB_DIR / "logs"
DB_DIR = SOVEREIGN_DIR / "chroma_db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"
IDENTITY_FILE = KB_DIR / "identity.txt"

# --- Environment Variables ---
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")       # Executive NFT
MARKET_ADDR = os.getenv("MARKETPLACE_ADDRESS")         # AISAAS Marketplace
USER_KEY = os.getenv("USER_PRIVATE_KEY")               # Wallet PK
USER_WALLET = os.getenv("USER_WALLET_ADDRESS")         # Wallet Address
RPC_URL = os.getenv("RPC_URL") 

# OpenRouter Config
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OR_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# --- Groq Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile" 

# --- Blockchain Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Loading Executive NFT Contract (For Auth)
NFT_ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "ExecutiveNFT.sol" / "ExecutiveNFT.json"
with open(NFT_ABI_PATH) as f:
    nft_abi = json.load(f)["abi"]
nft_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=nft_abi)

# Loading Marketplace Contract
MARKET_ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(MARKET_ABI_PATH) as f:
    market_abi = json.load(f)["abi"]
market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)

# --- AI Setup ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# --- FastAPI Initialization ---
app = FastAPI(title="AISAAS Sovereign Executive")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Models ---
class QueryRequest(BaseModel):
    prompt: str
    wallet_address: str

class ReleaseRequest(BaseModel):
    job_id: int
    rating: int # 1 to 5
    wallet_address: str

class IdentityUpdate(BaseModel):
    content: str
    wallet_address: str

class KnowledgeUpdate(BaseModel):
    filename: str
    content: str
    wallet_address: str

# --- Helper Functions ---
def is_authorized(user_wallet_address: str):
    try:
        addr = w3.to_checksum_address(user_wallet_address)
        return nft_contract.functions.hasActiveTwin(addr).call()
    except: 
        return False

def refresh_vector_db():
    print("[*] Rebuilding Memory Engine on disk...")
    build_memory()
    print("[*] Synchronizing RAM with new memory...")
    reload_memory()

# --- Endpoints ---
@app.post("/ask")
async def ask_twin(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")

    print(f"\n Executive Brain: Evaluating task: '{request.prompt[:50]}...'")
    specialist = select_best_agent(request.prompt)

    # --- ROUTE A: SPECIALIST DELEGATION ---
    if specialist:
        print(f" Specialist Found: {specialist['name']}. Initiating Phase 4 Payment...")
        
        try:
            print(f"Locking {specialist['fee_wei']} Wei for {specialist['name']}...")
            
            nonce = w3.eth.get_transaction_count(USER_WALLET)
            tx = market_contract.functions.createJob(specialist['id']).build_transaction({
                'from': USER_WALLET,
                'value': int(specialist['fee_wei']),
                'gas': 300000,
                'gasPrice': w3.to_wei('20', 'gwei'),
                'nonce': nonce,
            })
            
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=USER_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logs = market_contract.events.JobCreated().process_receipt(receipt)
            job_id = logs[0]['args']['jobId']
            print(f"Job #{job_id} Locked on-chain. Notifying Worker...")
        
        except Exception as e:
            print(f"Blockchain Payment Failed: {e}")
            raise HTTPException(status_code=500, detail="Escrow creation failed.")

        sleep_time = random.uniform(2.0, 4.0) 
        print(f" Simulating A2A Handshake Protocol... ({sleep_time:.1f}s additional delay)")
        time.sleep(sleep_time)
        
        payload = format_specialist_input(request.prompt, specialist['card'], request.wallet_address)
        payload['job_id'] = job_id  
        
        worker_result = call_specialist_agent(specialist['card'], payload)
        
        if worker_result:
            raw_val = (
                worker_result.get("result") or 
                worker_result.get("message") or 
                worker_result.get("rewritten_text") or
                str(worker_result)
            )
            final_answer = str(raw_val).split("<|")[0].strip()

            return {
                "answer": final_answer,
                "source": f"VERIFIED: {specialist['name']}",
                "job_id": job_id,
                "status": "PAYMENT_PENDING_APPROVAL",
                "data": worker_result,
                "authorized_wallet": request.wallet_address
            }
    
    # --- ROUTE B: INTERNAL KNOWLEDGE (LEVEL 5 RAG) ---
    print(" No specialist used. Consulting internal RAG memory...")
    memory_response = retrieve_internal_memory(request.prompt)
    
    if memory_response["status"] == "success":
        context = memory_response["context"]
        system_prompt = (
            "You are the 'Sovereign Executive'. Answer the user's query STRICTLY using the context below. "
            "Do not hallucinate or use outside information. If the context does not fully answer the query, "
            "explain what you know based on the context and state what is missing.\n\n"
            f"### CONTEXT:\n{context}"
        )
    else:
        system_prompt = (
            "You are the 'Sovereign Executive'. The requested information is NOT in your internal knowledge base. "
            "Politely inform the user that you do not have the verified data to answer their query, and suggest "
            "they add the relevant knowledge via the '/add-knowledge' endpoint."
        )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt}
        ],
        temperature=0.2 
    )
    
    return {
        "answer": response.choices[0].message.content, 
        "source": "Sovereign Executive (Internal RAG)",
        "status": memory_response["status"],
        "authorized_wallet": request.wallet_address
    }

@app.post("/release-payment")
async def release_payment(request: ReleaseRequest):
    """
    Finalizes the job on-chain by releasing the escrowed funds and 
    submitting a 1-5 star rating to update agent reputation.
    """
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        print(f" Submitting {request.rating}-star ⭐ rating for Job #{request.job_id}...")
        
        nonce = w3.eth.get_transaction_count(USER_WALLET)
        tx = market_contract.functions.releasePaymentWithRating(
            request.job_id, 
            request.rating
        ).build_transaction({
            'from': USER_WALLET,
            'gas': 300000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=USER_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)

        return {"status": "SUCCESS", "message": "Funds released and reputation updated!"}
    except Exception as e:
        print(f"Release Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-identity")
async def update_identity(request: IdentityUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    path = SOVEREIGN_DIR / "knowledge_base" / "identity.txt"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{request.content}")
    
    refresh_vector_db() 
    return {"status": "Identity Evolved", "message": "New traits appended."}

@app.post("/add-knowledge")
async def add_knowledge(request: KnowledgeUpdate):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    filename = f"{request.filename}.txt"
    path = SOVEREIGN_DIR / "knowledge_base" / "documents" / filename
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    mode = "a" if path.exists() else "w"
    content = f"\n{request.content}" if path.exists() else request.content

    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
        
    refresh_vector_db()
    return {"status": "Knowledge Added", "file": filename}

@app.get("/list-knowledge")
async def list_knowledge():
    docs_path = SOVEREIGN_DIR / "knowledge_base" / "documents"
    try:
        files = [f.name for f in docs_path.glob("*.txt")]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/agents")
async def list_marketplace_agents():
    try:
        agents = get_all_registered_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Startup Automation ---
def auto_prepare_memory():
    """Checks if memory exists on disk; if not, builds it."""
    db_exists = os.path.exists(DB_DIR)
    bm25_exists = BM25_INDEX_PATH.exists()

    if not db_exists or not bm25_exists:
        print("[!] Memory indices missing. Auto-generating Sovereign Memory...")
        build_memory()
        # We also need to make sure Navigator loads this new data into RAM
        reload_memory()
    else:
        print("[+] Sovereign Memory found and loaded.")

if __name__ == "__main__":
    import uvicorn
    # 1. Run the check BEFORE starting the web server
    auto_prepare_memory()
    
    # 2. Start the engine
    uvicorn.run(app, host="0.0.0.0", port=8000)
