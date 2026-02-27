import os
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# --- 1. PATH RESOLUTION ---
# Going up from /marketplace/agents/humanizer_agent/ to root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

# --- 2. CONFIG ---
RPC_URL = "http://127.0.0.1:8545"
# Ensure address is a Checksum Address
MARKET_ADDR = Web3.to_checksum_address(os.getenv("MARKETPLACE_ADDRESS"))
DEV_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" 

# --- 3. INITIALIZE WEB3 & CONTRACT ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# Check connection
if not w3.is_connected():
    print(" Error: Could not connect to Hardhat node. Is it running?")
    exit()

# Navigate to ABI
ABI_PATH = ROOT_DIR / "marketplace" / "artifacts" / "contracts" / "AISAAS_Market.sol" / "AISAAS_Market.json"
with open(ABI_PATH) as f:
    market_abi = json.load(f)["abi"]

market_contract = w3.eth.contract(address=MARKET_ADDR, abi=market_abi)
account = w3.eth.account.from_key(DEV_PRIVATE_KEY)

def register():
    print(f" Attempting to register agent at Market: {MARKET_ADDR}")
    
    # Path to the card.json
    card_path = Path(__file__).parent / "card.json"
    card_uri = str(card_path.resolve())
    
    # Building the transaction WITHOUT the 'to' field inside the dict
    # because the market_contract instance already has the address.
    try:
        tx_params = {
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 31337 # Standard Hardhat Chain ID
        }

        # Use the contract function directly
        func = market_contract.functions.registerAgent(
            "GhostWriter Pro",
            "writing",
            card_uri,
            w3.to_wei(0.001, 'ether')
        )

        # Build it
        raw_tx = func.build_transaction(tx_params)

        # Sign it
        signed_tx = w3.eth.account.sign_transaction(raw_tx, DEV_PRIVATE_KEY)
        
        # Send it
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f" Transaction sent! Hash: {tx_hash.hex()}")
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(" Registration Successful! Agent is now live in the Marketplace.")
        else:
            print(" Registration failed on-chain. Check Hardhat logs.")

    except Exception as e:
        print(f" Python Error: {str(e)}")

if __name__ == "__main__":
    register()