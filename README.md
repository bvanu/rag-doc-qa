# RAG Document Q&A

A retrieval-augmented (RAG) API to upload documents and ask questions about them
in plain English. Built with FastAPI, PostgreSQL + pgvector, and sentence-transformer embeddings.

## What it does
- Upload text or PDF documents via a REST API
- Documents are chunked, embedded, and stored as vectors in PostgreSQL (pgvector)
- Ask a question → it embeds the question, finds the most semantically similar
  chunks, and returns them with their source document and similarity score

## Architecture
Upload → chunk (~1000 chars, 150 overlap) → embed (all-MiniLM-L6-v2, 384-dim) → store in pgvector
Query → embed question → nearest-neighbor search (pgvector `<=>`) → return top-k relevant chunks

## Tech stack
FastAPI · PostgreSQL + pgvector (hosted on Neon) · sentence-transformers · pdfplumber

## Endpoints
- `POST /upload` — ingest raw text
- `POST /upload-pdf` — ingest a PDF
- `POST /query` — ask a question, get the most relevant chunks
- `GET /` — health check

## Setup
\`\`\`bash
git clone https://github.com/<your-username>/rag-doc-qa.git
cd rag-doc-qa
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://...neon.tech/...?sslmode=require"
uvicorn app:app --reload
\`\`\`
Open http://127.0.0.1:8000/docs

## Demo
![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)
Live demo: [your Render URL, once deployed]