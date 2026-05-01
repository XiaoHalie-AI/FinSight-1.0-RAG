# FinSight 1.0 — Agentic RAG Financial Research Platform


A production-grade agentic RAG system for financial document analysis. Upload earnings reports, ask questions, and get answers grounded in the source — with quantitative evaluation metrics to prove it.


---

## Architecture

```
Frontend (Next.js / TypeScript)
        │  SSE streaming / REST
        ▼
Backend (FastAPI / Python)
        │
        ├── POST /upload  →  PDF → chunks → BM25 + FAISS index
        ├── POST /chat    →  question → Agent → streaming tokens
        └── GET  /eval    →  RAGAS scores
                │
                ├── Retriever (BM25 + FAISS + Metadata Filter + Multi-Query)
                ├── ReAct Agent (LangChain LCEL)
                │     ├── PDF_Finance_Analyst  (RAG tool)
                │     ├── Get_Live_Stock_Price (yfinance)
                │     └── Web_Search           (DuckDuckGo)
                └── RAGAS Evaluation Pipeline
```

---

## Key Technical Decisions

### 1. Hybrid Retrieval (BM25 + FAISS)
Pure vector search misses exact financial terms like `EBITDA` or `Q4 FY26`. BM25 handles exact keyword matches while FAISS captures semantic similarity. Results are merged via **Reciprocal Rank Fusion**, then reranked by **FlashRank** (cross-encoder model) to keep the top 4 most relevant chunks.

### 2. Metadata Filtering
Each chunk is tagged at index time with structured metadata (`quarter`, `fiscal_year`) extracted via regex — zero LLM cost. At query time, the same regex runs on the question to build a FAISS filter, preventing FY25 chunks from polluting FY26 answers.

### 3. Multi-Query Expansion
An LLM rewrites each question into 3 alternative phrasings before retrieval. This improves recall for paraphrased or multi-part questions without changing the reranking or answer generation steps.

### 4. RAGAS Evaluation
Every retrieval improvement is measured with four quantitative metrics:

| Metric | Score | What it measures |
|--------|-------|-----------------|
| Faithfulness | **0.60** | Answers grounded in retrieved context (anti-hallucination) |
| Answer Relevancy | **0.60** | Answers directly address the question |
| Context Precision | **0.40** | Retrieved chunks are relevant |
| Context Recall | **0.40** | All necessary information is retrieved |

Adding Multi-Query expansion improved Faithfulness from **0.20 → 0.60** (3× improvement).

"Note: Scores are based on a sample dataset of NVIDIA FY25/FY26 earnings calls. Evaluation was conducted locally to optimize retrieval parameters before final implementation."

### 5. Streaming (SSE)
The FastAPI `/chat` endpoint uses Server-Sent Events. A background thread runs the synchronous `AgentExecutor` while a `StreamingCallbackHandler` puts each token into a queue. The Next.js frontend consumes the stream token-by-token, rendering the cursor in real time.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| LLM | GPT-4o-mini (OpenAI) |
| Embeddings | OpenAI `text-embedding-ada-002` |
| Vector Store | FAISS |
| Keyword Search | BM25 (rank-bm25) |
| Reranking | FlashRank (ms-marco-MultiBERT-L-12) |
| Agent Framework | LangChain LCEL, `create_react_agent` |
| Evaluation | RAGAS |

---

## Local Setup

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-..." > .env
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open `http://localhost:3000`, upload a PDF earnings report, and start asking questions.

---


**Security & Cost Management**
To ensure API key security and prevent unauthorized costs, this project is architected for local development and private demonstration.

1. Credential Isolation: All sensitive keys are managed via .env files, which are strictly excluded from version control via .gitignore.

2. Local-First Indexing: Utilizes FAISS for on-disk vector storage, eliminating the need (and cost) of managed cloud vector databases.

3. Budget-Friendly Evaluation: RAGAS testing is performed on targeted golden datasets to optimize performance without excessive LLM API consumption.


"Note: This project is architected for local demonstration to ensure API security and cost management. To run the platform, please clone the repo and provide your own OpenAI API key in a local .env file."

