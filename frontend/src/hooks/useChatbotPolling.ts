import { useEffect, useRef } from "react";
import { useAuth } from "./useAuth";
import { fetchWithAuth } from "@/services/api";
import { Status } from "@/contexts/AppContext";

type PollingResponse = {
  status: string;
  answer?: string;
  sources?: string[];
};

export function useChatbotPolling(taskId: string | null, setChatbotStatus: (status: Status) => void, onComplete: (data: any) => void) {
  const { token } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!taskId) return;

    setChatbotStatus("pending");

    const poll = async () => {
      try {
        const response: PollingResponse = await fetchWithAuth(`/chatbot/answer/${taskId}`, token);
        if (response.status === "done") {
          setChatbotStatus("done");
          onComplete(response);
          if (intervalRef.current) clearInterval(intervalRef.current);
        } else if (response.status === "pending") {
          // still processing, do nothing
        } else {
          setChatbotStatus("error");
          clearInterval(intervalRef.current!);
        }
      } catch (err) {
        console.error("Polling error", err);
        setChatbotStatus("error");
        clearInterval(intervalRef.current!);
      }
    };

    intervalRef.current = setInterval(poll, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [taskId]);
}
