import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FileText } from "lucide-react";
import { getDocuments, Document } from "../lib/api";

export function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await getDocuments(query);
        setDocuments(data);
        setLoading(false);
      } catch (err) {
        setError("Failed to load documents");
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [query]);

  if (loading) {
    return (
      <div className="text-center text-gray-900 dark:text-gray-100">
        Loading...
      </div>
    );
  }

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
    );
  }

  // if (documents.length === 0) {
  //   return (
  //     <div className="text-center text-gray-900 dark:text-gray-100">
  //       No documents found
  //     </div>
  //   );
  // }

  return (
    <div>
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
    </div>
  );
}
