import { useEffect, useState } from "react";
import { getUploads, deleteUpload, UploadResponse } from "../lib/api";

export default function PastUploads({ onSelect }: { onSelect: (upload: UploadResponse) => void }) {
  const [uploads, setUploads] = useState<UploadResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchUploads = async () => {
    try {
      const data = await getUploads(5);
      setUploads(data.filter(u => u.status === 'COMPLETED' || u.status === 'FAILED'));
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteUpload(id);
      setUploads(uploads.filter(u => u.id !== id));
    } catch (error) {
      console.error("Failed to delete upload:", error);
    }
  };

  useEffect(() => {
    fetchUploads();
  }, []);

  if (loading) return null;
  if (uploads.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 overflow-y-auto" style={{ flex: 1 }}>
      <div className="sidebar-title">Recent Uploads</div>
      {uploads.map((upload) => (
        <div key={upload.id} className="relative group" style={{ display: 'flex', width: '100%' }}>
          <button
            onClick={() => onSelect(upload)}
            className="sidebar-item"
            style={{ paddingRight: '2rem' }}
          >
            <div className="truncate w-full">
              💬 {upload.filename.replace(/\.[^/.]+$/, "")}
            </div>
          </button>
          <button
            onClick={(e) => handleDelete(e, upload.id)}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
            title="Delete upload"
            style={{ background: 'var(--bg-sidebar)', padding: '0.2rem' }}
          >
            🗑️
          </button>
        </div>
      ))}
    </div>
  );
}
