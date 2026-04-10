import os
import json
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

app = FastAPI(title="Sentry Auditor (Real-Time Security Agent)")

class SecurityRequest(BaseModel):
    code_to_audit: str
    strict_mode: bool
    job_id: int

@app.post("/process")
async def process_security(request: SecurityRequest):
    print(f"\n--- Initiating Security Audit for Job #{request.job_id} ---")
    
    try:
        job_data = market_contract.functions.jobs(request.job_id).call()
        if job_data[5] != 0:
            return {"status": "PAYMENT_REQUIRED", "message": "Audit fee not secured in escrow."}
        
        print("Payment Verified. Analyzing code snippet for vulnerabilities...")

        system_prompt = (
            "You are the Sentry Auditor, an elite AI specialized in finding security vulnerabilities."
            "\nAnalyze the provided code and generate a formal audit report."
            "\n\nSTRICT OUTPUT FORMAT:"
            "\n1. VULNERABILITY SCAN: Identify 2-3 specific risks (e.g., Reentrancy, SQL Injection, Logic errors)."
            "\n2. SEVERITY ASSESSMENT: Rate the risk level (Low/Medium/High/Critical)."
            "\n3. REMEDIATION: Provide a short code fix for the most critical issue found."
            "\n4. AUDIT CERTIFICATION: Conclude with a 'CERTIFICATE OF AUDIT' block. "
            "State: 'Audit Hash: SEC-X99. Status: PENDING FINAL PAYMENT RELEASE.'"
        )
        
        user_prompt = f"Audit Request for Code Snippet:\n\n{request.code_to_audit}"

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )

        audit_report = response.choices[0].message.content
        print("Audit complete. Sending report to Executive.")

        return {
            "status": "SUCCESS",
            "result": audit_report,
            "job_id": request.job_id
        }

    except Exception as e:
        print(f"SECURITY ERROR: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)