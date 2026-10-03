"use client";

import { useState, useEffect } from "react";
import "./globals.css";
import UploadForm from "../components/UploadForm";
import StatusPanel from "../components/StatusPanel";
import ResultsPanel from "../components/ResultsPanel";
import PastUploads from "../components/PastUploads";
import { uploadAudio, getUploadStatus, UploadResponse } from "../lib/api";

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<UploadResponse | null>(null);
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    // Load theme from localStorage on mount
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute("data-theme", savedTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);
  };

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (
      uploadInfo &&
      !["COMPLETED", "FAILED"].includes(uploadInfo.status)
    ) {
      intervalId = setInterval(async () => {
        try {
          const updatedInfo = await getUploadStatus(uploadInfo.id);
          setUploadInfo(updatedInfo);
        } catch (error) {
          console.error("Failed to poll status:", error);
        }
      }, 3000); // Poll every 3 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [uploadInfo]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadInfo(null);

    try {
      const data = await uploadAudio(file);
      setUploadInfo(data);
    } catch (error: any) {
      console.error(error);
      setUploadInfo({
        id: "error",
        filename: file.name,
        status: "FAILED",
        progress: 0,
        error_message: error.message || "An error occurred during upload.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: uploadInfo && uploadInfo.status === "COMPLETED" ? "800px" : "600px", transition: "max-width 0.5s ease" }}>
      <div className="card" style={{ position: 'relative' }}>
        {uploadInfo && (
          <button 
            onClick={() => setUploadInfo(null)}
            style={{ 
              position: 'absolute', top: '1.5rem', left: '1.5rem', 
              background: 'transparent', border: 'none', 
              fontSize: '1rem', cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              fontWeight: 500
            }}
            className="hover:text-primary transition-colors"
          >
            ← Back
          </button>
        )}
        <button 
          onClick={toggleTheme} 
          style={{ 
            position: 'absolute', top: '1.5rem', right: '1.5rem', 
            background: 'transparent', border: 'none', 
            fontSize: '1.5rem', cursor: 'pointer',
            color: 'var(--foreground)'
          }}
          title="Toggle Theme"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        <h1 className="title" style={{ marginTop: uploadInfo ? '1.5rem' : '0' }}>Audio Notes</h1>
        <p className="subtitle">Upload your audio to get AI-powered transcripts & summaries</p>

        {(!uploadInfo || ["FAILED"].includes(uploadInfo.status)) && (
          <>
            <UploadForm onUpload={handleUpload} isUploading={isUploading} />
            <PastUploads onSelect={setUploadInfo} />
          </>
        )}

        {uploadInfo && !["FAILED"].includes(uploadInfo.status) && (
          <StatusPanel uploadInfo={uploadInfo} />
        )}
        
        {uploadInfo && !["FAILED"].includes(uploadInfo.status) && (
          <ResultsPanel uploadInfo={uploadInfo} />
        )}
        
        {uploadInfo && ["COMPLETED", "FAILED"].includes(uploadInfo.status) && (
          <button 
            className="btn mt-8" 
            style={{ marginTop: '2rem' }}
            onClick={() => setUploadInfo(null)}
          >
            Upload Another File
          </button>
        )}
      </div>
    </div>
  );
}

