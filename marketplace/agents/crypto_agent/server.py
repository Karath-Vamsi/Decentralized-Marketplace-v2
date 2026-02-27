from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import secrets

app = FastAPI(title="Vault-Guard Crypto Agent")

class CryptoRequest(BaseModel):
    data_string: str
    operation: str  # "hash" or "encrypt"

@app.post("/process")
async def process_crypto(request: CryptoRequest):
    print(f" CRYPTO OP: {request.operation} requested for data.")
    
    if request.operation.lower() == "hash":
        result = hashlib.sha256(request.data_string.encode()).hexdigest()
        msg = "SHA-256 Hash generated successfully."
    else:
        # Simulate an encryption blob
        result = f"ENC-{secrets.token_hex(16)}"
        msg = "Data moved to secure vault. Encryption token generated."
    
    return {
        "status": "SUCCESS",
        "result": result,
        "message": msg
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)