"""
Run RAGAS evaluation on FinSight.

Usage:
    python backend/run_eval.py

Output:
    - Prints scores to console
    - Saves results to backend/eval_results.json
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.core.retriever import build_hybrid_retriever_from_files
from backend.app.core.agent import build_agent
from backend.app.core.evaluator import run_evaluation

PDF_FILES = [
    "NVIDIAAn 2025.pdf",
    "NVIDIAAn 2026.pdf",
]
EVAL_DATASET = "backend/eval_dataset.json"
OUTPUT_FILE = "backend/eval_results.json"


def main():
    print("Building hybrid retriever...")
    retriever = build_hybrid_retriever_from_files(PDF_FILES)

    print("Building LCEL agent...")
    agent_executor = build_agent(retriever)

    print("Loading test cases...")
    with open(EVAL_DATASET) as f:
        test_cases = json.load(f)

    print(f"Running RAGAS evaluation on {len(test_cases)} questions...\n")
    result = run_evaluation(
        retriever=retriever,
        agent_executor=agent_executor,
        test_cases=test_cases,
    )

    print(result.summary())

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
