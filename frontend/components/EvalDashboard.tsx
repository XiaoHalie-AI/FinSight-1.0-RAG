"use client";
import { useEffect, useState } from "react";
import { fetchEval } from "@/lib/api";

const METRICS = [
  { key: "faithfulness",      label: "Faithfulness",       desc: "Answers stay true to retrieved context" },
  { key: "answer_relevancy",  label: "Answer Relevancy",   desc: "Answers directly address the question" },
  { key: "context_precision", label: "Context Precision",  desc: "Retrieved chunks are relevant" },
  { key: "context_recall",    label: "Context Recall",     desc: "All necessary info is retrieved" },
];

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-semibold w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function EvalDashboard() {
  const [scores, setScores] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchEval()
      .then(setScores)
      .catch(() => setError(true));
  }, []);

  if (error) return null;
  if (!scores) return <p className="text-sm text-gray-400 animate-pulse">Loading eval…</p>;

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
        RAGAS Evaluation
      </h2>
      {METRICS.map(({ key, label, desc }) => (
        <div key={key}>
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">{label}</span>
          </div>
          <ScoreBar value={scores[key] ?? 0} />
          <p className="text-xs text-gray-400 mt-1">{desc}</p>
        </div>
      ))}
    </div>
  );
}
