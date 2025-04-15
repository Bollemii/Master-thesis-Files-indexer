import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Document } from "../types/api";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Trash2, RefreshCcw } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { fetchWithAuth } from "../services/api";
import { DocumentPreview } from "./DocumentPreview";
import { UpdateDocumentModal } from "./UpdateDocumentModal";

// Custom colors for the pie chart
const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

export function CorpusDetail() {
  const [document, setDocument] = useState<Document>();
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const { id } = useParams();
  const { token } = useAuth();

  const fetchDocument = useCallback(
    async (documentId: string) => {
      try {
        const document = await fetchWithAuth(`/documents/${documentId}`, token);
        setDocument(document);
      } catch (err) {
        console.error("Failed to fetch document:", err);
      }
    },
    [token]
  );

  useEffect(() => {
    if (id) fetchDocument(id);
  }, [fetchDocument, id]);

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  const topicData = document.topics?.map((topic) => {
    const value = topic.weight;
    const minAngle = value > 0 && value < 0.02 ? 2 : 0;
    return {
      name: topic.name,
      value,
      minAngle,
    };
  });

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${document?.filename}"? This action cannot be undone.`)) {
      fetchWithAuth(`/documents/${document.id}`, token, {
        method: "DELETE",
      }).then(() => {
        window.location.href = "/dashboard";
      }).catch(err => {
        console.error("Failed to delete document:", err);
        alert("Failed to delete the document. Please try again.");
      });
    };
  };

  const handleUpdate = () => {
    setIsUpdateModalOpen(true);
  };

  const handleDocumentUpdated = (updatedDocument: Document) => {
    setDocument(updatedDocument);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 min-h-[100px]">
        <div className="flex justify-between items-center mt-2">
          <h2 className="text-2xl font-bold mb-4 dark:text-white">
            {document.filename}
          </h2>
          <button
            className="flex items-center cursor-pointer text-white bg-blue-600 hover:bg-blue-700 rounded-md px-3 py-1 text-sm transition-colors"
            onClick={handleUpdate}
          >
            <RefreshCcw className="h-5 w-5 pr-1" />
            Update
          </button>
        </div>
        <div className="flex justify-between items-center mt-2">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Uploaded on {new Date(document.upload_date).toLocaleDateString()}
          </div>
          <button
            className="flex items-center cursor-pointer px-3 py-1 text-white bg-red-600 hover:bg-red-700 rounded-md text-sm transition-colors"
            onClick={handleDelete}
          >
            <Trash2 className="h-5 w-5 pr-1" />
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium mb-4 dark:text-white">
            Document Preview
          </h3>
          <div className="w-full flex justify-center">
            <DocumentPreview
              previewUrl={document.detail_preview_url || document.preview_url}
              filename={document.filename}
              size="detail"
              className="aspect-auto max-h-full"
            />
          </div>
        </div>

        {topicData && topicData.length > 0 ? (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4 dark:text-white">
              Topic Distribution
            </h3>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={topicData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={140}
                    paddingAngle={2}
                    dataKey="value"
                    minAngle={2}
                  >
                    {topicData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [
                      `${(Number(value) * 100).toFixed(1)}%`,
                      "Weight",
                    ]}
                    contentStyle={{
                      backgroundColor: "var(--tooltip-bg, #fff)",
                      color: "var(--tooltip-text, #000)",
                      borderColor: "var(--tooltip-border, #ccc)",
                    }}
                  />
                  <Legend
                    layout="vertical"
                    align="right"
                    verticalAlign="middle"
                    formatter={(value) => (
                      <span className="dark:text-white">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center justify-center">
            <div className="text-gray-500 dark:text-gray-400 text-center">
              <p className="mb-2">No topic data available for this document.</p>
              <p className="text-sm">
                This may be because the document hasn't been processed yet or
                there were no identifiable topics.
              </p>
            </div>
          </div>
        )}
      </div>
      {token && (
        <UpdateDocumentModal
          document={document}
          isOpen={isUpdateModalOpen}
          token={token}
          onClose={() => setIsUpdateModalOpen(false)}
          onDocumentUpdated={handleDocumentUpdated}
        />
      )}
    </div>
  );
}
