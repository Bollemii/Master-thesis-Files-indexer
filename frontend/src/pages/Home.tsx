import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText } from "lucide-react";
import { getDocuments, Document } from "../lib/api";

export function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await getDocuments();
        setDocuments(data);
        setLoading(false);
      } catch (err) {
        setError("Failed to load documents");
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Documents</h1>
      <div className="grid gap-4">
        {documents.map((doc) => (
          <Link
            key={doc.id}
            to={`/documents/${doc.id}`}
            className="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <FileText className="h-6 w-6 text-gray-400 mr-3" />
            <div>
              <h2 className="font-medium">{doc.filename}</h2>
              <p className="text-sm text-gray-500">
                {new Date(doc.upload_date).toLocaleDateString()}
                {doc.processed && " • Processed"}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
