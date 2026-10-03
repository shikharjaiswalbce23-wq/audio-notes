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

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    // Load theme from localStorage on mount
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute("data-theme", savedTheme);
    }
  }, []);

  useEffect(() => {
    if (uploadInfo) {
      setRefreshTrigger(prev => prev + 1);
    }
  }, [uploadInfo?.status, uploadInfo?.id]);

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
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <button 
          className="new-chat-btn" 
          onClick={() => setUploadInfo(null)}
        >
          <span style={{ fontSize: '1.2rem' }}>+</span> New Upload
        </button>
        
        <PastUploads onSelect={setUploadInfo} refreshTrigger={refreshTrigger} />
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="top-bar">
          <button 
            className="theme-toggle"
            onClick={toggleTheme}
            title="Toggle Theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>

        <div className="content-wrapper">
          <div className="card">
            <h1 className="title">Audio Notes</h1>
            <p className="subtitle">Upload your audio to get AI-powered transcripts & summaries</p>

            {(!uploadInfo || ["FAILED"].includes(uploadInfo.status)) && (
              <UploadForm onUpload={handleUpload} isUploading={isUploading} />
            )}

            {uploadInfo && !["FAILED"].includes(uploadInfo.status) && (
              <StatusPanel uploadInfo={uploadInfo} />
            )}
            
            {uploadInfo && !["FAILED"].includes(uploadInfo.status) && (
              <ResultsPanel uploadInfo={uploadInfo} />
            )}

            {uploadInfo && ["COMPLETED"].includes(uploadInfo.status) && (
              <button 
                className="btn mt-8" 
                onClick={() => setUploadInfo(null)}
              >
                Upload Another File
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

