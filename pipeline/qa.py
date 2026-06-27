import os
from dotenv import load_dotenv
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding

load_dotenv()
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Setup LlamaIndex components using NVIDIA NIM
embed_model = NVIDIAEmbedding(
    model="nvidia/nv-embedqa-e5-v5", 
    api_key=NVIDIA_API_KEY, 
    base_url="https://integrate.api.nvidia.com/v1"
)
Settings.embed_model = embed_model

def set_llm_temperature(temp: float):
    Settings.llm = NVIDIA(
        model="meta/llama-3.1-70b-instruct", 
        temperature=temp, 
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1"
    )

# Initialize with default
set_llm_temperature(0.0)

system_prompt = (
    "You answer questions about images and documents. "
    "Cite the source image filename and detected objects when answering."
)

def get_chat_engine(top_k=5):
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = client.get_or_create_collection(name="visionrag_docs_nvidia")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # Fix for Pydantic v2 bug where _collection is not added to __pydantic_private__
    if hasattr(vector_store, '__pydantic_private__') and vector_store.__pydantic_private__ is not None:
        vector_store.__pydantic_private__['_collection'] = chroma_collection
    elif hasattr(vector_store, '__pydantic_private__') and vector_store.__pydantic_private__ is None:
        vector_store.__pydantic_private__ = {'_collection': chroma_collection}
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=system_prompt,
        similarity_top_k=top_k
    )
    return chat_engine

import base64
from io import BytesIO
from PIL import Image
import time
from openai import OpenAI

# Native OpenAI client for Vision inference
nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

def summarize_content(img: Image.Image, text: str) -> str:
    """Uses NVIDIA Llama 3.2 90B Vision to summarize the image visually, and includes OCR text if available."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Convert PIL Image to Base64
            buffered = BytesIO()
            # Convert RGBA to RGB if needed to save as JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buffered, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            prompt = (
                "Analyze this image and provide a 1-sentence summary of what it shows. "
                "If it's a document, summarize its purpose. If it's a photo, describe the scene. "
            )
            
            if text.strip():
                prompt += f"\n\nThe following text was also extracted from the image via OCR. Extract any key entities (names, dates, amounts) from it:\n{text[:2000]}"
                
            response = nim_client.chat.completions.create(
                model="meta/llama-3.2-90b-vision-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }],
                max_tokens=250,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg or "rate limit" in error_msg.lower():
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return "⚠️ NVIDIA API Rate Limit Reached. Auto-Summary skipped for this page."
            return f"⚠️ Error generating AI summary: {e}"
