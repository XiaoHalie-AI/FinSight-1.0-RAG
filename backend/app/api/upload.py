"""
POST /upload — Accept one or more PDF files, build hybrid retriever, return session_id.
"""

import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List

from app.core.retriever import build_hybrid_retriever_from_files
from app.core.agent import build_agent
from app.api.session import create_session

router = APIRouter()


@router.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    saved_paths = []
    tmp_dir = tempfile.mkdtemp()

    try:
        # Save uploaded files to a temp directory
        for file in files:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not a PDF."
                )
            dest = os.path.join(tmp_dir, file.filename)
            content = await file.read()
            with open(dest, "wb") as f:
                f.write(content)
            saved_paths.append(dest)

        # Build retriever and agent (this is the slow step — embeddings + BM25)
        retriever = build_hybrid_retriever_from_files(saved_paths)
        agent_executor = build_agent(retriever)
        session_id = create_session(retriever, agent_executor)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDFs: {str(e)}")

    return {
        "session_id": session_id,
        "files": [f.filename for f in files],
        "message": f"Processed {len(files)} PDF(s). Ready to chat."
    }
