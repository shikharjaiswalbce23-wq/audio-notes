import { useState, useRef } from "react";

interface UploadFormProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export default function UploadForm({ onUpload, isUploading }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile: File) => {
    if (!selectedFile.type.startsWith("audio/")) {
      setError("Please select an audio file.");
      return;
    }
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError("File is too large. Maximum size is 100MB.");
      return;
    }
    setFile(selectedFile);
    setError(null);
  };

  const handleSubmit = () => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div>
      <div
        className={`upload-area ${dragActive ? "active" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="upload-icon">🎙️</div>
        <div className="upload-text">
          {file ? file.name : "Click or drag audio file here"}
        </div>
        <div className="upload-hint">MP3, WAV, M4A up to 100MB</div>
        <input
          ref={fileInputRef}
          type="file"
          className="file-input"
          accept="audio/*"
          onChange={handleChange}
        />
      </div>

      <button
        className="btn mt-4"
        onClick={handleSubmit}
        disabled={!file || isUploading}
      >
        {isUploading ? "Uploading..." : "Generate Notes"}
      </button>

      {error && (
        <div className="status-message status-error">
          {error}
        </div>
      )}
    </div>
  );
}
