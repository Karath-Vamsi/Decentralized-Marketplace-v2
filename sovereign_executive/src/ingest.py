import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Configuration
KB_DIR = "../knowledge_base"
DB_DIR = "../chroma_db"

def build_memory():
    print("Initializing Digital Twin Memory Ingestion...")

    # 2. Load the "Knowledge Base"
    # We load everything from the folders we created
    loader = DirectoryLoader(KB_DIR, glob="./**/*.txt", loader_cls=TextLoader)
    try:
        documents = loader.load()
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    print(f"📄 Found {len(documents)} documents in your Knowledge Base.")

    # 3. Chunking
    # We break documents into 500-character pieces so the AI can find specific facts
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f"Created {len(texts)} memory chunks.")

    # 4. Local Embeddings (The "RAG Secret Sauce")
    # This model runs entirely on your CPU and is very fast.
    print("Generating mathematical embeddings (100% local)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 5. Create and Persist Vector Database
    # This saves the 'math version' of your knowledge to the chroma_db folder
    vectorstore = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings, 
        persist_directory=DB_DIR
    )
    
    print(f"Success! Your Twin's memory is now stored in: {DB_DIR}")

if __name__ == "__main__":
    build_memory()