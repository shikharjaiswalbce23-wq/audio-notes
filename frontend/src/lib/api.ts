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

export const getUploads = async (limit: number = 10): Promise<UploadResponse[]> => {
  const response = await fetch(`${API_BASE_URL}/uploads?limit=${limit}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch uploads list");
  }

  return response.json();
};

export const deleteUpload = async (id: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/uploads/${id}`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to delete upload");
  }
};

export const updateUpload = async (id: string, filename: string): Promise<UploadResponse> => {
  const response = await fetch(`${API_BASE_URL}/uploads/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to update upload");
  }

  return response.json();
};
