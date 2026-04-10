import requests
import json
import time
from pathlib import Path

# --- PATH RESOLUTION ---
CURRENT_FILE_DIR = Path(__file__).resolve().parent 
SOVEREIGN_DIR = CURRENT_FILE_DIR.parent 
LOGS_DIR = SOVEREIGN_DIR / "knowledge_base" / "logs"

def log_interaction(agent_name, payload, response):
    """
    Saves the interaction to the /logs folder for Preference Distillation.
    This allows ingest.py to later 'distill' the Digital Twin's behavior.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    log_file = LOGS_DIR / f"interaction_{agent_name}_{timestamp}.txt"
    
    log_content = (
        f"AGENT: {agent_name}\n"
        f"TIMESTAMP: {timestamp}\n"
        f"REQUEST_PAYLOAD: {json.dumps(payload)}\n"
        f"RESPONSE_RECEIVED: {json.dumps(response)}\n"
        f"--- END OF LOG ---"
    )
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(log_content)

def call_specialist_agent(agent_card, payload):
    """
    Takes an Agent Card and a payload, and sends a request 
    to the specialist's endpoint.
    """
    endpoint = agent_card.get("endpoint")
    name = agent_card.get("name")
    
    print(f" [*] Initiating A2A Handshake with {name}...")
    print(f" [*] Endpoint: {endpoint}")

    try:
        # Reduced timeout to 120s (unless you specifically need an hour for big tasks)
        # requests.post timeout is in seconds.
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300 
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f" [+] {name} successfully processed the request.")
            
            # CRITICAL: Log the successful interaction for Preference Distillation
            log_interaction(name, payload, result)
            
            return result
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f" [!] {name} returned an error: {error_msg}")
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        print(f" [!] Failed to communicate with agent: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Mock for testing
    mock_card = {
        "name": "GhostWriter Pro",
        "endpoint": "http://127.0.0.1:8001/process"
    }
    
    mock_payload = {
        "text": "The AI is good for writing code.",
        "tone": "witty"
    }
    
    res = call_specialist_agent(mock_card, mock_payload)
    if res:
        print("\n--- OUTPUT ---")
        print(res)