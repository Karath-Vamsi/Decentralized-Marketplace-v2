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
    try:
        total_agents = market_contract.functions.totalAgents().call()
    except Exception as e:
        print(f" Error fetching totalAgents: {e}")
        return []
    
    all_agents = []
    for i in range(1, total_agents + 1):
        details = market_contract.functions.registry(i).call()
        if details[5]:  # isActive check
            try:
                with open(details[3], 'r') as f:
                    card_data = json.load(f)
                all_agents.append({
                    "id": i,
                    "name": details[1],
                    "card": card_data,
                    "fee_wei": details[4]
                })
            except:
                continue
    return all_agents

def select_best_agent(user_query: str):
    agents = get_all_registered_agents()
    if not agents: 
        return None

    q = user_query.lower()

    #  THE GUARD (Bypasses LLM Refusals)
    if any(word in q for word in ["hash", "sha-256", "crypto", "encrypt"]):
        print(" Keyword Match: Routing to Vault-Guard Crypto")
        # Find the crypto agent dynamically just in case IDs shift
        for a in agents: 
            if "Vault" in a['name']: return a

    if any(word in q for word in ["audit", "security", "vulnerability", "scan"]):
        print(" Keyword Match: Routing to Sentinel-Audit")
        for a in agents: 
            if "Sentinel" in a['name']: return a

    if any(word in q for word in ["flight", "book", "travel", "ticket"]):
        print(" Keyword Match: Routing to SkyBound Navigator")
        for a in agents: 
            if "SkyBound" in a['name']: return a

    # --- Fallback to LLM for complex stuff ---
    staff_directory = ""
    for i, a in enumerate(agents):
        staff_directory += f"AGENT_ID [{i}]: {a['name']} - Capability: {a['card']['description']}\n"

    system_prompt = (
        "You are a ROUTING_GATEWAY. Output ONLY a single digit based on the directory below.\n"
        f"### STAFF DIRECTORY:\n{staff_directory}\n"
        "RULES:\n"
        "1. If request matches an agent capability, return ONLY its AGENT_ID number.\n"
        "2. If request is about personal data, identity, or general chat, return 'NONE'."
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
        
        print(f" Fallback to Internal. LLM Output: {raw_choice}")
    except Exception as e:
        print(f"Routing Error: {e}")
    
    return None

def format_specialist_input(user_query: str, agent_card: dict):
    name = agent_card.get('name', '')
    
    #  SPECIAL CASE 1: Sentinel-Audit
    if "Sentinel" in name:
        return {"code_to_audit": user_query, "strict_mode": True}

    #  SPECIAL CASE 2: Vault-Guard
    if "Vault-Guard" in name:
        strings = re.findall(r"'(.*?)'|\"(.*?)\"", user_query)
        data_to_hash = strings[0][0] or strings[0][1] if strings else "AISAAS_DATA"
        return {"data_string": data_to_hash, "operation": "hash"}
    
    #  GENERAL CASE: LLM Extraction (Travel Agent, etc.)
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