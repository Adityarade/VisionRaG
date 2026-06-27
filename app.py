import streamlit as st
import os
import time
import json
import pandas as pd
import plotly.express as px
import httpx

# --- Fix for httpx>=0.28.0 breaking OpenAI ---
_orig_sync_init = httpx.Client.__init__
_orig_async_init = httpx.AsyncClient.__init__

def _patched_sync_init(self, *args, **kwargs):
    kwargs.pop('proxies', None)
    return _orig_sync_init(self, *args, **kwargs)

def _patched_async_init(self, *args, **kwargs):
    kwargs.pop('proxies', None)
    return _orig_async_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_sync_init
httpx.AsyncClient.__init__ = _patched_async_init
# ---------------------------------------------
from PIL import Image
import fitz # PyMuPDF
import io
from dotenv import load_dotenv

# Set page config first - Force collapsed sidebar
st.set_page_config(page_title="VisionRAG Pro", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# --- Custom Vibrant Dashboard CSS ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide the sidebar toggle button completely */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Hide Default Top Header */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #1E293B;
    }
    
    /* Enhanced Animated Navigation Panel */
    div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        gap: 20px;
        background: rgba(248, 250, 252, 0.7);
        backdrop-filter: blur(15px);
        padding: 15px;
        border-radius: 50px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.1);
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    div[role="radiogroup"] > label {
        padding: 12px 25px;
        border-radius: 40px;
        background-color: white;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: 2px solid transparent;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    div[role="radiogroup"] > label:hover {
        background-color: #ffffff;
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 25px -10px rgba(79, 70, 229, 0.3);
        border: 2px solid #E0E7FF;
        z-index: 10;
    }
    /* Style the active radio button */
    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        border-color: transparent;
        box-shadow: 0 10px 20px -5px rgba(79, 70, 229, 0.5);
        transform: scale(1.02);
    }
    div[role="radiogroup"] > label[data-checked="true"]:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 15px 25px -5px rgba(79, 70, 229, 0.7);
    }
    div[role="radiogroup"] > label[data-checked="true"] div, div[role="radiogroup"] > label[data-checked="true"] p {
        color: white !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    div[role="radiogroup"] > label div, div[role="radiogroup"] > label p {
        font-weight: 900 !important;
        font-size: 16px !important;
        letter-spacing: 0.5px;
        color: #4F46E5 !important; /* Vibrant Indigo Text instead of gray */
        text-transform: uppercase;
        transition: color 0.3s ease;
    }
    
    /* Smooth button hover */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards for metrics/results */
    div.css-1r6slb0, div[data-testid="metric-container"], .gallery-card { 
        border-radius: 16px;
        padding: 20px;
        background: white;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    .gallery-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Vibrant Analytics Cards */
    .metric-card {
        padding: 25px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-card h2 { color: white; font-size: 3rem; margin: 0; }
    .metric-card p { font-size: 1.2rem; margin: 0; opacity: 0.9; font-weight: 500; }
    
    .bg-teal { background: linear-gradient(135deg, #2DD4BF 0%, #0D9488 100%); }
    .bg-pink { background: linear-gradient(135deg, #F472B6 0%, #DB2777 100%); }
    .bg-violet { background: linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%); }
    
    /* Sticky Footer & Header */
    .custom-footer, .custom-header {
        position: fixed;
        left: 0;
        width: 100%;
        background-color: #0F172A;
        color: #94A3B8;
        text-align: center;
        padding: 12px;
        font-size: 14px;
        z-index: 9999;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .custom-footer { bottom: 0; }
    .custom-header { top: 0; border-bottom: 2px solid #38BDF8; }
    
    .custom-footer span, .custom-header span { color: #38BDF8; font-weight: 700; letter-spacing: 0.5px; }
    .block-container { 
        padding-bottom: 80px !important; 
        padding-top: 60px !important; 
    }
    
    /* Smooth Scrolling & Sticky Nav for Landing Page */
    html, body, div[data-testid="stAppViewContainer"], .stApp { scroll-behavior: smooth !important; }
    .sticky-nav {
        position: sticky; top: 0px; 
        background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
        padding: 15px 0; border-bottom: 1px solid #e2e8f0; border-radius: 8px;
        z-index: 999; display: flex; justify-content: center; gap: 30px;
        margin-bottom: 30px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .sticky-nav a { color: #4F46E5; text-decoration: none; font-weight: 700; font-size: 16px; transition: color 0.2s; }
    .sticky-nav a:hover { color: #FF6B6B; }
    .anchor-section { scroll-margin-top: 100px; }
</style>
""", unsafe_allow_html=True)

# Lazy load modules
from pipeline.detector import detect_objects
from utils.image_utils import preprocess_for_ocr
from pipeline.ocr import extract_text
from pipeline.embedder import embed_image_content
from pipeline.indexer import index_chunks, visual_search, collection
from pipeline.qa import get_chat_engine, summarize_text, set_llm_temperature

load_dotenv()
UPLOAD_DIR = os.path.join("data", "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Render Custom Global Header ---
st.markdown("""
    <div class="custom-header">
        <span>VISIONRAG PRO</span> &nbsp; | &nbsp; Multimodal RAG Pipeline
    </div>
""", unsafe_allow_html=True)

# --- LOGO SECTION ---
col_b1, col_logo, col_b2 = st.columns([3, 1, 3])
with col_logo:
    st.image(r"C:\Users\adity\.gemini\antigravity\brain\11256803-6edd-4c16-b31d-b196a79d131c\visionrag_logo_white_1781248188976.png", use_column_width=True)

# --- INLINE NAVIGATION ---
page = st.radio("Navigation", 
                ["🏠 Home", "🚀 Upload & Process", "🔍 Visual Search", "💬 Ask About Images", "📈 Analytics Dashboard"], 
                horizontal=True, 
                label_visibility="collapsed")

# --- GLOBAL SETTINGS MODULE (Dropdown) ---
with st.expander("⚙️ Advanced Settings Module", expanded=False):
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        conf_threshold = st.slider("Detection Confidence", min_value=0.1, max_value=0.9, value=0.25, step=0.05, help="Filter out low-confidence object detections.")
    with col_s2:
        llm_temp = st.slider("LLM Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1, help="0.0 = Strict & Factual. 1.0 = Creative & Loose.")
        set_llm_temperature(llm_temp)
    with col_s3:
        top_k_search = st.slider("Top-K Search Results", min_value=3, max_value=12, value=6, step=3, help="How many images to retrieve in Visual Search.")
    with col_s4:
        st.markdown("<br>", unsafe_allow_html=True)
        enable_auto_summary = st.toggle("Enable AI Auto-Summary", value=True, help="Automatically run LLM summarization on uploaded images.")

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Page: Home / Landing Page ---
if page == "🏠 Home":
    st.markdown("""
        <div class='sticky-nav'>
            <a href="#about-visionrag">About</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#faq">FAQ</a>
        </div>
        
        <div style='background: linear-gradient(135deg, #FF6B6B 0%, #4FACFE 100%); padding: 4rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 3rem; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);'>
            <h1 style='color: white; font-size: 3.5rem; margin-bottom: 1rem; font-family: Outfit;'>Welcome to VisionRAG Pro</h1>
            <p style='font-size: 1.4rem; opacity: 0.95; font-weight: 500;'>The Colorful, Enterprise Multimodal AI Pipeline.</p>
        </div>
        
        <div id="about-visionrag" class="anchor-section">
            <h2 style='color: #FF6B6B;'>About VisionRAG</h2>
            <div style='background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                <p style='font-size: 1.1rem; color: #334155; line-height: 1.7;'>
                    VisionRAG is a state-of-the-art multimodal application designed to bridge the gap between unstructured visual data and intelligent search. 
                    Unlike traditional databases that only understand text, VisionRAG uses advanced Computer Vision (YOLOv8) to detect objects in images, Optical Character Recognition (Tesseract) to extract embedded text, and Large Language Models (GPT-4o) to summarize and reason over that data. 
                </p>
            </div>
        </div>
        
        <div id="how-it-works" class="anchor-section">
            <h2 style='color: #4FACFE;'>How It Works</h2>
            <div style='display: flex; justify-content: space-between; gap: 20px; margin-bottom: 3rem;'>
                <div style='flex: 1; background: white; padding: 30px 20px; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                    <h1 style='font-size: 4rem; margin: 0; color: #FF6B6B; font-family: Outfit;'>1</h1>
                    <h3 style='color: #1E293B;'>Ingestion</h3>
                    <p style='color: #64748b;'>Upload images or PDFs. The system extracts text via OCR and detects objects using YOLO.</p>
                </div>
                <div style='flex: 1; background: white; padding: 30px 20px; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                    <h1 style='font-size: 4rem; margin: 0; color: #4FACFE; font-family: Outfit;'>2</h1>
                    <h3 style='color: #1E293B;'>Processing</h3>
                    <p style='color: #64748b;'>Data is summarized by an LLM and stored securely in a local ChromaDB instance.</p>
                </div>
                <div style='flex: 1; background: white; padding: 30px 20px; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                    <h1 style='font-size: 4rem; margin: 0; color: #2DD4BF; font-family: Outfit;'>3</h1>
                    <h3 style='color: #1E293B;'>Retrieval</h3>
                    <p style='color: #64748b;'>Query the system using natural language or dynamic visual search.</p>
                </div>
            </div>
        </div>
        
        <div id="faq" class="anchor-section">
            <h2 style='color: #A78BFA; margin-bottom: 1rem;'>Frequently Asked Questions</h2>
    """, unsafe_allow_html=True)
    
    with st.expander("What models are powering this application?"):
        st.write("""
        - **Object Detection:** YOLOv8
        - **Optical Character Recognition:** Tesseract OCR
        - **Summarization & Chat Agent:** Google Gemini `gemini-2.5-flash`
        - **Vector Embeddings:** Google Gemini `gemini-embedding-2`
        """)
    with st.expander("How is the data stored securely?"):
        st.write("All vectorized data is stored locally on your machine using a persistent ChromaDB instance. Data is only sent externally when generating LLM embeddings or summaries via API.")
    with st.expander("Can it handle multi-page PDFs?"):
        st.write("Yes! The ingestion engine automatically splits multi-page PDFs into individual images, running OCR and detection on every single page separately to ensure high granularity during search.")

# --- Page: Upload & Process ---
elif page == "🚀 Upload & Process":
    st.markdown("""
        <div style='background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);'>
            <h1 style='color: white; margin:0; font-family: Outfit;'>Upload & Ingestion Engine</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem;'>Upload documents to run the multi-stage AI extraction pipeline.</p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("Drop your files here", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if not uploaded_files:
        st.info("Awaiting file upload... Drop a dense PDF or photograph above to ignite the pipeline.")
        
    elif uploaded_files and st.button("🚀 Execute Neural Pipeline", type="primary"):
        total_files = len(uploaded_files)
        master_report = []
        
        for i, file in enumerate(uploaded_files):
            filename = file.name
            
            with st.status(f"⚙️ Processing Payload: {filename}", expanded=True) as status:
                st.write(f"[`{time.strftime('%H:%M:%S')}`] 📥 Initializing data ingestion module...")
                
                images_to_process = [] # Will hold tuples of (Image, Optional[extracted_text])
                if filename.lower().endswith(".pdf"):
                    try:
                        st.write(f"[`{time.strftime('%H:%M:%S')}`] 📄 Detected PDF format. Slicing into component frames...")
                        pdf_bytes = file.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        for page in doc:
                            pix = page.get_pixmap()
                            img_data = pix.tobytes("png")
                            img = Image.open(io.BytesIO(img_data)).convert("RGB")
                            # Extract native text directly from the PDF page
                            native_text = page.get_text()
                            images_to_process.append((img, native_text))
                    except Exception as e:
                        status.update(label=f"Error reading PDF {filename}", state="error")
                        st.error(str(e))
                        continue
                else:
                    try:
                        img = Image.open(file).convert("RGB")
                        images_to_process.append((img, None))
                    except Exception as e:
                        status.update(label=f"Error reading image {filename}", state="error")
                        st.error(str(e))
                        continue
                
                for page_idx, (img, native_text) in enumerate(images_to_process):
                    st.write(f"[`{time.strftime('%H:%M:%S')}`] 👁️ Running YOLOv8 object detection on frame {page_idx+1}...")
                    img_path = os.path.join(UPLOAD_DIR, f"{filename}_p{page_idx}.png")
                    img.save(img_path)
                    
                    annotated_img, detection_summary, detected_objects = detect_objects(img, conf_threshold=conf_threshold)
                    
                    if native_text and native_text.strip():
                        st.write(f"[`{time.strftime('%H:%M:%S')}`] 📄 Using native PDF text extraction (Bypassing OCR)...")
                        ocr_text = native_text
                    else:
                        st.write(f"[`{time.strftime('%H:%M:%S')}`] 🔤 Initializing Tesseract OCR engine...")
                        preprocessed_img = preprocess_for_ocr(img)
                        ocr_text = extract_text(preprocessed_img)
                    
                    summary_text = "AI Auto-Summary Disabled."
                    if enable_auto_summary:
                        if ocr_text.strip():
                            st.write(f"[`{time.strftime('%H:%M:%S')}`] 🧠 Connecting to Gemini 2.5 for semantic analysis...")
                            summary_text = summarize_text(ocr_text)
                        else:
                            summary_text = "No readable text found for AI Insights."
                            
                    st.write(f"[`{time.strftime('%H:%M:%S')}`] 🧬 Generating 1536-dimensional embeddings & storing to ChromaDB...")
                    embedded_chunks = embed_image_content(
                        filename=filename, page_num=page_idx+1,
                        detection_summary=detection_summary, ocr_text=ocr_text,
                        detected_objects=detected_objects
                    )
                    for chunk in embedded_chunks:
                        chunk['metadata']['img_path'] = img_path
                    
                    if embedded_chunks:
                        index_chunks(embedded_chunks)
                        
                    report_entry = {
                        "filename": filename,
                        "page": page_idx + 1,
                        "objects_detected": len(detected_objects),
                        "ocr_character_count": len(ocr_text),
                        "summary": summary_text,
                        "vectors_generated": len(embedded_chunks)
                    }
                    master_report.append(report_entry)
                    
                status.update(label=f"✅ Payload Processed: {filename}", state="complete", expanded=False)
            
            # --- Enterprise Output Presentation ---
            st.markdown(f"### 📄 Analysis Results: `{filename}`")
            
            tab1, tab2, tab3 = st.tabs(["👁️ Vision Analysis", "📝 OCR & AI Insights", "💾 Vector Metadata"])
            
            with tab1:
                col_img, col_data = st.columns([1.5, 1])
                with col_img:
                    st.image(annotated_img, caption="YOLOv8 Bounding Box Annotations", use_column_width=True)
                with col_data:
                    st.markdown("#### 📊 Detected Entities")
                    if detected_objects:
                        df_objs = pd.DataFrame(detected_objects)
                        st.dataframe(df_objs, use_container_width=True, hide_index=True)
                    else:
                        st.info("No physical objects detected above threshold.")
                        
            with tab2:
                if enable_auto_summary:
                    st.success(f"**Gemini 2.5 Analysis:**\n\n{summary_text}")
                st.markdown("#### 📝 Raw Extracted Text")
                st.text_area("Tesseract OCR Output", ocr_text if ocr_text.strip() else "No text found.", height=250, disabled=True, label_visibility="collapsed")
                
            with tab3:
                st.markdown("#### 🧬 ChromaDB Payload")
                st.json({
                    "database": "visionrag_docs",
                    "chunk_count": len(embedded_chunks),
                    "embedding_model": "text-embedding-3-small",
                    "dimensions": 1536,
                    "metadata_snapshot": embedded_chunks[0]['metadata'] if embedded_chunks else "None"
                })
            
            st.divider()
            
        st.success("✅ Enterprise pipeline execution complete. All data successfully indexed.")
        st.balloons()
        
        # Download Report
        report_json = json.dumps(master_report, indent=4)
        st.download_button(
            label="📥 Download Pipeline Extraction Report (JSON)",
            data=report_json,
            file_name="visionrag_extraction_report.json",
            mime="application/json",
            type="primary"
        )

# --- Page: Visual Search ---
elif page == "🔍 Visual Search":
    st.markdown("""
        <div style='background: linear-gradient(135deg, #2DD4BF 0%, #0D9488 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);'>
            <h1 style='color: white; margin:0; font-family: Outfit;'>🖼️ Visual Image Gallery Search</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem;'>Search across your indexed documents using semantics.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("search_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            query = st.text_input("Semantic Query", placeholder="e.g., 'A financial report from Q3'")
        with col2:
            object_filter = st.text_input("Object Class Filter", placeholder="e.g., 'laptop', 'person'")
        submitted = st.form_submit_button("Search Indexed Database")
    
    if submitted and query:
        with st.spinner("Searching..."):
            from pipeline.embedder import embed_model
            query_embedding = embed_model.get_text_embedding(query)
            
            results = visual_search(
                query_embedding=query_embedding,
                object_class=object_filter if object_filter else None,
                top_k=top_k_search # Dynamic Top-K from Settings
            )
            
            if not results or not results['ids'] or not results['ids'][0]:
                st.warning("No matching results found in the database.")
            else:
                st.success(f"Found {len(results['ids'][0])} highly relevant results.")
                cols = st.columns(3)
                for idx in range(len(results['ids'][0])):
                    col = cols[idx % 3]
                    distance = results['distances'][0][idx]
                    metadata = results['metadatas'][0][idx]
                    similarity_score = (1 - distance) * 100
                    img_path = metadata.get('img_path', None)
                    
                    with col:
                        st.markdown("<div class='gallery-card'>", unsafe_allow_html=True)
                        if img_path and os.path.exists(img_path):
                            st.image(img_path, use_column_width=True)
                        else:
                            st.info("Image not available locally.")
                            
                        st.markdown(f"**{metadata.get('filename')} (P{metadata.get('page_num')})**")
                        st.progress(int(similarity_score) if similarity_score > 0 else 0)
                        st.caption(f"Score: {similarity_score:.1f}%")
                        
                        with st.expander("Classes"):
                            objs = json.loads(metadata.get('detected_objects_json', '[]'))
                            classes = [obj['class'] for obj in objs]
                            st.markdown(" ".join([f"`{c}`" for c in set(classes)]) if classes else "None")
                        st.markdown("</div>", unsafe_allow_html=True)

# --- Page: Ask About Images ---
elif page == "💬 Ask About Images":
    st.markdown("""
        <div style='background: linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);'>
            <h1 style='color: white; margin:0; font-family: Outfit;'>💬 Conversational AI Assistant</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem;'>Chat with your documents using advanced memory.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_chat, col_controls = st.columns([4, 1])
    with col_controls:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            if "chat_engine" in st.session_state:
                st.session_state.chat_engine.reset()
            st.rerun()
            
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = get_chat_engine()
        
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("E.g., What is the total on the invoice? -> Who is it billed to?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = st.session_state.chat_engine.stream_chat(prompt)
                full_response = ""
                for text_chunk in response.response_gen:
                    full_response += text_chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                if response.source_nodes:
                    with st.expander("📚 Sources & Citations"):
                        for i, node in enumerate(response.source_nodes):
                            st.markdown(f"**Source {i+1}** (Score: {node.score:.2f})")
                            st.caption(f"**File:** {node.metadata.get('filename')} (Page {node.metadata.get('page_num')})")
                            st.markdown(f"_{node.text[:200]}..._")
                            st.divider()
            except Exception as e:
                st.error(f"Error generating response: {e}")

# --- Page: Analytics Dashboard ---
elif page == "📈 Analytics Dashboard":
    st.markdown("""
        <div style='background: linear-gradient(135deg, #F472B6 0%, #DB2777 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);'>
            <h1 style='color: white; margin:0; font-family: Outfit;'>📈 Analytics Dashboard</h1>
            <p style='font-size: 1.1rem; margin-top: 0.5rem;'>View vibrant, high-level metrics of your indexed multimodal data.</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        total_chunks = collection.count()
        all_data = collection.get(include=['metadatas'])
        metadatas = all_data['metadatas']
        
        unique_images = set()
        class_counts = {}
        confidence_distribution = []
        
        for meta in metadatas:
            filename = meta.get('filename')
            page_num = meta.get('page_num')
            unique_images.add(f"{filename}_{page_num}")
            try:
                objs = json.loads(meta.get('detected_objects_json', '[]'))
                for obj in objs:
                    cls_name = obj['class']
                    conf = obj['confidence']
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                    confidence_distribution.append({'class': cls_name, 'confidence': conf})
            except:
                pass
                
        # Colorful Metric Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card bg-teal">
                    <p>Total Chunks in DB</p>
                    <h2>{total_chunks}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card bg-pink">
                    <p>Total Unique Pages</p>
                    <h2>{len(unique_images)}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-card bg-violet">
                    <p>Total Objects Detected</p>
                    <h2>{sum(class_counts.values())}</h2>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if class_counts:
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("Top Object Classes")
                df_classes = pd.DataFrame(list(class_counts.items()), columns=['Object Class', 'Count'])
                df_classes = df_classes.sort_values(by='Count', ascending=True)
                fig1 = px.bar(df_classes, x='Count', y='Object Class', orientation='h', 
                              color='Count', color_continuous_scale='Sunset',
                              title="Detected Object Frequencies")
                st.plotly_chart(fig1, use_container_width=True)
                
            with col_chart2:
                st.subheader("Confidence Scores by Class")
                df_conf = pd.DataFrame(confidence_distribution)
                if not df_conf.empty:
                    fig2 = px.box(df_conf, x='class', y='confidence', color='class',
                                  title="Confidence Distribution", points="all", color_discrete_sequence=px.colors.qualitative.Vivid)
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No objects detected yet. Please upload and process some images to populate the dashboard.")
            
    except Exception as e:
        st.error(f"Could not load analytics: {e}")

# --- Render Custom Footer at the very end ---
st.markdown("""
    <div class="custom-header">
        <span>VISIONRAG PRO</span> &nbsp; | &nbsp; Multimodal RAG Pipeline
    </div>
""", unsafe_allow_html=True)
