import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { TopicResponse } from "../types/api";
import { useAuth } from "../hooks/useAuth";
import { fetchWithAuth } from "../services/api";

export function TopicDetail() {
  const [topic, setTopic] = useState<TopicResponse>();
  const { id } = useParams();
  const { token } = useAuth();

  const fetchTopic = useCallback(
    async (topicId: string) => {
      // Note: This endpoint is not in the OpenAPI spec, but would be needed
      try {
        const topic = await fetchWithAuth(`/topics/${topicId}`, token);
        setTopic(topic);
      } catch (err) {
        console.error("Failed to fetch topic:", err);
      }
    },
    [token]
  );

  useEffect(() => {
    if (id) fetchTopic(id);
  }, [fetchTopic, id]);

  if (!topic) return <div>Loading...</div>;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">{topic.name}</h2>
      {topic.description && (
        <p className="text-gray-600 mb-4">{topic.description}</p>
      )}

      <div className="mt-6">
        <h3 className="text-lg font-medium mb-4">Word Distribution</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(topic.words).map(([word, weight]) => (
            <div key={word} className="flex justify-between items-center">
              <span className="text-gray-700">{word}</span>
              <span className="text-gray-500">{weight.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
