import requests

# The wallet address you just minted the NFT for
MY_WALLET = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
# A random wallet that DOES NOT own an NFT
FAKE_WALLET = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

def ask_ai(wallet, question):
    url = "http://127.0.0.1:8000/ask"
    payload = {
        "prompt": question,
        "wallet_address": wallet
    }
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

print("--- TESTING UNAUTHORIZED ACCESS ---")
ask_ai(FAKE_WALLET, "What is the secret code?")

print("--- TESTING AUTHORIZED ACCESS ---")
ask_ai(MY_WALLET, "What is the AISAAS project brief?")