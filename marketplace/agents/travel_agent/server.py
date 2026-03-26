import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from web3 import Web3
from tavily import TavilyClient
from openai import OpenAI

# --- Setup Paths & Env ---
AGENT_DIR = Path(__file__).resolve().parent
MARKETPLACE_DIR = AGENT_DIR.parent.parent
ROOT_DIR = MARKETPLACE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# --- Config ---
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MARKET_ADDR = os.getenv("MARKETPLACE_ADDRESS")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
LLM_URL = "http://127.0.0.1:8090/v1" # Using your existing local LLM

# --- Clients ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
tavily = TavilyClient(api_key=TAVILY_KEY)
llm_client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

# --- Load ABI ---
ABI_PATH = MARKETPLACE_DIR / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]
market_contract = w3.eth.contract(address=w3.to_checksum_address(MARKET_ADDR), abi=market_abi)

app = FastAPI(title="SkyBound Navigator (Real-Time Agent)")

class TravelRequest(BaseModel):
    origin: str
    destination: str
    date: str
    job_id: int


@app.post("/process")
async def process_travel(request: TravelRequest):
    print(f"\n--- 🎫 Executing Decision Protocol for Job #{request.job_id} ---")
    
    try:
        # 1. Blockchain Verification
        job_data = market_contract.functions.jobs(request.job_id).call()
        if job_data[4] != 0:
            return {"status": "PAYMENT_REQUIRED", "message": "Escrow not found."}
        
        # 2. Web Search (Live Data)
        print(f"🌐 Gathering live intelligence for {request.destination}...")
        search_query = f"cheapest flights from {request.origin} to {request.destination} on {request.date}"
        search_response = tavily.search(query=search_query, max_results=5)
        search_results = search_response.get('results', [])

        if not search_results:
            return {"status": "SUCCESS", "result": "No flight options found.", "job_id": request.job_id}

        # 3. Agentic Decision Making
        print("🧠 Analyzing options and generating Mock Booking...")

        raw_context = "\n".join([
            f"DATA {i}: {r['content'][:500]}... [Source: {r['url']}]" 
            for i, r in enumerate(search_results)
        ])

        # Updated System Prompt with explicit Mock Booking instructions
        system_prompt = (
            "You are the SkyBound Navigator, a specialized travel agent for the AISAAS Marketplace. "
            "Your goal is to analyze flight data and perform a MOCK BOOKING for the user."
            "\n\nSTRICT OUTPUT FORMAT:"
            "\n1. FOUND OPTIONS: List 2-3 best flights with prices and airlines."
            "\n2. STRATEGIC ANALYSIS: Explain why one specific flight is the 'Most Efficient'."
            "\n3. BOOKING CONFIRMATION: End with a clear success block. "
            "Include a fake PNR (e.g., AS-7892), the flight number, and state: 'Booking is currently on HOLD. "
            "Funds are secured in AISAAS Escrow and will be released upon user approval.'"
        )

        response = llm_client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Finalize decision for {request.origin} to {request.destination} on {request.date}:\n{raw_context}"}
            ],
            temperature=0.3,
            max_tokens=500 
        )

        agent_output = response.choices[0].message.content
        print("✅ Decision & Mock Booking finalized.")

        return {
            "status": "SUCCESS",
            "result": agent_output,
            "job_id": request.job_id
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)