from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import psycopg
from pgvector.psycopg import register_vector
import pdfplumber, io
import anthropic
import logging, time
from dotenv import load_dotenv
import os

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from your environment

class Query(BaseModel):
    question: str

load_dotenv()
DB = os.environ["DATABASE_URL"]

def chunk_text(text, size=1000, overlap=150):
    out, start = [], 0
    while start < len(text):
        out.append(text[start:start + size])
        start += size - overlap
    return out

class Doc(BaseModel):
    doc_id: str
    text: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/upload")
def upload(doc: Doc):
    chunks = chunk_text(doc.text)
    embs = model.encode(chunks)
    with psycopg.connect(DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for c, e in zip(chunks, embs):
                cur.execute(
                    "INSERT INTO chunks (doc_id, text, embedding) VALUES (%s, %s, %s)",
                    (doc.doc_id, c, e),
                )
    return {"inserted": len(chunks)}


@app.post("/query")
def query(q: Query):
    start = time.time()
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    q_emb = model.encode(q.question)
    with psycopg.connect(DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text, doc_id, embedding <=> %s AS distance FROM chunks ORDER BY distance LIMIT 4",
                (q_emb,),
            )
            rows = cur.fetchall()   # each row is (text, doc_id, distance)
            # cur.execute("SELECT text FROM chunks ORDER BY embedding <=> %s LIMIT 4", (q_emb,))
    # chunks = [row[0] for row in cur.fetchall()]
    chunks = [r[0] for r in rows]          # reuse rows — don't fetch again
    if not chunks:
        raise HTTPException(status_code=404, detail="No documents found — upload something first.")
    logger.info(f"query={q.question[:50]!r} -> {len(chunks)} chunks in {time.time()-start:.2f}s")
    THRESHOLD = 0.8   # tune this to your data
    results = [
        {"text": t[:120], "source": doc_id, "distance": float(d)}
        for t, doc_id, d in rows if d < THRESHOLD
    ]
    return {"matched_chunks": results}


@app.post("/upload-pdf")
def upload_pdf(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file.")
    contents = file.file.read()
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read that PDF — it may be corrupted.")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found — is this a scanned/image PDF? Those need OCR.")
    chunks = chunk_text(text)
    embs = model.encode(chunks)
    with psycopg.connect(DB) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for c, e in zip(chunks, embs):
                cur.execute("INSERT INTO chunks (doc_id, text, embedding) VALUES (%s,%s,%s)", (file.filename, c, e))
    return {"filename": file.filename, "chunks_inserted": len(chunks)}
