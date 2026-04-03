import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from web3 import Web3

# --- Setup Paths & Env ---
AGENT_DIR = Path(__file__).resolve().parent
MARKETPLACE_DIR = AGENT_DIR.parent.parent
ROOT_DIR = MARKETPLACE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# --- Blockchain Setup ---
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MARKET_ADDR = os.getenv("MARKETPLACE_ADDRESS")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ABI_PATH = MARKETPLACE_DIR / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=w3.to_checksum_address(MARKET_ADDR), abi=market_abi)

app = FastAPI(title="GhostWriter Humanizer (Phase 4 Enabled)")

class HumanizerRequest(BaseModel):
    text: str
    tone: str
    intensity: int
    job_id: int

@app.post("/process")
async def process_humanizer(request: HumanizerRequest):
    print(f" Checking Payment for Job #{request.job_id}...")
    
    try:
        job_data = market_contract.functions.jobs(request.job_id).call()
        if job_data[5] != 0:
            return {"status": "PAYMENT_REQUIRED", "message": "No locked escrow found."}
        
        print(f" Verified. Humanizing text with {request.tone} tone...")
        
        rewritten = f"[HUMANIZED - {request.tone.upper()}]: {request.text}"
        
        return {
            "status": "SUCCESS",
            "rewritten_text": rewritten,
            "job_id": request.job_id
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)