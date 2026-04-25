"use client";
import { useState } from "react";
import FileUpload from "@/components/FileUpload";
import ChatWindow from "@/components/ChatWindow";
import EvalDashboard from "@/components/EvalDashboard";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <span className="text-xl font-bold text-blue-600">FinSight</span>
        <span className="text-sm text-gray-400">AI-Powered Financial Research Platform</span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar */}
        <aside className="w-80 bg-white border-r p-6 flex flex-col gap-8 overflow-y-auto">
          <FileUpload onSessionReady={(id) => setSessionId(id)} />
          <EvalDashboard />
        </aside>

        {/* Chat area */}
        <main className="flex-1 flex flex-col">
          {sessionId ? (
            <ChatWindow sessionId={sessionId} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <p className="text-4xl mb-4">📊</p>
                <p className="font-medium">Upload a financial report to get started</p>
                <p className="text-sm mt-1">Supports earnings reports, 10-K, 10-Q</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
