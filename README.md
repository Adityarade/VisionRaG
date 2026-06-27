# 👁️‍🗨️ VisionRAG Pro

![License](https://img.shields.io/badge/License-MIT-blue.svg) ![Version](https://img.shields.io/badge/Version-1.0.0-green.svg) ![Platform](https://img.shields.io/badge/Platform-Web-gray.svg)

---

## 📋 Table of Contents
- [Description](#-description)
- [Demo Video](#-demo-video)
- [Features](#-features)
- [User Journey](#-user-journey)
- [Project Structure](#-project-structure)
- [Built With](#-built-with)
- [Installation & Setup](#-installation--setup)

---

## 📑 Description

**VisionRAG Pro** is an Enterprise AI Document Intelligence platform. It allows you to instantly process, extract, and chat with visual documents using a powerful multimodal neural pipeline. By combining cutting-edge object detection (YOLOv8) with NVIDIA's Llama 3 models and ChromaDB vector retrieval, VisionRAG Pro can "see" your documents, understand their layout, and answer questions about them with high accuracy.

---

## 🎥 Demo Video

See VisionRAG Pro in Action!

📺 [Watch Demo Video](#) *(Coming soon)*

*Experience the power of visual document intelligence, AI summarization, and multimodal chat.*

---

## ✨ Features

- 📄 **Visual Document Ingestion**: Upload images or PDFs. The pipeline automatically extracts text via OCR (Tesseract) and detects visual elements (Charts, Tables, Signatures) using YOLOv8.
- 🧠 **AI Auto-Summarization**: Uses NVIDIA Llama 3.2 Vision to visually analyze and summarize the content of each page.
- 💬 **RAG Chat Assistant**: Ask questions about your documents. The system uses NVIDIA EmbedQA to embed your data into a ChromaDB vector store, retrieving the most relevant chunks using Similarity Search (Top-K).
- 🎨 **Beautiful Glassmorphism UI**: A sleek, hot-reloading React/Vite frontend featuring live system analytics and interactive charts.

---

## 🗺️ User Journey

**Upload Document &rarr; Visual Object Detection &rarr; AI Summarization &rarr; Vector Embedding &rarr; RAG Chat**

The journey transforms unstructured visual documents into highly queryable knowledge. Users upload their PDF or images, instantly see how the AI detects charts and text, and then receive a comprehensive summary. Finally, the system allows users to seamlessly chat with their documents to extract precise information and insights.

---

## 📁 Project Structure

```text
VisionRAG/
├── frontend/               # React Application (Vite + Recharts)
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── App.jsx         # Main Dashboard & Chat interface
│   │   └── main.jsx        # React entry point
│   └── package.json
├── pipeline/               # Core AI & Neural Pipeline
│   ├── detector.py         # YOLOv8 Object Detection
│   ├── embedder.py         # NVIDIA NIM Embedding logic
│   ├── indexer.py          # Document chunking & ChromaDB
│   ├── ocr.py              # Tesseract OCR extraction
│   └── qa.py               # Llama-3.1 RAG Chat generation
├── main.py                 # FastAPI Backend Server & Endpoints
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (NVIDIA_API_KEY)
```

---

## 🛠️ Built With

Here are the major tools and technologies used to build VisionRAG Pro:

### Backend & AI
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge&logo=yolo&logoColor=black) ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge) ![NVIDIA](https://img.shields.io/badge/NVIDIA_NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)

### Frontend
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB) ![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E) ![CSS](https://img.shields.io/badge/Vanilla_CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white) ![Recharts](https://img.shields.io/badge/Recharts-22B5BF?style=for-the-badge)

---

## 📦 Installation & Setup

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

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
