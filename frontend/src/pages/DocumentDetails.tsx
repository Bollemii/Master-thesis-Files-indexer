import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDocument, Document } from "../lib/api";

export function DocumentDetails() {
  const { documentId } = useParams<{ documentId: string }>();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocument = async () => {
      if (!documentId) return;

      try {
        const data = await getDocument(documentId);
        setDocument(data);
        setLoading(false);
      } catch (err) {
        setError("Failed to load document");
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  if (error || !document) {
    return (
      <div className="text-center text-red-500">
        {error || "Document not found"}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">{document.filename}</h1>

        <div className="mb-6">
          <p className="text-gray-600">
            Uploaded on {new Date(document.upload_date).toLocaleString()}
          </p>
          <p className="text-gray-600">
            Status: {document.processed ? "Processed" : "Pending"}
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4">Topics</h2>
          <div className="space-y-4">
            {document.topics.map((topic) => (
              <div key={topic.id} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-medium">{topic.name}</h3>
                  <span className="text-sm text-gray-500">
                    Weight: {(topic.weight * 100).toFixed(1)}%
                  </span>
                </div>
                {topic.description && (
                  <p className="text-gray-600 text-sm mb-2">
                    {topic.description}
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  {Object.entries(topic.words).map(([word, count]) => (
                    <span
                      key={word}
                      className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded"
                    >
                      {word} ({count})
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
