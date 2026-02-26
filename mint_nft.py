import os
from dotenv import load_dotenv
from web3 import Web3
import json
from pathlib import Path

load_dotenv()

# Connect
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = w3.to_checksum_address(os.getenv("USER_WALLET_ADDRESS"))
private_key = os.getenv("USER_PRIVATE_KEY")

# Get ABI
ABI_PATH = Path("marketplace/artifacts/contracts/ExecutiveNFT.sol/ExecutiveNFT.json")
with open(ABI_PATH) as f:
    abi = json.load(f)["abi"]

contract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=abi)

print(f"Minting NFT for {account}...")

# Build Transaction
nonce = w3.eth.get_transaction_count(account)
tx = contract.functions.mintTwin().build_transaction({
    'from': account,
    'nonce': nonce,
    'gas': 2000000,
    'gasPrice': w3.to_wei('50', 'gwei')
})

# Sign and Send
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f" NFT Minted! Tx Hash: {w3.to_hex(tx_hash)}")