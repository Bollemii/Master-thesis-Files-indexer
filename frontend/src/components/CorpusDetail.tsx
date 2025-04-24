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
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Trash2, RefreshCcw } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { fetchWithAuth } from "../services/api";
import { DocumentPreview } from "./DocumentPreview";
import { UpdateDocumentModal } from "./UpdateDocumentModal";

// Custom colors for the pie chart
const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];
const BAR_COLOR = "#8884d8";

interface WordData {
  name: string;
  weight: number;
}

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
    const displayName = topic.description?.trim()
      ? topic.description
      : topic.name;
    return {
      name: displayName,
      value,
      minAngle,
      originalTopic: topic,
    };
  });

  const MAJOR_TOPIC_THRESHOLD = 0.1; // Example threshold: 10% weight
  const TOP_N_WORDS = 10; // Show top N words per topic

  const majorTopicsWithWordData = topicData
    ?.filter(
      (topic) =>
        topic.value >= MAJOR_TOPIC_THRESHOLD && topic.originalTopic.words
    ) // Filter major topics that have word data
    .map((topic) => {
      // Convert words dictionary to sorted array [{ name: string, weight: number }]
      const wordsArray: WordData[] = Object.entries(topic.originalTopic.words)
        .map(([name, weight]) => ({ name, weight: Number(weight) })) // Ensure weight is number
        .sort((a, b) => b.weight - a.weight) // Sort descending by weight
        .slice(0, TOP_N_WORDS); // Take top N words

      return {
        topicName: topic.name, // Use the display name (description or name)
        words: wordsArray,
      };
    })
    .filter((topic) => topic.words.length > 0);

  const handleDelete = () => {
    if (
      window.confirm(
        `Are you sure you want to delete "${document?.filename}"? This action cannot be undone.`
      )
    ) {
      fetchWithAuth(`/documents/${document.id}`, token, {
        method: "DELETE",
      })
        .then(() => {
          window.location.href = "/dashboard";
        })
        .catch((err) => {
          console.error("Failed to delete document:", err);
          alert("Failed to delete the document. Please try again.");
        });
    }
  };

  const handleUpdate = () => {
    setIsUpdateModalOpen(true);
  };

  const handleDocumentUpdated = (updatedDocument: Document) => {
    setDocument(updatedDocument);
  };

  return (
    <div className="space-y-6 pb-10">
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
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 min-w-0">
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
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 min-w-0">
            <h3 className="text-lg font-medium mb-4 dark:text-white">
              Topic Distribution
            </h3>
            <div className="h-[350px] sm:h-[400px] w-full">
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
                    labelFormatter={(Label) => (
                      <span className="dark:text-white">{Label}</span>
                    )}
                    contentStyle={{
                      backgroundColor: "var(--tooltip-bg, #fff)",
                      color: "var(--tooltip-text, #000)",
                      borderColor: "var(--tooltip-border, #ccc)",
                    }}
                  />
                  <Legend
                    layout="horizontal"
                    align="center"
                    verticalAlign="bottom"
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
      {majorTopicsWithWordData && majorTopicsWithWordData.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold dark:text-white mt-8  pt-6">
            Major Topic Word Distributions (Top {TOP_N_WORDS})
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {majorTopicsWithWordData.map((topicData, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 min-w-0"
              >
                <h3
                  className="text-lg font-medium mb-4 dark:text-white truncate"
                  title={topicData.topicName}
                >
                  {topicData.topicName}
                </h3>
                <div className="h-[300px] w-full">
                  {" "}
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={topicData.words}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />{" "}
                      <XAxis type="number" hide />{" "}
                      <YAxis
                        dataKey="name"
                        type="category"
                        width={80}
                        tick={{
                          fontSize: 12,
                          fill: "var(--text-color, #6b7280)",
                        }}
                        className="dark:text-gray-400"
                      />
                      <Tooltip
                        formatter={(value: number) => [
                          value.toFixed(4),
                          "Weight",
                        ]}
                        labelFormatter={(label: string) => (
                          <span className="dark:text-white">{label}</span>
                        )}
                        contentStyle={{
                          backgroundColor: "var(--tooltip-bg, #fff)",
                          color: "var(--tooltip-text, #000)",
                          borderColor: "var(--tooltip-border, #ccc)",
                        }}
                        cursor={{ fill: "rgba(200, 200, 200, 0.1)" }}
                      />
                      <Bar dataKey="weight" fill={BAR_COLOR} barSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
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
