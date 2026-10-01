"use client";

import { useState, useEffect } from "react";
import "./globals.css";
import UploadForm from "../components/UploadForm";
import StatusPanel from "../components/StatusPanel";
import ResultsPanel from "../components/ResultsPanel";
import { uploadAudio, getUploadStatus, UploadResponse } from "../lib/api";

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<UploadResponse | null>(null);

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
      <div className="card">
        <h1 className="title">Audio Notes</h1>
        <p className="subtitle">Upload your audio to get AI-powered transcripts & summaries</p>

        {(!uploadInfo || ["FAILED"].includes(uploadInfo.status)) && (
          <UploadForm onUpload={handleUpload} isUploading={isUploading} />
        )}

        <StatusPanel uploadInfo={uploadInfo} />
        <ResultsPanel uploadInfo={uploadInfo} />
        
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

