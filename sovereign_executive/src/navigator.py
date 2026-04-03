import os
import json
import re
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
from openai import OpenAI

# Path resolution
SRC_DIR = Path(__file__).resolve().parent
SOVEREIGN_DIR = SRC_DIR.parent
ROOT_DIR = SOVEREIGN_DIR.parent

load_dotenv(ROOT_DIR / ".env")

# Config
RPC_URL = "http://127.0.0.1:8545"
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))
LLM_URL = "http://127.0.0.1:8090/v1"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

# Load Marketplace ABI
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)

def get_all_registered_agents():
    """
    Fetches all active agents from the blockchain, including Phase 5 Reputation data.
    """
    try:
        total_agents = market_contract.functions.totalAgents().call()
    except Exception as e:
        print(f" Error fetching totalAgents: {e}")
        return []
    
    all_agents = []
    for i in range(1, total_agents + 1):
        details = market_contract.functions.registry(i).call()
        if details[5]:
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
    """
    Routes user query to the highest-rated specialist in the matching category.
    Now optimized with 'Priority Routing' to prevent keyword collisions.
    """
    agents = get_all_registered_agents()
    if not agents: 
        return None

    q = user_query.lower()

    # --- REPUTATION-BASED SELECTION LOGIC ---
    
    def get_best_in_group(keyword_list, agent_identifier):
        if any(word in q for word in keyword_list):
            matched = [a for a in agents if agent_identifier in a['name']]
            if matched:
                sorted_group = sorted(matched, key=lambda x: (x['rating'], x['jobs_done']), reverse=True)
                print(f" 🎯 Phase 5 Routing: Selected {sorted_group[0]['name']} (Rating: {sorted_group[0]['rating']})")
                return sorted_group[0]
        return None

    # PRIORITY 1: Security Group (Specific Technical Intent)
    sec_keywords = ["audit", "security", "vulnerability", "scan", "smart contract"]
    best_sec = get_best_in_group(sec_keywords, "Sentinel")
    if best_sec: 
        return best_sec

    # PRIORITY 2: Travel Group (Specific Lifestyle Intent)
    travel_keywords = ["flight", "book", "travel", "ticket"]
    best_travel = get_best_in_group(travel_keywords, "SkyBound")
    if best_travel: return best_travel

    # PRIORITY 3: Crypto Group (General Financial Intent)
    crypto_keywords = ["check balance", "wallet funds", "eth price", "gas price", "crypto market"]
    
    legacy_crypto_keywords = ["price", "market", "wallet", "hash"]
    
    best_crypto = get_best_in_group(crypto_keywords + legacy_crypto_keywords, "Vault")
    if best_crypto: 
        return best_crypto

    # --- Fallback to LLM for complex stuff (Includes Reputation context) ---
    staff_directory = ""
    for i, a in enumerate(agents):
        staff_directory += f"AGENT_ID [{i}]: {a['name']} - Rating: {a['rating']} Stars - Capability: {a['card']['description']}\n"

    system_prompt = (
        "You are a ROUTING_GATEWAY for a decentralized marketplace.\n"
        "Output ONLY a single digit (AGENT_ID) for the best-rated agent that fits the request.\n"
        f"### STAFF DIRECTORY:\n{staff_directory}\n"
        "RULES:\n"
        "1. Prioritize agents with higher ratings if multiple match.\n"
        "2. If no specialist fits, return 'NONE'."
    )

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_query}],
            temperature=0.0 
        )
        raw_choice = response.choices[0].message.content.strip().lower()
        match = re.search(r'\d+', raw_choice)
        if match:
            idx = int(match.group())
            if idx < len(agents): return agents[idx]
    except Exception as e:
        print(f"Routing Error: {e}")
    
    return None

def format_specialist_input(user_query: str, agent_card: dict, user_wallet: str = None):
    name = agent_card.get('name', '')
    
    # SPECIAL CASE 1: Sentinel-Audit
    if "Sentinel" in name:
        return {"code_to_audit": user_query, "strict_mode": True}

    # SPECIAL CASE 2: Vault-Guard
    if "Vault-Guard" in name:
        q = user_query.lower()
        operation = "market_data"
        if any(word in q for word in ["balance", "wallet", "funds"]):
            operation = "balance_check"
        elif any(word in q for word in ["gas", "fee"]):
            operation = "gas_estimate"
        
        addr_match = re.search(r'0x[a-fA-F0-9]{40}', user_query)
        account = addr_match.group() if addr_match else user_wallet
        
        return {
            "account_to_analyze": account or "0x0000000000000000000000000000000000000000",
            "operation": operation
        }
    
    # GENERAL CASE: LLM Extraction (Travel Agent, etc.)
    schema = agent_card.get("input_schema", {})
    keys = ", ".join(schema.keys())

    extraction_prompt = (
        f"Extract these values: {keys}\n"
        f"Text: {user_query}\n"
        "Return ONLY a JSON object. If missing, use 'unknown'."
    )

    try:
        res = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0
        )
        raw = res.choices[0].message.content
        clean_json = re.sub(r'<\|.*?\|>', '', raw).strip()
        clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # Flight Agent Fallbacks
        if "origin" in schema:
            if data.get("origin") == "unknown": data["origin"] = "Hyderabad"
            if data.get("destination") == "unknown": data["destination"] = "Barcelona"
            if data.get("date") == "unknown": data["date"] = "2026-03-10"
            
        return data
    except Exception as e:
        print(f" Extraction failed: {e}")
        return {}