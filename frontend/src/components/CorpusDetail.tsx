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
import { useAuth } from "../hooks/useAuth";
import { fetchWithAuth } from "../services/api";
import { DocumentPreview } from "./DocumentPreview";

// Custom colors for the pie chart
const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

export function CorpusDetail() {
  const [document, setDocument] = useState<Document>();
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

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6 min-h-[100px]">
        <h2 className="text-2xl font-bold mb-4">{document.filename}</h2>
        <div className="text-sm text-gray-500">
          Uploaded on {new Date(document.upload_date).toLocaleDateString()}
        </div>
      </div>

      {topicData && topicData.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium mb-4">Topic Distribution</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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
                  />
                  <Legend
                    layout="vertical"
                    align="right"
                    verticalAlign="middle"
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="aspect-square">
              <DocumentPreview
                previewUrl={document.preview_url}
                filename={document.filename}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
