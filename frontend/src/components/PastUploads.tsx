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
    <div className="mt-8 text-left border-t border-white/10 pt-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-200">Recent Uploads</h3>
      <div className="flex flex-col gap-2">
        {uploads.map((upload) => (
          <div key={upload.id} className="relative group">
            <button
              onClick={() => onSelect(upload)}
              className="text-left p-3 rounded-lg bg-white/5 hover:bg-black/20 transition-colors border border-white/5 flex justify-between items-center w-full"
            >
              <div style={{ flex: 1, minWidth: 0, paddingRight: '2.5rem' }}>
                <p className="font-medium text-gray-200 truncate" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{upload.filename}</p>
                <p className="text-sm text-gray-400">
                  {new Date(upload.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <span className={`text-xs px-2 py-1 rounded-full ${upload.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {upload.status}
                </span>
              </div>
            </button>
            <button
              onClick={(e) => handleDelete(e, upload.id)}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-md hover:bg-red-500/20 text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete upload"
              style={{ transform: 'translateY(-50%)' }}
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
