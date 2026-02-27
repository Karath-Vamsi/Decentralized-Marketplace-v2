import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GhostWriter Pro - Humanizer Agent")

# Allow requests from your Twin's server and the Dashboard
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Point to your local Llamafile
LLM_URL = "http://127.0.0.1:8081/v1" 
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

class HumanizeRequest(BaseModel):
    text: str
    tone: str = "professional"
    intensity: int = 5

@app.post("/process")
async def process_text(request: HumanizeRequest):
    print(f" Received request to humanize text (Tone: {request.tone})")
    
    system_prompt = (
        f"You are a 'GhostWriter Pro', a specialist agent in the AISAAS marketplace. "
        f"Your sole task is to rewrite the provided text to sound more human, high-agency, and engaging. "
        f"Target Tone: {request.tone}. Intensity Level: {request.intensity}/10. "
        "Do not include any conversational filler. Just return the rewritten text."
    )

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.text}
            ],
            temperature=0.8 # Higher temperature for more creative/human output
        )
        return {"rewritten_text": response.choices[0].message.content, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)