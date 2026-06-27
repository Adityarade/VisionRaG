import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv

load_dotenv()
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Initialize ChromaDB Client
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name="visionrag_docs_nvidia")

def index_chunks(embedded_chunks: list):
    """
    Upserts embedded chunks into ChromaDB.
    """
    if not embedded_chunks:
        return
        
    ids = [chunk['id'] for chunk in embedded_chunks]
    embeddings = [chunk['embedding'] for chunk in embedded_chunks]
    documents = [chunk['text'] for chunk in embedded_chunks]
    metadatas = [chunk['metadata'] for chunk in embedded_chunks]
    
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

def visual_search(query_embedding: list, object_class: str = None, top_k: int = 5):
    """
    Performs similarity search, optionally filtered by detected object class.
    Returns top_k results.
    """
    where_filter = None
    if object_class and object_class.strip():
        # ChromaDB supports filtering. Our classes_detected is a comma-separated string.
        # Note: ChromaDB $contains operator works for strings.
        where_filter = {"classes_detected": {"$contains": object_class}}
        
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=['documents', 'metadatas', 'distances']
    )
    
    return results
