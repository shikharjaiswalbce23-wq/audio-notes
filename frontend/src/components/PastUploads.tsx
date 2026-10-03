import { useEffect, useState, useRef } from "react";
import { getUploads, deleteUpload, updateUpload, UploadResponse } from "../lib/api";

export default function PastUploads({ 
  onSelect, 
  refreshTrigger = 0 
}: { 
  onSelect: (upload: UploadResponse) => void;
  refreshTrigger?: number;
}) {

  const [uploads, setUploads] = useState<UploadResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchUploads = async () => {
    try {
      const data = await getUploads(20);
      setUploads(data);
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

  const startEdit = (e: React.MouseEvent, upload: UploadResponse) => {
    e.stopPropagation();
    setEditingId(upload.id);
    setEditValue(upload.filename.replace(/\.[^/.]+$/, ""));
  };

  const saveEdit = async (id: string) => {
    if (editingId === id && editValue.trim() !== "") {
      try {
        const upload = uploads.find(u => u.id === id);
        if (upload) {
          const extension = upload.filename.includes('.') ? '.' + upload.filename.split('.').pop() : '';
          const newFilename = `${editValue.trim()}${extension}`;
          await updateUpload(id, newFilename);
          setUploads(uploads.map(u => u.id === id ? { ...u, filename: newFilename } : u));
        }
      } catch (error) {
        console.error("Failed to rename upload:", error);
      }
    }
    setEditingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === 'Enter') {
      saveEdit(id);
    } else if (e.key === 'Escape') {
      setEditingId(null);
    }
  };

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
    }
  }, [editingId]);

  useEffect(() => {
    fetchUploads();
  }, [refreshTrigger]);

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
            style={{ paddingRight: '4rem' }}
          >
            {editingId === upload.id ? (
              <input
                ref={inputRef}
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={() => saveEdit(upload.id)}
                onKeyDown={(e) => handleKeyDown(e, upload.id)}
                onClick={(e) => e.stopPropagation()}
                className="w-full text-sm outline-none"
                style={{ background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--accent)', borderRadius: '4px', padding: '2px 4px' }}
              />
            ) : (
              <div className="truncate w-full text-sm">
                {upload.filename.replace(/\.[^/.]+$/, "")}
              </div>
            )}
          </button>
          
          {editingId !== upload.id && (
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: 'var(--hover-bg)' }}>
              <button
                onClick={(e) => startEdit(e, upload)}
                className="p-1 rounded-md text-gray-400 hover:text-gray-200"
                title="Rename upload"
              >
                ✏️
              </button>
              <button
                onClick={(e) => handleDelete(e, upload.id)}
                className="p-1 rounded-md text-gray-400 hover:text-red-400"
                title="Delete upload"
              >
                🗑️
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
