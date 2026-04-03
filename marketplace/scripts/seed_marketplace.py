import os
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Setup
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

RPC_URL = "http://127.0.0.1:8545"
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))
DEV_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)
account = w3.eth.account.from_key(DEV_KEY)

GHOST_FOLDER = Path(__file__).parent / "ghost_metadata"
GHOST_FOLDER.mkdir(exist_ok=True)

GHOST_AGENTS = [
    {"name": "Legal-Eagle GPT", "cat": "Legal", "fee": 0.008, "desc": "Specialized in smart contract law and international trade compliance."},
    {"name": "Ad-Genius Pro", "cat": "Marketing", "fee": 0.002, "desc": "Generates high-conversion ad copy and social media strategies."},
    {"name": "Cyber-Sleuth", "cat": "Security", "fee": 0.012, "desc": "Off-chain deep-packet inspection and advanced forensic analysis."},
    {"name": "Code-Wizard JS", "cat": "Writing", "fee": 0.004, "desc": "Expert at refactoring React and Next.js codebases for performance."},
    {"name": "Med-Scribe AI", "cat": "Healthcare", "fee": 0.015, "desc": "HIPAA-compliant medical transcription and diagnostic assistance."},
    {"name": "Data-Cleaner Elite", "cat": "Utility", "fee": 0.001, "desc": "Automated CSV/JSON normalization and outlier detection."},
    {"name": "Translator Prime", "cat": "Language", "fee": 0.003, "desc": "Near-instant translation across 150+ languages with cultural nuance."},
    {"name": "Logo-Gen AI", "cat": "Creative", "fee": 0.005, "desc": "Vector-based brand identity generation from text prompts."},
    {"name": "Fin-Analyst Ultra", "cat": "Finance", "fee": 0.009, "desc": "Predictive analytics for DeFi yields and cross-chain arbitrage."},
    {"name": "Thesis-Assistant", "cat": "Academic", "fee": 0.006, "desc": "Citation management and logical flow auditing for research papers."}
]

def seed():
    print(f"Seeding Marketplace with {len(GHOST_AGENTS)} Shadow Agents...")
    
    for i, agent in enumerate(GHOST_AGENTS):
        card_content = {
            "name": agent['name'],
            "category": agent['cat'],
            "description": agent['desc']
        }
        card_file = GHOST_FOLDER / f"ghost_{i}.json"
        with open(card_file, "w") as f:
            json.dump(card_content, f)

        tx_params = {
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': w3.eth.gas_price
        }

        func = market_contract.functions.registerAgent(
            agent['name'],
            agent['cat'],
            str(card_file.resolve()),
            w3.to_wei(agent['fee'], 'ether')
        )

        signed_tx = w3.eth.account.sign_transaction(func.build_transaction(tx_params), DEV_KEY)
        w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f" Registered: {agent['name']} on-chain.")

if __name__ == "__main__":
    seed()