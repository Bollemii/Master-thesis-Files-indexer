import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FileText, Plus } from "lucide-react";
import { getDocuments, uploadDocument, Documents } from "../lib/api";
import { BottomBar } from "../components/BottomBar";

export function Home() {
  const [documents, setDocuments] = useState<Documents[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const query = searchParams.get("q") || "";
  const fileInputRef = useRef<HTMLInputElement>(null);
  const limit = 50;

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getDocuments(query, page, limit);
        setDocuments(data.items || []);
        setTotal(data.total || 0);
      } catch (err) {
        setError(`Failed to load documents: ${err instanceof Error ? err.message : String(err)}`);
        setDocuments([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [query, page]);

  const totalPages = Math.ceil(total / limit);
  const currentPage = page + 1;

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      await uploadDocument(file);
      const data = await getDocuments(query, page, limit);
      setDocuments(data.items);
    } catch (err) {
      setError(`Failed to upload document: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  if (loading) {
    return (
      <div className="text-center text-gray-900 dark:text-gray-100">
        Loading...
      </div>
    )
  };

  if (error) {
    return (
      <div className="text-center">
        <p className="text-red-500 dark:text-red-400">Error: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white rounded hover:bg-blue-600 
                   dark:hover:bg-blue-700 transition-colors duration-200"
        >
          Retry
        </button>
      </div>
    )
  };

  return (
    <div className="pb-6">
      {query && (
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
          Search results for "{query}"
        </h2>
      )}

      {documents.length === 0 ? (
        <div className="text-center text-gray-900 dark:text-gray-100">
          {query ? `No documents found for "${query}"` : "No documents found"}
        </div>
      ) : (
        <div>
          <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">
            Documents ({documents.length})
          </h1>
          <div className="grid gap-4">
            {documents.map((doc) => (
              <Link
                key={doc.id}
                to={`/documents/${doc.id}`}
                className="flex items-center p-4 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-700
                        ring-2 ring-transparent hover:outline-none hover:ring-blue-500 dark:hover:ring-blue-400 transition-shadow duration-200"
              >
                <FileText className="h-6 w-6 text-gray-400 dark:text-gray-500 mr-3" />
                <div>
                  <h2 className="font-medium text-gray-900 dark:text-gray-100">
                    {doc.filename}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(doc.upload_date).toLocaleDateString()}
                    {doc.processed && " • Processed"}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf"
      />

      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        className="fixed bottom-20 right-8 p-4 bg-blue-500 dark:bg-blue-600 
                 text-white rounded-full shadow-lg hover:bg-blue-600 
                 dark:hover:bg-blue-700 transition-colors duration-200
                 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Upload document"
      >
        {uploading ? (
          <div
            className="w-6 h-6 border-2 border-white border-t-transparent 
                        rounded-full animate-spin"
          />
        ) : (
          <Plus className="w-6 h-6" />
        )}
      </button>
      <BottomBar
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        limit={limit}
        page={page}
        total={total}
      />
    </div>
  );
}
