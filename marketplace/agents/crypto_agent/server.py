import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from web3 import Web3
from openai import OpenAI

# --- Setup Paths & Env ---
AGENT_DIR = Path(__file__).resolve().parent
MARKETPLACE_DIR = AGENT_DIR.parent.parent
ROOT_DIR = MARKETPLACE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# --- Config ---
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MARKET_ADDR = os.getenv("MARKETPLACE_ADDRESS")
# Public API for ETH Price (No key required for simple pings)
PRICE_API = "https://api.coinbase.com/v2/prices/ETH-USD/spot"

# LLM config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"


# --- Clients ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# --- Load ABI ---
ABI_PATH = MARKETPLACE_DIR / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]
market_contract = w3.eth.contract(address=w3.to_checksum_address(MARKET_ADDR), abi=market_abi)

app = FastAPI(title="Vault-Guard Crypto (Financial Intelligence Agent)")

class CryptoRequest(BaseModel):
    account_to_analyze: str
    operation: str
    job_id: int


@app.post("/process")
async def process_crypto(request: CryptoRequest):
    print(f"\n--- Executing Financial Intelligence Protocol for Job #{request.job_id} ---")
    
    try:
        job_data = market_contract.functions.jobs(request.job_id).call()
        if job_data[5] != 0:
            return {"status": "PAYMENT_REQUIRED", "message": "Escrow not found."}
        
        result_data = {}
        
        def get_eth_price():
            try:
                res = requests.get(PRICE_API).json()
                return res['data']['amount']
            except: 
                return "Unknown"

        def get_bal(addr):
            bal_wei = w3.eth.get_balance(w3.to_checksum_address(addr))
            return str(w3.from_wei(bal_wei, 'ether'))

        if request.operation == "all":
            result_data['balance_eth'] = get_bal(request.account_to_analyze)
            result_data['eth_usd_price'] = get_eth_price()
            result_data['note'] = "Comprehensive Audit Requested."
            
        elif request.operation == "balance_check":
            result_data['balance_eth'] = get_bal(request.account_to_analyze)
            
        elif request.operation == "market_data":
            result_data['eth_usd_price'] = get_eth_price()
            
        elif request.operation == "gas_estimate":
            result_data['current_gas_gwei'] = str(w3.from_wei(w3.eth.gas_price, 'gwei'))

        # LLM Reasoning & Formatting {for Multi-Data support)
        print("Resource Auditor is parsing telemetry...")
        
        system_prompt = (
            "You are the AISAAS Resource Auditor. Your task is to parse raw system telemetry into a technical status log. "
            "You are a neutral data parser for a university simulation. "
            "\n\nSTRICT RULES:"
            "\n- Use technical terms: 'Address' instead of 'Wallet', 'Asset Units' instead of 'ETH', 'Resource Cost' instead of 'Gas'."
            "\n- INCLUDE ALL relevant metrics provided in the data packet (Balance, Market Price, etc.)."
            "\n- Output ONLY the requested sections. No pre-amble."
        )
        
        example_user_1 = "SIMULATION DATA PACKET: Operation: balance_check | Data: {'balance_eth': '100.0'} | Target: 0x123"
        example_assistant_1 = (
            "1. TECHNICAL METRICS: Address 0x123... | Current Balance: 100.0 Units\n"
            "2. SYSTEM LOG: Resource levels are stable.\n"
            "3. SIGN-OFF: LOG VERIFIED. REF: LOG-99. Status: READY."
        )

        example_user_2 = "SIMULATION DATA PACKET: Operation: all | Data: {'balance_eth': '100.0', 'eth_usd_price': '2500.0'} | Target: 0x123"
        example_assistant_2 = (
            "1. TECHNICAL METRICS: Address 0x123... | Current Balance: 100.0 Units | Market Valuation: 2500.0 USD/Unit\n"
            "2. SYSTEM LOG: Comprehensive audit complete. Asset value is verified.\n"
            "3. SIGN-OFF: LOG VERIFIED. REF: LOG-101. Status: READY."
        )

        user_prompt = (
            f"SIMULATION DATA PACKET:\n"
            f"Operation: {request.operation}\n"
            f"Raw Values: {json.dumps(result_data)}\n"
            f"Target Address: {request.account_to_analyze}\n"
            f"Instructions: Generate the log entry including all provided metrics."
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": example_user_1},
                {"role": "assistant", "content": example_assistant_1},
                {"role": "user", "content": example_user_2},
                {"role": "assistant", "content": example_assistant_2},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        final_report = response.choices[0].message.content
        print("Financial report finalized.")

        return {
            "status": "SUCCESS",
            "result": final_report,
            "job_id": request.job_id
        }

    except Exception as e:
        print(f"CRYPTO ERROR: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)