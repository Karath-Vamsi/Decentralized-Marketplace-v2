import os
import json
import time 
import random 
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from web3 import Web3
from openai import OpenAI

# Updated imports
from navigator import sovereign_graph, reload_memory, get_all_registered_agents
from a2a_client import call_specialist_agent
from ingest import build_memory

# --- Unified Path Configuration ---
SRC_DIR = Path(__file__).resolve().parent
SOVEREIGN_DIR = SRC_DIR.parent
ROOT_DIR = SOVEREIGN_DIR.parent

load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Core Directories
KB_DIR = SOVEREIGN_DIR / "knowledge_base"
DOCS_DIR = KB_DIR / "documents"
LOGS_DIR = KB_DIR / "logs"
DB_DIR = SOVEREIGN_DIR / "chroma_db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"
IDENTITY_FILE = KB_DIR / "identity.txt"

# --- Environment Variables ---
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
MARKET_ADDR = os.getenv("MARKETPLACE_ADDRESS")
USER_KEY = os.getenv("USER_PRIVATE_KEY")
USER_WALLET = os.getenv("USER_WALLET_ADDRESS")
RPC_URL = os.getenv("RPC_URL") 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile" 

# --- Blockchain & AI Setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))

NFT_ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "ExecutiveNFT.sol" / "ExecutiveNFT.json"
with open(NFT_ABI_PATH) as f:
    nft_abi = json.load(f)["abi"]
nft_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=nft_abi)

MARKET_ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(MARKET_ABI_PATH) as f:
    market_abi = json.load(f)["abi"]
market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

# --- NEW: SYNTHESIS PROMPT ---
SYNTHESIS_PROMPT = """You are the SOVEREIGN EXECUTIVE. 
Your task is to wrap the raw specialist telemetry into a high-fidelity briefing without losing any technical detail.

STRICT FORMATTING COMMANDS:
1. NO EMOJIS: Do not use any emojis in the header, status, or body of the response.
2. NO HTML: Never use tags like <br/> or <div>. Use only Markdown.
3. TRIPLE NEWLINES: You MUST use three newlines (\\n\\n\\n) between the Title, the Annex, and the Insight.
4. THEMATIC BREAKS: Use '---' on its own line to create horizontal separation between sections.
5. FONT WEIGHT: Use # and ## for headers to trigger larger font sizes in the UI.
6. ABSOLUTE DATA INTEGRITY: You are FORBIDDEN from summarizing, shortening, or altering the specialist's response. You must include the ENTIRE text provided by the worker in the Technical Annex.

REPORT TEMPLATE:

# EXECUTIVE BRIEFING: [Insert Title]

**SYSTEM STATUS**: [SECURE / PENDING]


---


## TECHNICAL ANNEX: MARKETPLACE DATA
[INJECT THE FULL, UNEDITED SPECIALIST RESPONSE HERE. Ensure all tables, PNRs, addresses, and analysis from the worker node are preserved verbatim.]


---


## EXECUTIVE INSIGHT
> **STRATEGIC ANALYSIS**:
> [Provide your additional strategic observation here. Do not repeat the worker's data. Instead, explain the implications or next steps for the Principal. Use bold text for the most critical instruction.]
"""

app = FastAPI(title="AISAAS Sovereign Executive")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Models ---
class QueryRequest(BaseModel):
    prompt: str
    wallet_address: str

class ReleaseRequest(BaseModel):
    job_id: int
    rating: int 
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

def get_initial_state(request: QueryRequest):
    return {
        "query": request.prompt, "wallet_address": request.wallet_address,
        "route_decision": "", "selected_agent": None, "worker_payload": None,
        "final_answer": "", "metadata": None, "context": None, "job_id": None, "current_thought": ""
    }

# =====================================================================
# ENDPOINTS
# =====================================================================

@app.post("/ask-stream")
async def ask_twin_stream(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")

    def event_stream():
        yield f"data: {json.dumps({'type': 'thought', 'content': '[SYSTEM] Initializing Sovereign Executive...'})}\n\n"
        
        initial_state = get_initial_state(request)
        final_state = initial_state.copy()
        
        # 1. Run the LangGraph
        for output in sovereign_graph.stream(initial_state):
            for node_name, state_update in output.items():
                final_state.update(state_update)
                if "current_thought" in state_update:
                    yield f"data: {json.dumps({'type': 'thought', 'content': state_update['current_thought']})}\n\n"
                    time.sleep(0.3)
        
        # 2. Blockchain & A2A Execution
        if final_state.get("route_decision") == "specialist":
            agent = final_state["selected_agent"]
            payload = final_state["worker_payload"]
            
            yield f"data: {json.dumps({'type': 'thought', 'content': f'[BLOCKCHAIN] Locking {agent['fee_wei']} Wei for {agent['name']}...'})}\n\n"
            
            try:
                nonce = w3.eth.get_transaction_count(USER_WALLET)
                tx = market_contract.functions.createJob(agent['id']).build_transaction({
                    'from': USER_WALLET, 'value': int(agent['fee_wei']),
                    'gas': 300000, 'gasPrice': w3.to_wei('20', 'gwei'), 'nonce': nonce,
                })
                signed_tx = w3.eth.account.sign_transaction(tx, private_key=USER_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                job_id = market_contract.events.JobCreated().process_receipt(receipt)[0]['args']['jobId']
                yield f"data: {json.dumps({'type': 'thought', 'content': f'[BLOCKCHAIN] Job #{job_id} Locked. Initiating Handshake...'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': f'Blockchain Error: {str(e)}'})}\n\n"
                return
            
            yield f"data: {json.dumps({'type': 'thought', 'content': '[NETWORK] Waiting for specialist response...'})}\n\n"
            payload['job_id'] = job_id
            worker_result = call_specialist_agent(agent['card'], payload)
            
            if worker_result:
                raw_val = worker_result.get("result") or worker_result.get("message") or str(worker_result)
                
                # --- NEW: EXECUTIVE SYNTHESIS STEP ---
                yield f"data: {json.dumps({'type': 'thought', 'content': '[SYNTHESIS] Formatting Immutable Technical Annex for Principal...'})}\n\n"
                
                try:
                    synthesis_res = client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=[
                            {"role": "system", "content": SYNTHESIS_PROMPT},
                            {"role": "user", "content": f"User Query: {request.prompt}\n\nRaw Specialist Data:\n{raw_val}"}
                        ],
                        temperature=0.1 # Very low temp to ensure strict adherence to formatting without hallucinating data
                    )
                    final_answer = synthesis_res.choices[0].message.content
                except Exception as e:
                    print(f"Synthesis failed, falling back to raw output: {e}")
                    final_answer = str(raw_val).split("<|")[0].strip()

                yield f"data: {json.dumps({'type': 'result', 'answer': final_answer, 'source': f'VERIFIED: {agent['name']}', 'job_id': job_id})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Worker failed to respond.'})}\n\n"

        # 3. Internal RAG Output
        else:
            yield f"data: {json.dumps({'type': 'result', 'answer': final_state['final_answer'], 'source': 'Sovereign Executive (Internal RAG)'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/ask")
async def ask_twin(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")

    print(f"\n Executive Brain: Evaluating task: '{request.prompt[:50]}...'")
    
    initial_state = get_initial_state(request)
    final_state = sovereign_graph.invoke(initial_state)

    if final_state["route_decision"] == "specialist":
        agent = final_state["selected_agent"]
        payload = final_state["worker_payload"]
        print(f" Specialist Found: {agent['name']}. Initiating Phase 4 Payment...")
        
        try:
            print(f"Locking {agent['fee_wei']} Wei for {agent['name']}...")
            nonce = w3.eth.get_transaction_count(USER_WALLET)
            tx = market_contract.functions.createJob(agent['id']).build_transaction({
                'from': USER_WALLET, 'value': int(agent['fee_wei']),
                'gas': 300000, 'gasPrice': w3.to_wei('20', 'gwei'), 'nonce': nonce,
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=USER_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            job_id = market_contract.events.JobCreated().process_receipt(receipt)[0]['args']['jobId']
            print(f"Job #{job_id} Locked on-chain. Notifying Worker...")
        except Exception as e:
            print(f"Blockchain Payment Failed: {e}")
            raise HTTPException(status_code=500, detail="Escrow creation failed.")

        time.sleep(random.uniform(2.0, 4.0)) 
        payload['job_id'] = job_id  
        worker_result = call_specialist_agent(agent['card'], payload)
        
        if worker_result:
            raw_val = worker_result.get("result") or worker_result.get("message") or worker_result.get("rewritten_text") or str(worker_result)
            
            # --- NEW: EXECUTIVE SYNTHESIS STEP (Sync Version) ---
            print(" [SYNTHESIS] Formatting Immutable Technical Annex...")
            try:
                synthesis_res = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYNTHESIS_PROMPT},
                        {"role": "user", "content": f"User Query: {request.prompt}\n\nRaw Specialist Data:\n{raw_val}"}
                    ],
                    temperature=0.1
                )
                final_answer = synthesis_res.choices[0].message.content
            except Exception as e:
                print(f"Synthesis failed: {e}")
                final_answer = str(raw_val).split("<|")[0].strip()

            return {
                "answer": final_answer,
                "source": f"VERIFIED: {agent['name']}",
                "job_id": job_id,
                "status": "PAYMENT_PENDING_APPROVAL",
                "data": worker_result,
                "authorized_wallet": request.wallet_address
            }

    print(" No specialist used. Consulting internal RAG memory...")
    return {
        "answer": final_state["final_answer"], 
        "source": "Sovereign Executive (Internal RAG)",
        "status": "success" if final_state["final_answer"] else "fallback",
        "authorized_wallet": request.wallet_address
    }

@app.post("/release-payment")
async def release_payment(request: ReleaseRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        print(f" Submitting {request.rating}-star ⭐ rating for Job #{request.job_id}...")
        nonce = w3.eth.get_transaction_count(USER_WALLET)
        tx = market_contract.functions.releasePaymentWithRating(
            request.job_id, request.rating
        ).build_transaction({
            'from': USER_WALLET, 'gas': 300000, 'gasPrice': w3.to_wei('20', 'gwei'), 'nonce': nonce,
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

def auto_prepare_memory():
    db_exists = os.path.exists(DB_DIR)
    bm25_exists = BM25_INDEX_PATH.exists()
    if not db_exists or not bm25_exists:
        print("[!] Memory indices missing. Auto-generating Sovereign Memory...")
        build_memory()
        reload_memory()
    else:
        print("[+] Sovereign Memory found and loaded.")

if __name__ == "__main__":
    import uvicorn
    auto_prepare_memory()
    uvicorn.run(app, host="0.0.0.0", port=8000)