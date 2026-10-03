import { useEffect, useState } from "react";
import { getUploads, UploadResponse } from "../lib/api";

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
          <button
            key={upload.id}
            onClick={() => onSelect(upload)}
            className="text-left p-3 rounded-lg bg-white/5 hover:bg-black/20 transition-colors border border-white/5 flex justify-between items-center"
          >
            <div style={{ flex: 1, minWidth: 0 }}>
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
        ))}
      </div>
    </div>
  );
}
