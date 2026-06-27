import json
from utils.text_utils import chunk_text
from llama_index.embeddings.nvidia import NVIDIAEmbedding
import os

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Initialize NVIDIA NIM embedding model
embed_model = NVIDIAEmbedding(
    model="nvidia/nv-embedqa-e5-v5", 
    api_key=NVIDIA_API_KEY, 
    base_url="https://integrate.api.nvidia.com/v1"
)

def embed_image_content(filename: str, page_num: int, detection_summary: str, ocr_text: str, detected_objects: list):
    """
    Merges detection summary and OCR text, chunks it, and creates embeddings.
    Returns a list of dictionaries containing chunk text, embedding, and metadata.
    """
    # Merge content
    content = f"--- Image Description ---\n{detection_summary}\n\n--- OCR Text ---\n{ocr_text}"
    
    # Chunk text
    chunks = chunk_text(content, chunk_size=256, chunk_overlap=32)
    
    # Extract just the class names for metadata filtering
    classes_detected = list(set([obj['class'] for obj in detected_objects]))
    
    embedded_chunks = []
    
    if chunks:
        # Batch embedding for massive speedup!
        embeddings = embed_model.get_text_embedding_batch(chunks)
        
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            metadata = {
                "filename": filename,
                "page_num": page_num,
                "chunk_idx": idx,
                "classes_detected": ",".join(classes_detected), 
                "detected_objects_json": json.dumps(detected_objects)
            }
            
            embedded_chunks.append({
                "id": f"{filename}_p{page_num}_c{idx}",
                "text": chunk,
                "embedding": embedding,
                "metadata": metadata
            })
            
    return embedded_chunks
