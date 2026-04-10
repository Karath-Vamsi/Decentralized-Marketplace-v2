import os
import json
import re
import pickle
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- PATH RESOLUTION ---
SRC_DIR = Path(__file__).resolve().parent
SOVEREIGN_DIR = SRC_DIR.parent
ROOT_DIR = SOVEREIGN_DIR.parent
KB_DIR = SOVEREIGN_DIR / "knowledge_base"
DB_DIR = SOVEREIGN_DIR / "chroma_db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"

load_dotenv(ROOT_DIR / ".env")

# --- CONFIG & WEB3 ---
RPC_URL = "http://127.0.0.1:8545"
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))

# # --- OPENROUTER CONFIG ---
# OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
# MODEL_ID = "minimax/minimax-m2.5:free"

# --- Groq Config ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Initializing OpenAI client to point to Groq
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)

# =====================================================================
# RAG MEMORY ENGINE (LEVELS 3, 4, 5)
# =====================================================================

print("[*] Initializing RAG Memory Models...")
# Load Semantic (Chroma)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)

# Load Keyword (BM25)
bm25_data = None
if BM25_INDEX_PATH.exists():
    with open(BM25_INDEX_PATH, "rb") as f:
        bm25_data = pickle.load(f)

# Load Reranker (Cross-Encoder)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def retrieve_internal_memory(query: str, top_k: int = 3):
    """
    Executes Level 3 (Hybrid), Level 4 (Rerank), and Level 5 (Fallback)
    """
    if not bm25_data:
        return {"status": "error", "message": "Memory indices not found. Run ingest.py."}

    # --- LEVEL 3: HYBRID SEARCH ---
    semantic_results = vectorstore.similarity_search(query, k=15)
    
    tokenized_query = query.lower().split()
    bm25_results = bm25_data["bm25"].get_top_n(tokenized_query, bm25_data["chunks"], n=15)

    unique_candidates = {doc.page_content: doc for doc in semantic_results + bm25_results}
    candidates_list = list(unique_candidates.values())

    if not candidates_list:
        return {"status": "fallback", "context": None, "message": "No memory candidates found."}

    # --- LEVEL 4: RERANKING ---
    pairs = [[query, doc.page_content] for doc in candidates_list]
    scores = reranker.predict(pairs)

    reranked = sorted(zip(candidates_list, scores), key=lambda x: x[1], reverse=True)

    # --- LEVEL 5: PRODUCTION FALLBACK ---
    BEST_SCORE_THRESHOLD = 0.5 
    best_score = reranked[0][1]
    
    if best_score < BEST_SCORE_THRESHOLD:
        return {
            "status": "fallback", 
            "context": None, 
            "message": "Memory retrieval failed: relevant context not found."
        }

    final_docs = [doc for doc, score in reranked[:top_k]]
    return {
        "status": "success",
        "context": "\n\n".join([d.page_content for d in final_docs]),
        "metadata": [d.metadata for d in final_docs]
    }


# =====================================================================
# AGENT ROUTING ENGINE (PRESERVED GUARDRAILS)
# =====================================================================

def get_all_registered_agents():
    """Fetches all active agents from the blockchain."""
    try:
        total_agents = market_contract.functions.totalAgents().call()
    except Exception as e:
        print(f" Error fetching totalAgents: {e}")
        return []
    
    VALID_SPECIALISTS = ["Sentinel-Audit", "SkyBound Navigator", "Vault-Guard Crypto"]
    all_agents = []
    for i in range(1, total_agents + 1):
        details = market_contract.functions.registry(i).call()
        if details[5]:
            if not any(name in details[1] for name in VALID_SPECIALISTS):
                continue
            try:
                total_stars = details[6]
                jobs_done = details[7]
                avg_rating = (total_stars / jobs_done) if jobs_done > 0 else 0
                
                with open(details[3], 'r') as f:
                    card_data = json.load(f)
                    
                all_agents.append({
                    "id": i,
                    "name": details[1],
                    "category": details[2],
                    "rating": avg_rating,
                    "jobs_done": jobs_done,
                    "card": card_data,
                    "fee_wei": details[4]
                })
            except Exception as e:
                print(f" Error loading card for agent {i}: {e}")
                continue
    return all_agents

def select_best_agent(user_query: str):
    """Routes user query with Priority Routing using Llama 3.3 70B via OpenRouter."""
    agents = get_all_registered_agents()
    if not agents: 
        return None

    q = user_query.lower()

    def get_best_in_group(keyword_list, agent_identifier):
        if any(word in q for word in keyword_list):
            matched = [a for a in agents if agent_identifier in a['name']]
            if matched:
                sorted_group = sorted(matched, key=lambda x: (x['rating'], x['jobs_done']), reverse=True)
                print(f" 🎯 Phase 5 Routing: Selected {sorted_group[0]['name']}")
                return sorted_group[0]
        return None

    # PRIORITY GUARDRAILS
    if res := get_best_in_group(["audit", "security", "vulnerability", "scan", "smart contract"], "Sentinel"): return res
    if res := get_best_in_group(["flight", "book", "travel", "ticket"], "SkyBound"): return res
    if res := get_best_in_group(["balance", "wallet", "funds", "price", "market", "gas"], "Vault"): return res

    # Fallback to LLM
    staff_directory = ""
    for i, a in enumerate(agents):
        staff_directory += f"AGENT_ID [{i}]: {a['name']} - Specialist in: {a['card']['description']}\n"

    system_prompt = (
        "You are the SOVEREIGN ROUTER. Your task is to decide if a query requires an EXTERNAL specialist.\n"
        "DIRECTORIES OF SPECIALISTS:\n"
        f"{staff_directory}\n"
        "STRICT CLASSIFICATION RULES:\n"
        "1. If the query is about YOUR identity, AISAAS, greetings, or general knowledge, return 'NONE'.\n"
        "2. If the query asks for a specific action (Audit, Booking, Crypto Data) that matches a specialist, return their AGENT_ID.\n"
        "3. If you are unsure or the query is ambiguous, return 'NONE'.\n"
        "4. DO NOT invent agents. Output ONLY the digit or 'NONE'."
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_query}],
            temperature=0.0 
        )
        raw_choice = response.choices[0].message.content.strip().lower()

        if "NONE" in raw_choice:
            print(" [!] Intent Classification: Internal Knowledge / General Query.")
            return None
        
        match = re.search(r'\d+', raw_choice)
        if match:
            idx = int(match.group())
            if idx < len(agents): 
                return agents[idx]
    except Exception as e:
        print(f"Routing Error: {e}")
    
    return None

def format_specialist_input(user_query: str, agent_card: dict, user_wallet: str = None):
    """Extraction logic using Llama 3.3 70B via OpenRouter."""
    name = agent_card.get('name', '')
    
    if "Sentinel" in name:
        return {"code_to_audit": user_query, "strict_mode": True}

    if "Vault-Guard" in name:
        q = user_query.lower()
        operation = "balance_check" if any(word in q for word in ["balance", "wallet", "funds"]) else "market_data"
        addr_match = re.search(r'0x[a-fA-F0-9]{40}', user_query)
        return {
            "account_to_analyze": addr_match.group() if addr_match else user_wallet or "0x0000000000000000000000000000000000000000",
            "operation": operation
        }
    
    schema = agent_card.get("input_schema", {})
    keys = ", ".join(schema.keys())

    extraction_prompt = (
        f"Extract these values: {keys}\nText: {user_query}\n"
        "Return ONLY a JSON object. If missing, use 'unknown'."
    )

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0
        )
        raw = res.choices[0].message.content
        clean_json = re.sub(r'<\|.*?\|>', '', raw).strip()
        clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        if "origin" in schema:
            if data.get("origin") == "unknown": data["origin"] = "Hyderabad"
            if data.get("destination") == "unknown": data["destination"] = "Barcelona"
            if data.get("date") == "unknown": data["date"] = "2026-03-10"
            
        return data
    except Exception as e:
        print(f" Extraction failed: {e}")
        return {}

def reload_memory():
    """Reloads the RAG memory into RAM without restarting the server."""
    global vectorstore, bm25_data
    print("[*] Reloading Navigator Memory Engine...")
    vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)
    if BM25_INDEX_PATH.exists():
        with open(BM25_INDEX_PATH, "rb") as f:
            bm25_data = pickle.load(f)
    print("[+] Navigator Memory Reload Complete.")