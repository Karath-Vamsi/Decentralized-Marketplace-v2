import os
import pickle
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

# --- PATH CONFIGURATION ---
CURRENT_FILE_DIR = Path(__file__).resolve().parent 
SOVEREIGN_DIR = CURRENT_FILE_DIR.parent 

# Core Directories
KB_DIR = SOVEREIGN_DIR / "knowledge_base"
DOCS_DIR = KB_DIR / "documents"
LOGS_DIR = KB_DIR / "logs"
DB_DIR = SOVEREIGN_DIR / "chroma_db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"
IDENTITY_FILE = KB_DIR / "identity.txt"

def load_text_file(filepath: Path, doc_type: str, source_name: str) -> list[Document]:
    """Helper to load a single file and attach base metadata."""
    if not filepath.exists():
        print(f" [!] Warning: File not found -> {filepath}")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
        
    return [Document(page_content=text, metadata={"source": source_name, "type": doc_type})]

def load_directory(dir_path: Path, doc_type: str) -> list[Document]:
    """Helper to load directories and attach base metadata."""
    if not dir_path.exists():
        print(f" [!] Warning: Directory not found -> {dir_path}")
        return []

    loader = DirectoryLoader(str(dir_path), glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()
    
    # Inject doc_type metadata into loaded documents
    for doc in docs:
        doc.metadata["type"] = doc_type
    return docs

def build_memory():
    print("\n--- Initializing Sovereign Executive Memory Rebuild ---")
    
    # Ensure necessary output directories exist
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    all_raw_documents = []

    # 1. LOAD IDENTITY FIRST
    print("[*] 1. Loading Core Identity...")
    identity_docs = load_text_file(IDENTITY_FILE, "core_identity", "identity.txt")
    all_raw_documents.extend(identity_docs)

    # 2. LOAD KNOWLEDGE BASE (Documents)
    print("[*] 2. Loading Knowledge Base Documents...")
    kb_docs = load_directory(DOCS_DIR, "knowledge_document")
    all_raw_documents.extend(kb_docs)

    # 3. LOAD LOGS (Preference Distillation)
    print("[*] 3. Loading Interaction Logs...")
    log_docs = load_directory(LOGS_DIR, "preference_log")
    all_raw_documents.extend(log_docs)

    if not all_raw_documents:
        print("[!] No documents loaded. Aborting pipeline.")
        return

    # 4. LEVEL 2: SMART CHUNKING
    print("[*] 4. Executing Smart Chunking (Level 2 RAG)...")
    # Using the "Sweet spot" from the article: 400 chunk size, 100 overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, 
        chunk_overlap=100,
        add_start_index=True, # Critical for metadata
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(all_raw_documents)
    print(f" [+] Generated {len(chunks)} contextual chunks with metadata.")

    # 5. LEVEL 3 PREP: HYBRID SEARCH (Vector + BM25)
    print("[*] 5. Building Vector Database & BM25 Keyword Index (Level 3 RAG)...")
    
    # --- Semantic Index (Chroma/Vectors) ---
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=str(DB_DIR)
    )
    print(f" [+] Vector Embeddings saved to {DB_DIR}")

    # --- Keyword Index (BM25) ---
    # Extract text from chunks, tokenize by lowercasing and splitting
    tokenized_corpus = [chunk.page_content.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # Save the BM25 model and the raw chunk data to disk alongside Chroma
    # We save the chunks so the retrieval script can map BM25 scores back to the actual text/metadata
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
        
    print(f" [+] BM25 Keyword Index saved to {BM25_INDEX_PATH}")
    
    print("\n--- Success! Ingestion Pipeline Complete ---")

if __name__ == "__main__":
    build_memory()