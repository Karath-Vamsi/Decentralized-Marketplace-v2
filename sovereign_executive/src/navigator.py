import os
import json
import re
import pickle
from typing import TypedDict, Optional, Dict, Any, List
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langgraph.graph import StateGraph, END

# --- PATH RESOLUTION ---
SRC_DIR = Path(__file__).resolve().parent
SOVEREIGN_DIR = SRC_DIR.parent
ROOT_DIR = SOVEREIGN_DIR.parent
KB_DIR = SOVEREIGN_DIR / "knowledge_base"
DB_DIR = SOVEREIGN_DIR / "chroma_db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"

load_dotenv(ROOT_DIR / ".env")

# --- CONFIG & WEB3 ---
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]
market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)

# =====================================================================
# RAG MEMORY ENGINE (LEVELS 3, 4, 5) - FULLY PRESERVED
# =====================================================================
print("[*] Initializing RAG Memory Models...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)
bm25_data = None
if BM25_INDEX_PATH.exists():
    with open(BM25_INDEX_PATH, "rb") as f:
        bm25_data = pickle.load(f)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def reload_memory():
    global vectorstore, bm25_data
    print("[*] Reloading Navigator Memory Engine...")
    vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)
    if BM25_INDEX_PATH.exists():
        with open(BM25_INDEX_PATH, "rb") as f:
            bm25_data = pickle.load(f)

# =====================================================================
# AGENT DIRECTORY - PRESERVED GUARDRAILS
# =====================================================================
def get_all_registered_agents():
    try:
        total_agents = market_contract.functions.totalAgents().call()
    except Exception:
        return []
    
    VALID_SPECIALISTS = ["Sentinel-Audit", "SkyBound Navigator", "Vault-Guard Crypto"]
    all_agents = []
    for i in range(1, total_agents + 1):
        details = market_contract.functions.registry(i).call()
        if details[5]:
            if not any(name in details[1] for name in VALID_SPECIALISTS): continue
            try:
                total_stars = details[6]
                jobs_done = details[7]
                avg_rating = (total_stars / jobs_done) if jobs_done > 0 else 0
                with open(details[3], 'r') as f:
                    card_data = json.load(f)
                all_agents.append({
                    "id": i, "name": details[1], "category": details[2], 
                    "rating": avg_rating, "jobs_done": jobs_done, 
                    "card": card_data, "fee_wei": details[4]
                })
            except Exception:
                continue
    return all_agents

# =====================================================================
# LANGGRAPH: THE MISSION STATE & NODES
# =====================================================================

class MissionState(TypedDict):
    query: str
    wallet_address: str
    route_decision: str       # 'specialist' or 'internal_rag'
    selected_agent: Optional[Dict[str, Any]]
    worker_payload: Optional[Dict[str, Any]]
    final_answer: str
    metadata: Optional[List[Dict[str, Any]]] # Preserved Metadata
    context: Optional[str]                   # Preserved RAG Context
    job_id: Optional[int]
    current_thought: str

# Node 1: Router (Preserves Priority Guardrails + Cognitive Gate)
def node_router(state: MissionState) -> MissionState:
    q = state["query"].lower()
    agents = get_all_registered_agents()
    
    if not agents:
        return {"route_decision": "internal_rag", "current_thought": "[SYSTEM] No specialists online. Defaulting to internal memory."}

    # Priority Guardrails logic exactly as before
    def get_best_in_group(keywords, identifier):
        if any(word in q for word in keywords):
            matched = [a for a in agents if identifier in a['name']]
            if matched:
                return sorted(matched, key=lambda x: (x['rating'], x['jobs_done']), reverse=True)[0]
        return None

    res = get_best_in_group(["audit", "security", "vulnerability", "scan", "smart contract"], "Sentinel") or \
          get_best_in_group(["flight", "book", "travel", "ticket"], "SkyBound") or \
          get_best_in_group(["balance", "wallet", "funds", "price", "market", "gas"], "Vault")

    if res:
        return {"route_decision": "specialist", "selected_agent": res, "current_thought": f"[PLANNING] Matched priority guardrail. Routing to {res['name']}."}

    # Cognitive Gate logic exactly as before
    staff_directory = "".join([f"AGENT_ID [{i}]: {a['name']} - {a['card']['description']}\n" for i, a in enumerate(agents)])
    system_prompt = (
        "You are the SOVEREIGN ROUTER. Your task is to decide if a query requires an EXTERNAL specialist.\n"
        "DIRECTORIES OF SPECIALISTS:\n"
        f"{staff_directory}\n"
        "STRICT CLASSIFICATION RULES:\n"
        "1. If the query is about YOUR identity, AISAAS, greetings, or general knowledge, return 'NONE'.\n"
        "2. If the query asks for a specific action (Audit, Booking, Crypto Data) that matches a specialist, return their AGENT_ID.\n"
        "3. If you are unsure or the query is ambiguous, return 'NONE'."
    )
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": state["query"]}],
            temperature=0.0
        )
        raw_choice = response.choices[0].message.content.strip().upper()
        if "NONE" in raw_choice:
            return {"route_decision": "internal_rag", "current_thought": "[PLANNING] Intent: Internal AISAAS Knowledge."}
        
        match = re.search(r'\d+', raw_choice)
        if match and int(match.group()) < len(agents):
            agent = agents[int(match.group())]
            return {"route_decision": "specialist", "selected_agent": agent, "current_thought": f"[PLANNING] Routing to {agent['name']} via cognitive intent."}
    except: pass
    return {"route_decision": "internal_rag", "current_thought": "[PLANNING] Defaulting to safe internal RAG."}

# Node 2: Extractor (Restores Sentinel/Vault Logic + SkyBound Defaults)
def node_extract_payload(state: MissionState) -> MissionState:
    agent = state["selected_agent"]
    query = state["query"]
    name = agent["name"]
    thought = f"[HANDSHAKE] Formatting specialist payload for {name}..."
    
    # Restored Sentinel Logic
    if "Sentinel" in name:
        return {"worker_payload": {"code_to_audit": query, "strict_mode": True}, "current_thought": thought}
    
    # Restored Vault-Guard Logic
    if "Vault-Guard" in name:
        q_low = query.lower()
        operation = "balance_check" if any(w in q_low for w in ["balance", "wallet", "funds"]) else "market_data"
        addr_match = re.search(r'0x[a-fA-F0-9]{40}', query)
        return {
            "worker_payload": {
                "account_to_analyze": addr_match.group() if addr_match else state["wallet_address"] or "0x0000000000000000000000000000000000000000",
                "operation": operation
            },
            "current_thought": thought
        }

    # Restored Dynamic Extraction with SkyBound Defaults
    schema = agent["card"].get("input_schema", {})
    keys = ", ".join(schema.keys())
    extraction_prompt = f"Extract these values: {keys}\nText: {query}\nReturn ONLY JSON. If missing, use 'unknown'."
    try:
        res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": extraction_prompt}], temperature=0)
        raw = res.choices[0].message.content
        clean = re.sub(r'<\|.*?\|>', '', raw).replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        # RESTORED: Travel Agent Defaults
        if "origin" in schema:
            if data.get("origin") == "unknown": data["origin"] = "Hyderabad"
            if data.get("destination") == "unknown": data["destination"] = "Barcelona"
            if data.get("date") == "unknown": data["date"] = "2026-03-10"
            
        return {"worker_payload": data, "current_thought": thought}
    except Exception as e:
        return {"worker_payload": {}, "current_thought": f"[WARNING] Extraction failed: {str(e)}"}

# Node 3: Internal RAG (Restores Level 3-5 logic + metadata capture)
def node_internal_rag(state: MissionState) -> MissionState:
    query = state["query"]
    if not bm25_data: return {"final_answer": "Memory offline.", "current_thought": "[ERROR] Memory failure."}

    # Level 3: Hybrid Search
    sem_res = vectorstore.similarity_search(query, k=15)
    bm25_res = bm25_data["bm25"].get_top_n(query.lower().split(), bm25_data["chunks"], n=15)
    unique = list({d.page_content: d for d in sem_res + bm25_res}.values())

    if not unique: return {"final_answer": "No memory found.", "current_thought": "[RETRIEVAL] Empty result."}

    # Level 4: Reranking
    scores = reranker.predict([[query, d.page_content] for d in unique])
    reranked = sorted(zip(unique, scores), key=lambda x: x[1], reverse=True)
    
    # Level 5: Fallback Threshold
    if reranked[0][1] < 0.5:
        return {"final_answer": "Relevant context not found.", "current_thought": "[RETRIEVAL] Low confidence score."}

    final_docs = [d for d, s in reranked[:3]]
    context_text = "\n\n".join([d.page_content for d in final_docs])
    metadata_list = [d.metadata for d in final_docs]

    # Synthesis
    res = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": f"You are Sovereign Executive. Use only:\n{context_text}"},
                  {"role": "user", "content": query}],
        temperature=0.2
    )
    return {
        "final_answer": res.choices[0].message.content, 
        "context": context_text, 
        "metadata": metadata_list,
        "current_thought": "[SYNTHESIS] Response generated from internal memory."
    }

# =====================================================================
# GRAPH COMPILATION
# =====================================================================
def build_sovereign_graph():
    workflow = StateGraph(MissionState)
    workflow.add_node("Router", node_router)
    workflow.add_node("Extractor", node_extract_payload)
    workflow.add_node("InternalRAG", node_internal_rag)
    workflow.set_entry_point("Router")
    workflow.add_conditional_edges("Router", lambda state: state["route_decision"], {"specialist": "Extractor", "internal_rag": "InternalRAG"})
    workflow.add_edge("Extractor", END)
    workflow.add_edge("InternalRAG", END)
    return workflow.compile()

sovereign_graph = build_sovereign_graph()