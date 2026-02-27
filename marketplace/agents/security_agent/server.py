from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="Sentinel-Audit Agent")

class AuditRequest(BaseModel):
    code_to_audit: str
    strict_mode: bool = True

@app.post("/process")
async def perform_audit(request: AuditRequest):
    print(f" AUDIT START: Scanning {len(request.code_to_audit)} characters of code...")
    
    # Simulate a deep scan
    issues = ["Re-entrancy risk", "Integer Overflow", "Unprotected Admin Function"]
    found = random.sample(issues, k=random.randint(0, 2))
    
    return {
        "status": "COMPLETED",
        "vulnerabilities_found": found,
        "risk_score": "LOW" if not found else "CRITICAL",
        "message": "Audit completed. Please review findings before mainnet deployment."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)