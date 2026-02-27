from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SkyBound Navigator - Travel Agent")

class TravelRequest(BaseModel):
    origin: str
    destination: str
    date: str

@app.post("/process")
async def book_flight(request: TravelRequest):
    print(f" RECEIVED BOOKING REQUEST: {request.origin} -> {request.destination} on {request.date}")
    
    # Simulate a "Real-World" action
    return {
        "status": "SUCCESS",
        "confirmation_code": "AISAAS-V2-999",
        "message": f"Flight from {request.origin} to {request.destination} has been tentatively 'booked' in the mock system."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)