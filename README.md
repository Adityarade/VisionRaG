# VisionRAG Pro 👁️🧠

VisionRAG Pro is an Enterprise AI Document Intelligence platform. It allows you to instantly process, extract, and chat with visual documents using a powerful multimodal neural pipeline.

By combining cutting-edge object detection (YOLOv8) with NVIDIA's Llama 3 models and ChromaDB vector retrieval, VisionRAG Pro can "see" your documents, understand their layout, and answer questions about them with high accuracy.

## 🚀 Features

- **Visual Document Ingestion**: Upload images or PDFs. The pipeline automatically extracts text via OCR (Tesseract) and detects visual elements (Charts, Tables, Signatures) using YOLOv8.
- **AI Auto-Summarization**: Uses NVIDIA Llama 3.2 Vision to visually analyze and summarize the content of each page.
- **RAG Chat Assistant**: Ask questions about your documents. The system uses NVIDIA EmbedQA to embed your data into a ChromaDB vector store, retrieving the most relevant chunks using Similarity Search (Top-K).
- **Beautiful Glassmorphism UI**: A sleek, hot-reloading React/Vite frontend featuring live system analytics and interactive charts.

## 🏗️ Architecture

- **Frontend**: React, Vite, Recharts
- **Backend**: Python, FastAPI, Uvicorn
- **AI Models**: 
  - Object Detection: YOLOv8 (ultralytics)
  - LLM & Chat: `meta/llama-3.1-70b-instruct` (via NVIDIA NIM)
  - Vision Summarization: `meta/llama-3.2-90b-vision-instruct` (via NVIDIA NIM)
  - Embeddings: `nvidia/nv-embedqa-e5-v5`
- **Database**: ChromaDB (Persistent Vector Store)

## 🛠️ Installation & Local Setup

### Prerequisites
- Python 3.10+
- Node.js & npm
- Tesseract OCR (Installed and added to PATH)
- NVIDIA NIM API Key (`NVIDIA_API_KEY`)

### Backend Setup
1. Open a terminal and navigate to the root directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your NVIDIA API key:
   ```env
   NVIDIA_API_KEY=your_api_key_here
   ```
4. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --port 8000
   ```

### Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## 🚢 Deployment

**Note**: This architecture requires a split deployment.
1. Deploy the `frontend/` directory to **Vercel** or **Netlify**.
2. Deploy the root directory (Backend) to a persistent Python host like **Render**, **Railway**, or a cloud VPS. 
*(Ensure you update the API URLs in `App.jsx` to point to your live backend before deploying the frontend).*

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
