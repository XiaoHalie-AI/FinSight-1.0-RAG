"""
FinSight FastAPI backend.

Endpoints:
  POST /upload  — Upload PDFs, build hybrid retriever, return session_id
  POST /chat    — Streaming chat (SSE)
  GET  /eval    — Return RAGAS evaluation results
  GET  /health  — Health check
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.api.eval import router as eval_router

app = FastAPI(title="FinSight API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(eval_router)


@app.get("/health")
def health():
    return {"status": "ok"}
