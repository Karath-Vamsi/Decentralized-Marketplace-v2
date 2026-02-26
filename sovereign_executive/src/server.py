import os
import json
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from web3 import Web3

# AI & RAG Imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI

# --- 1. PATH RESOLUTION (Aligned with AISAAS_Project Structure) ---
# server.py is in: ROOT/sovereign_executive/src/server.py
SRC_DIR = Path(__file__).resolve().parent      # ROOT/sovereign_executive/src
BASE_DIR = SRC_DIR.parent                      # ROOT/sovereign_executive
ROOT_DIR = BASE_DIR.parent                     # ROOT/AISAAS_Project

# Load .env from ROOT/AISAAS_Project/.env
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Database is in ROOT/sovereign_executive/chroma_db
DB_DIR = str(BASE_DIR / "chroma_db")

# ABI is in ROOT/marketplace/artifacts/contracts/ExecutiveNFT.sol/ExecutiveNFT.json
# Note: Hardhat creates 'artifacts' in the folder where hardhat.config.js lives
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "ExecutiveNFT.sol" / "ExecutiveNFT.json"

# --- 2. CONFIGURATION ---
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL") 
LLM_URL = "http://127.0.0.1:8081/v1" 

# --- 3. INITIALIZATION ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))

try:
    with open(ABI_PATH) as f:
        abi = json.load(f)["abi"]
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
except FileNotFoundError:
    print(f" ERROR: ABI not found at {ABI_PATH}. Did you run 'npx hardhat compile' inside /marketplace?")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

app = FastAPI(title="AISAAS Sovereign Executive")

class QueryRequest(BaseModel):
    prompt: str
    wallet_address: str

# --- 4. AUTH LOGIC ---
def is_authorized(user_wallet_address: str):
    try:
        addr = w3.to_checksum_address(user_wallet_address)
        return contract.functions.hasActiveTwin(addr).call()
    except Exception as e:
        print(f"Gatekeeper Auth Error: {e}")
        return False

# --- 5. API ROUTES ---
@app.get("/")
async def root():
    return {"status": "Online", "agent": "Sovereign Executive", "contract": CONTRACT_ADDRESS}

@app.post("/ask")
async def ask_twin(request: QueryRequest):
    if not is_authorized(request.wallet_address):
        raise HTTPException(status_code=403, detail="NFT Ownership Required.")

    try:
        docs = vector_db.similarity_search(request.prompt, k=3)
        context = "\n---\n".join([doc.page_content for doc in docs])

        system_prompt = f"""
        You are the 'Sovereign Executive'—a personalized Digital Twin.
        Answer the user's request using the following context:
        {context}
        """

        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7
        )

        return {
            "answer": response.choices[0].message.content,
            "authorized_wallet": request.wallet_address,
            "sources": [doc.metadata for doc in docs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)