export interface UploadResponse {
  id: string;
  filename: string;
  status: string;
  progress: number;
  transcript?: string;
  summary?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const uploadAudio = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/uploads`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Upload failed");
  }

  return response.json();
};

export const getUploadStatus = async (id: string): Promise<UploadResponse> => {
  const response = await fetch(`${API_BASE_URL}/uploads/${id}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch status");
  }

  return response.json();
};
