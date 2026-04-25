"""
GET /eval — Return the latest RAGAS evaluation results.
"""

import json
import os

from fastapi import APIRouter, HTTPException

router = APIRouter()

EVAL_RESULTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "eval_results.json"
)


@router.get("/eval")
def get_eval_results():
    path = os.path.normpath(EVAL_RESULTS_PATH)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="No evaluation results found. Run `python backend/run_eval.py` first."
        )
    with open(path) as f:
        results = json.load(f)
    return results
