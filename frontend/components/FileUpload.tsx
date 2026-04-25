"use client";
import { useRef, useState } from "react";
import { uploadPDFs } from "@/lib/api";

interface Props {
  onSessionReady: (id: string, names: string[]) => void;
}

export default function FileUpload({ onSessionReady }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [fileNames, setFileNames] = useState<string[]>([]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const arr = Array.from(files);
    setFileNames(arr.map((f) => f.name));
    setStatus("uploading");
    try {
      const sessionId = await uploadPDFs(arr);
      onSessionReady(sessionId, arr.map((f) => f.name));
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => { e.preventDefault(); handleFiles(e.dataTransfer.files); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {status === "idle" && (
        <>
          <p className="text-2xl mb-2">📄</p>
          <p className="font-medium text-gray-700">Drop PDFs here or click to upload</p>
          <p className="text-sm text-gray-400 mt-1">Supports multiple files</p>
        </>
      )}

      {status === "uploading" && (
        <p className="text-blue-500 font-medium animate-pulse">Processing PDFs…</p>
      )}

      {status === "done" && (
        <>
          <p className="text-green-600 font-medium">✅ Ready to chat</p>
          <p className="text-sm text-gray-500 mt-1">{fileNames.join(", ")}</p>
        </>
      )}

      {status === "error" && (
        <p className="text-red-500 font-medium">Upload failed. Try again.</p>
      )}
    </div>
  );
}
