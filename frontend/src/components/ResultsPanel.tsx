import { UploadResponse } from "../lib/api";

interface ResultsPanelProps {
  uploadInfo: UploadResponse | null;
}

export default function ResultsPanel({ uploadInfo }: ResultsPanelProps) {
  if (!uploadInfo || uploadInfo.status !== "COMPLETED") {
    return null;
  }

  return (
    <div className="results-panel mt-8 text-left">
      {uploadInfo.summary && (
        <div className="result-section">
          <h2 className="section-title text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            AI Summary
          </h2>
          <div className="content-box bg-white/5 border border-white/10 rounded-xl p-6 whitespace-pre-wrap leading-relaxed shadow-lg">
            {uploadInfo.summary}
          </div>
        </div>
      )}

      {uploadInfo.transcript && (
        <div className="result-section mt-8">
          <h2 className="section-title text-2xl font-bold mb-4 text-gray-200">
            Full Transcript
          </h2>
          <div className="content-box bg-black/20 border border-white/5 rounded-xl p-6 whitespace-pre-wrap leading-relaxed h-64 overflow-y-auto font-mono text-sm">
            {uploadInfo.transcript}
          </div>
        </div>
      )}
    </div>
  );
}
