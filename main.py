from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import json
from PIL import Image
import fitz
import io
import time

# Pipeline imports
from pipeline.detector import detect_objects
from pipeline.ocr import extract_text
from utils.image_utils import preprocess_for_ocr
from pipeline.embedder import embed_image_content, embed_model
from pipeline.indexer import index_chunks, visual_search, collection
from pipeline.qa import get_chat_engine, summarize_content, set_llm_temperature

app = FastAPI(title="VisionRAG Pro API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join("data", "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount the uploaded images directory so the frontend can display them!
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    conf_threshold: float = Form(0.25),
    enable_auto_summary: bool = Form(True)
):
    master_report = []
    
    for file in files:
        filename = file.filename
        file_bytes = await file.read()
        
        images_to_process = [] # Tuples of (Image, Optional[extracted_text])
        
        if filename.lower().endswith(".pdf"):
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    if len(images_to_process) >= 2: # Cap at 2 pages to prevent browser timeouts
                        break
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data)).convert("RGB")
                    native_text = page.get_text()
                    images_to_process.append((img, native_text))
            except Exception as e:
                return {"error": f"Error reading PDF {filename}: {str(e)}"}
        else:
            try:
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                images_to_process.append((img, None))
            except Exception as e:
                return {"error": f"Error reading image {filename}: {str(e)}"}
        
        for page_idx, (img, native_text) in enumerate(images_to_process):
            img_path = os.path.join(UPLOAD_DIR, f"{filename}_p{page_idx}.png")
            img.save(img_path)
            
            # For serving over HTTP
            img_url = f"/images/{filename}_p{page_idx}.png"
            
            # 1. Detection
            annotated_img, detection_summary, detected_objects = detect_objects(img, conf_threshold=conf_threshold)
            
            # 2. Text Extraction (OCR or Native)
            if native_text and native_text.strip():
                ocr_text = native_text
            else:
                preprocessed_img = preprocess_for_ocr(img)
                ocr_text = extract_text(preprocessed_img)
            
            # 3. AI Summary
            summary_text = "AI Auto-Summary Disabled."
            if enable_auto_summary:
                if page_idx < 3: # Limit to first 3 pages to prevent Gemini rate limit timeouts
                    summary_text = summarize_content(img, ocr_text)
                else:
                    summary_text = "AI Auto-Summary skipped for this page to conserve API limits."
            
            # 4. Embed & Index
            embedded_chunks = embed_image_content(
                filename=filename, page_num=page_idx+1,
                detection_summary=detection_summary, ocr_text=ocr_text,
                detected_objects=detected_objects
            )
            for chunk in embedded_chunks:
                chunk['metadata']['img_path'] = img_path
                chunk['metadata']['img_url'] = img_url # Add URL for frontend
            
            if embedded_chunks:
                index_chunks(embedded_chunks)
                
            report_entry = {
                "filename": filename,
                "page": page_idx + 1,
                "objects_detected": len(detected_objects),
                "ocr_character_count": len(ocr_text),
                "summary": summary_text,
                "vectors_generated": len(embedded_chunks),
                "img_url": img_url,
                "detected_objects": detected_objects
            }
            master_report.append(report_entry)
            
    return {"status": "success", "results": master_report}

@app.post("/api/search")
async def perform_search(
    query: str = Form(...),
    object_filter: Optional[str] = Form(None),
    top_k: int = Form(6)
):
    query_embedding = embed_model.get_text_embedding(query)
    results = visual_search(
        query_embedding=query_embedding,
        object_class=object_filter if object_filter else None,
        top_k=top_k
    )
    
    formatted_results = []
    if results and results['ids'] and results['ids'][0]:
        for idx in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][idx],
                "distance": results['distances'][0][idx],
                "metadata": results['metadatas'][0][idx]
            })
            
    return {"results": formatted_results}

from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

# Global chat engine instance
chat_engine_instance = None

@app.post("/api/chat")
async def chat_with_docs(request: ChatRequest):
    global chat_engine_instance
    if not chat_engine_instance:
        chat_engine_instance = get_chat_engine()
        
    try:
        response = chat_engine_instance.stream_chat(request.message)
        
        def event_generator():
            try:
                for token in response.response_gen:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    
                sources = []
                for node in response.source_nodes:
                    sources.append({
                        "score": node.score,
                        "filename": node.metadata.get('filename'),
                        "page_num": node.metadata.get('page_num'),
                        "img_url": node.metadata.get('img_url'),
                        "text": node.text[:200]
                    })
                yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as stream_err:
                error_str = str(stream_err)
                if "429" in error_str or "Quota" in error_str:
                    error_str = "Google Gemini Free-Tier limit reached! Please wait a moment before asking another question."
                yield f"data: {json.dumps({'type': 'error', 'content': error_str})}\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/clear")
async def clear_chat():
    global chat_engine_instance
    if chat_engine_instance:
        chat_engine_instance.reset()
    return {"status": "cleared"}

@app.get("/api/analytics")
async def get_analytics():
    total_chunks = collection.count()
    all_data = collection.get(include=['metadatas'])
    metadatas = all_data['metadatas']
    
    unique_images = set()
    class_counts = {}
    
    for meta in metadatas:
        filename = meta.get('filename')
        page_num = meta.get('page_num')
        unique_images.add(f"{filename}_{page_num}")
        try:
            objs = json.loads(meta.get('detected_objects_json', '[]'))
            for obj in objs:
                cls_name = obj['class']
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
        except:
            pass
            
    return {
        "total_chunks": total_chunks,
        "unique_pages": len(unique_images),
        "total_objects": sum(class_counts.values()),
        "class_counts": class_counts
    }

@app.get("/api/knowledge-graph")
async def get_knowledge_graph():
    try:
        all_data = collection.get(limit=15)
        docs = all_data.get('documents', [])
        
        if not docs:
            return {"nodes": [], "links": []}
            
        combined_text = "\\n".join(docs)[:8000]
        
        prompt = """
        Extract a knowledge graph from the following text. Identify key entities (like People, Organizations, Concepts, Locations) and the relationships between them.
        Return ONLY a valid JSON object with this exact structure, with NO markdown formatting:
        {
          "nodes": [{"id": "Entity Name", "group": 1}],
          "links": [{"source": "Entity Name 1", "target": "Entity Name 2", "label": "relationship"}]
        }
        Group 1 = Person, Group 2 = Organization, Group 3 = Concept, Group 4 = Location.
        
        Example Output:
        {
          "nodes": [{"id": "NVIDIA", "group": 2}, {"id": "AI", "group": 3}],
          "links": [{"source": "NVIDIA", "target": "AI", "label": "builds"}]
        }
        
        Text:
        """ + combined_text[:4000]
        
        from openai import OpenAI
        import time
        nim_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )
        
        max_retries = 3
        temp = 0.1
        for attempt in range(max_retries):
            try:
                response = nim_client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )
                json_str = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                json_str = json_str.replace("```JSON", "").strip()
                
                # In case Llama 3 responds with conversational text before the JSON, try to extract it
                if "{" in json_str:
                    json_str = json_str[json_str.find("{") : json_str.rfind("}") + 1]
                    
                graph_data = json.loads(json_str)
                return graph_data
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    # Dynamic temperature increase to escape bad JSON generation loop
                    temp += 0.3 
                    continue
                raise e
    except Exception as e:
        print(f"Error generating KG: {e}")
        return {"error": str(e), "nodes": [], "links": []}
