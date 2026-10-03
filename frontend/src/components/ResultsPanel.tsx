import { UploadResponse } from "../lib/api";

interface ResultsPanelProps {
  uploadInfo: UploadResponse | null;
}

export default function ResultsPanel({ uploadInfo }: ResultsPanelProps) {
  if (!uploadInfo || uploadInfo.status !== "COMPLETED") {
    return null;
  }

  return (
    <div className="results-panel mt-8 text-left w-full">
      {uploadInfo.summary && (
        <div className="result-section mb-8">
          <div className="flex items-center gap-2 mb-4">
            <span style={{ fontSize: '1.5rem' }}>✨</span>
            <h2 className="section-title text-xl font-bold text-gray-200" style={{ margin: 0 }}>
              Summary
            </h2>
          </div>
          <div className="content-box p-4 whitespace-pre-wrap leading-relaxed rounded-md" style={{ background: 'var(--bg-main)', border: '1px solid var(--border-color)' }}>
            {uploadInfo.summary}
          </div>
        </div>
      )}

      {uploadInfo.transcript && (
        <div className="result-section mt-8">
          <div className="flex items-center gap-2 mb-4">
            <span style={{ fontSize: '1.5rem' }}>📝</span>
            <h2 className="section-title text-xl font-bold text-gray-200" style={{ margin: 0 }}>
              Transcript
            </h2>
          </div>
          <div className="content-box p-4 whitespace-pre-wrap leading-relaxed font-mono text-sm rounded-md overflow-y-auto" style={{ background: 'var(--hover-bg)', border: '1px solid var(--border-color)', maxHeight: '300px' }}>
            {uploadInfo.transcript}
          </div>
        </div>
      )}
    </div>
  );
}
