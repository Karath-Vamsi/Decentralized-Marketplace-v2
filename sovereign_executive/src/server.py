from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI
import os

app = FastAPI(title="AISAAS Sovereign Executive")

# 1. Configuration & Setup
DB_DIR = "../chroma_db"
LLM_URL = "http://127.0.0.1:8081/v1" # Match your brain.py port!

# Initialize local embeddings and load the database
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# Initialize local LLM client
client = OpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

class QueryRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "Online", "agent": "Sovereign Executive"}

@app.post("/ask")
async def ask_twin(request: QueryRequest):
    try:
        # STEP A: Semantic Search (Retrieve)
        # We look for the top 3 most relevant facts from your knowledge base
        docs = vector_db.similarity_search(request.prompt, k=3)
        context = "\n---\n".join([doc.page_content for doc in docs])

        # STEP B: Construct the Sovereign Prompt (Augment)
        # We wrap your query in your identity and retrieved knowledge
        system_prompt = f"""
        You are the 'Sovereign Executive'—a personalized Digital Twin.
        Answer the user's request using the following context from their personal Knowledge Base.
        If the answer isn't in the context, use your internal knowledge but maintain the persona.

        CONTEXT FROM KNOWLEDGE BASE:
        {context}
        """

        # STEP C: Chat with Llamafile (Generate)
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": [doc.metadata for doc in docs]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)