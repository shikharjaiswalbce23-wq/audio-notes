import { UploadResponse } from "../lib/api";

interface StatusPanelProps {
  uploadInfo: UploadResponse | null;
}

export default function StatusPanel({ uploadInfo }: StatusPanelProps) {
  if (!uploadInfo) return null;

  const { status, progress, error_message } = uploadInfo;

  let statusText = "Processing...";
  let progressColor = "var(--primary)";

  switch (status) {
    case "UPLOADING":
      statusText = "Uploading to secure storage...";
      break;
    case "QUEUED":
      statusText = "Queued for processing...";
      break;
    case "TRANSCRIBING":
      statusText = "Transcribing audio (this may take a minute)...";
      progressColor = "#f59e0b"; // amber
      break;
    case "SUMMARIZING":
      statusText = "Generating AI summary...";
      progressColor = "#8b5cf6"; // purple
      break;
    case "COMPLETED":
      statusText = "Completed!";
      progressColor = "#10b981"; // emerald
      break;
    case "FAILED":
      statusText = "Processing Failed";
      progressColor = "#ef4444"; // red
      break;
  }

  return (
    <div className="status-panel mt-8">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold text-lg">{statusText}</h3>
        <span className="text-sm text-gray-400 font-mono">{progress}%</span>
      </div>
      
      <div className="progress-bar-container">
        <div 
          className="progress-bar-fill" 
          style={{ 
            width: `${progress}%`,
            backgroundColor: progressColor,
            transition: 'width 0.5s ease-in-out, background-color 0.5s ease'
          }}
        />
      </div>

      {status === "FAILED" && error_message && (
        <div className="status-message status-error mt-4">
          {error_message}
        </div>
      )}
    </div>
  );
}
