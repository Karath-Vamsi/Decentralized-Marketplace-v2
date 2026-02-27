import os
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Path resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

RPC_URL = "http://127.0.0.1:8545"
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))
DEV_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" 

w3 = Web3(Web3.HTTPProvider(RPC_URL))
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)
account = w3.eth.account.from_key(DEV_PRIVATE_KEY)

def register():
    print(" Registering Sentinel-Audit on Marketplace...")
    card_path = Path(__file__).parent / "card.json"
    card_uri = str(card_path.resolve())
    
    tx_params = {
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'chainId': 31337 
    }

    func = market_contract.functions.registerAgent(
        "Sentinel-Audit",
        "security",
        card_uri,
        w3.to_wei(0.008, 'ether')
    )

    signed_tx = w3.eth.account.sign_transaction(func.build_transaction(tx_params), DEV_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f" Security Agent Registered! Hash: {tx_hash.hex()}")

if __name__ == "__main__":
    register()