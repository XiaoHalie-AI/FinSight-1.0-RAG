"""
RAGAS evaluation pipeline for the FinSight RAG system.

Why RAGAS?
- Most RAG projects have no way to measure quality — this is the differentiator.
- RAGAS gives quantitative metrics (0-1 scale) that can be tracked across iterations.
- In interviews: "I improved Faithfulness from 0.71 to 0.89 by adding FlashRank reranking."

Metrics used:
- Faithfulness:      Does the answer stay faithful to retrieved context? (anti-hallucination)
- Answer Relevancy:  Does the answer actually address the question?
- Context Precision: Are the retrieved chunks relevant? (retrieval quality)
- Context Recall:    Did we retrieve all necessary information? (retrieval coverage)
"""

from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from ragas import evaluate, EvaluationDataset
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

load_dotenv()


@dataclass
class EvalResult:
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    def to_dict(self) -> dict:
        return {
            "faithfulness": round(self.faithfulness, 4),
            "answer_relevancy": round(self.answer_relevancy, 4),
            "context_precision": round(self.context_precision, 4),
            "context_recall": round(self.context_recall, 4),
        }

    def summary(self) -> str:
        d = self.to_dict()
        lines = ["=== RAGAS Evaluation Results ==="]
        for k, v in d.items():
            bar = "█" * int(v * 20)
            lines.append(f"  {k:<22} {v:.4f}  |{bar}")
        return "\n".join(lines)


def run_evaluation(
    retriever,
    agent_executor,
    test_cases: list[dict],
) -> EvalResult:
    """
    Run RAGAS evaluation on a list of test cases.

    Args:
        retriever:       The hybrid retriever (BM25 + FAISS + FlashRank)
        agent_executor:  The LCEL AgentExecutor
        test_cases:      List of {"question": str, "ground_truth": str}

    Returns:
        EvalResult with per-metric scores
    """
    from backend.app.core.agent import run_agent, make_history

    samples = []
    for case in test_cases:
        question = case["question"]
        ground_truth = case["ground_truth"]

        # Retrieve contexts
        docs = retriever.invoke(question)
        contexts = [d.page_content for d in docs]

        # Generate answer via agent (fresh history per question for eval)
        answer = run_agent(agent_executor, question, make_history())

        samples.append({
            "user_input": question,
            "retrieved_contexts": contexts,
            "response": answer,
            "reference": ground_truth,
        })

    dataset = EvaluationDataset.from_list(samples)

    # Use GPT-4o-mini as the evaluator LLM
    evaluator_llm = LangchainLLMWrapper(
        ChatOpenAI(model="gpt-4o-mini", temperature=0)
    )

    metrics = [
        Faithfulness(llm=evaluator_llm),
        AnswerRelevancy(llm=evaluator_llm),
        ContextPrecision(llm=evaluator_llm),
        ContextRecall(llm=evaluator_llm),
    ]

    results = evaluate(dataset=dataset, metrics=metrics)
    df = results.to_pandas()

    return EvalResult(
        faithfulness=df["faithfulness"].mean(),
        answer_relevancy=df["answer_relevancy"].mean(),
        context_precision=df["context_precision"].mean(),
        context_recall=df["context_recall"].mean(),
    )
