import requests
import json

def call_specialist_agent(agent_card, payload):
    """
    Takes an Agent Card and a payload, and sends a request 
    to the specialist's endpoint.
    """
    endpoint = agent_card.get("endpoint")
    name = agent_card.get("name")
    
    print(f" Initiating A2A Handshake with {name}...")
    print(f" Endpoint: {endpoint}")

    try:
        # We use the 'input_schema' logic from the card to ensure 
        # we are sending exactly what the agent wants.
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f" {name} successfully processed the request.")
            return result
        else:
            print(f" {name} returned an error: {response.text}")
            return None
            
    except Exception as e:
        print(f" Failed to communicate with agent: {e}")
        return None

if __name__ == "__main__":
    # Mock data for testing the client standalone
    mock_card = {
        "name": "GhostWriter Pro",
        "endpoint": "http://127.0.0.1:8001/process"
    }
    
    mock_payload = {
        "text": "The AI is good for writing code but sometimes it sounds like a robot.",
        "tone": "witty",
        "intensity": 8
    }
    
    res = call_specialist_agent(mock_card, mock_payload)
    if res:
        print("\n--- HUMANIZED OUTPUT ---")
        print(res.get("rewritten_text"))