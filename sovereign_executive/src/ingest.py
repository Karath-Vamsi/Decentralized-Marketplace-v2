import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- PATH CORRECTION ---
# 1. This file is in /src/ingest.py
CURRENT_FILE_DIR = Path(__file__).resolve().parent 
# 2. Go up one level to /sovereign_executive/
SOVEREIGN_DIR = CURRENT_FILE_DIR.parent 

# 3. Define correct paths relative to /sovereign_executive/
KB_DIR = str(SOVEREIGN_DIR / "knowledge_base")
DB_DIR = str(SOVEREIGN_DIR / "chroma_db")

def build_memory():
    print(" Initializing Digital Twin Memory Update...")
    print(f" Looking for files in: {KB_DIR}")

    # Load Knowledge Base
    # Note: We are pointing to KB_DIR which contains identity.txt and the /documents folder
    loader = DirectoryLoader(KB_DIR, glob="./**/*.txt", loader_cls=TextLoader)
    try:
        documents = loader.load()
    except Exception as e:
        print(f" Error loading files: {e}")
        return

    if not documents:
        print(f" Warning: No .txt files found in {KB_DIR}")
        return

    print(f" Found {len(documents)} documents. Processing...")

    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    # Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create and Persist
    # Updating the DB located in /sovereign_executive/chroma_db
    vectorstore = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory=DB_DIR
    )
    
    print(f" Success! Memory Rebuilt with {len(texts)} chunks in {DB_DIR}")

if __name__ == "__main__":
    build_memory()